"""
Hybrid Recommendation System
Combines content-based and collaborative filtering scores

Uses:
- Multilingual BERT for content-based filtering (768-dim embeddings)
- SVD Matrix Factorization for collaborative filtering (50-dim embeddings)
"""

import logging
from typing import List, Dict, Tuple, Optional

from .models import Place, UserPreference
from .content_filter_bert import ContentBasedFilterBERT
from .collaborative_filter_svd import CollaborativeFilterSVD
from .config import config

logger = logging.getLogger(__name__)


class HybridRecommender:
    """
    Hybrid recommendation system combining content-based and collaborative filtering
    
    Optimizations:
    - BERT embeddings cached for fast inference (~1ms per place after initial encoding)
    - SVD model persisted to disk for fast loading
    - Batch processing for initial embedding computation
    """
    
    def __init__(
        self, 
        cache_dir: str = "data/embeddings_cache",
        model_dir: str = "data/models"
    ):
        """
        Initialize the hybrid recommender
        
        Args:
            cache_dir: Directory for BERT embedding cache
            model_dir: Directory for collaborative filter models
        """
        logger.info("Initializing with Multilingual BERT content filter")
        self.content_filter = ContentBasedFilterBERT(cache_dir=cache_dir)
        
        logger.info("Initializing SVD collaborative filter")
        self.collaborative_filter = CollaborativeFilterSVD(
            n_factors=50,
            model_dir=model_dir
        )
        
        # Try to load existing CF model
        self.collaborative_filter.load_model()
    
    def train_collaborative_filter(self, interactions: List[Dict]) -> None:
        """
        Train the collaborative filtering component
        
        Args:
            interactions: List of user-place interactions
        """
        if interactions and len(interactions) > 0:
            self.collaborative_filter.fit(interactions)
        else:
            logger.warning("No interactions available for collaborative filtering training")
    
    def calculate_hybrid_scores(
        self,
        user_pref: UserPreference,
        candidate_places: List[Place],
        selected_places: List[Place],
        alpha: float = None,
        total_available_places: int = 30
    ) -> Dict[str, float]:
        """
        Calculate hybrid scores combining content-based and collaborative filtering
        
        Score formula: 
        hybrid_score = alpha * content_score + (1 - alpha) * collaborative_score
        
        Args:
            user_pref: User preferences
            candidate_places: List of candidate places (all places in city from DB)
            selected_places: Places user has already selected
            alpha: Weight for content-based filtering (0-1). If None, calculated from user_pref
            total_available_places: Total places available in city (for alpha calculation)
                                   Should be len(candidate_places) clipped to [30, 200]
            
        Returns:
            Dictionary mapping place_id to hybrid score
        """
        # Calculate alpha based on number of selected places if not provided
        if alpha is None:
            alpha = user_pref.calculate_alpha(total_available_places)
        
        logger.info(f"Using alpha={alpha:.2f} for hybrid scoring")
        
        # Calculate content-based scores
        content_scores = self.content_filter.calculate_content_scores(
            user_pref, candidate_places, selected_places
        )
        
        # Calculate collaborative scores
        collaborative_scores = self.collaborative_filter.calculate_collaborative_scores(
            user_pref.user_id, candidate_places
        )
        
        # Combine scores
        hybrid_scores = {}
        
        for place in candidate_places:
            place_id = place.place_id
            
            # Get individual scores (default to 0.5 if not available)
            content_score = content_scores.get(place_id, 0.5)
            collab_score = collaborative_scores.get(place_id, 0.5)
            
            # Calculate hybrid score
            hybrid_score = alpha * content_score + (1 - alpha) * collab_score
            
            # Bonus for highly rated places
            rating_bonus = (place.rating / 5.0) * 0.1
            
            # Final score
            final_score = min(1.0, hybrid_score + rating_bonus)
            
            hybrid_scores[place_id] = final_score
        
        logger.info(f"Calculated hybrid scores for {len(hybrid_scores)} places")
        return hybrid_scores
    
    def get_top_recommendations(
        self,
        user_pref: UserPreference,
        candidate_places: List[Place],
        selected_places: List[Place],
        k: int = None,
        alpha: float = None
    ) -> List[Tuple[Place, float]]:
        """
        Get top K recommended places, balanced across categories
        
        Args:
            user_pref: User preferences
            candidate_places: List of candidate places
            selected_places: Places user has selected
            k: Number of recommendations. If None, uses config.TOP_K_PLACES
            alpha: Weight for content-based filtering
            
        Returns:
            List of (Place, score) tuples sorted by score
        """
        if k is None:
            k = config.TOP_K_PLACES
        
        total_available = len(candidate_places)  # Actual DB size (có thể 5-5000)
        total_available_clipped = max(30, min(200, total_available))
        
        logger.info(f"Alpha calculation: {len(selected_places)} selected / {total_available_clipped} pool "
                   f"(DB has {total_available} places, clipped to interaction range [30, 200])")
        
        # Calculate hybrid scores với alpha dựa trên clipped pool
        scores = self.calculate_hybrid_scores(
            user_pref, candidate_places, selected_places, alpha, 
            total_available_places=total_available_clipped
        )
        
        # Create place lookup
        place_dict = {p.place_id: p for p in candidate_places}
        
        # Classify places by type using PlaceFilter
        from src.place_filter import PlaceFilter
        
        restaurants = []
        hotels = []
        activities = []
        
        for pid, score in scores.items():
            place = place_dict.get(pid)
            if not place:
                continue
                
            if PlaceFilter.is_restaurant(place):
                restaurants.append((pid, score))
            elif PlaceFilter.is_hotel(place):
                hotels.append((pid, score))
            elif PlaceFilter.is_activity(place):
                activities.append((pid, score))
        
        # Sort each category by score
        restaurants.sort(key=lambda x: x[1], reverse=True)
        hotels.sort(key=lambda x: x[1], reverse=True)
        activities.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate balanced distribution
        # For a 3-day trip: need ~6 activities, ~6 restaurants, ~3 hotels per day
        num_days = user_pref.trip_duration_days
        
        # Target: 60% activities, 30% restaurants, 10% hotels
        k_activities = min(len(activities), int(k * 0.6))
        k_restaurants = min(len(restaurants), int(k * 0.3))
        k_hotels = min(len(hotels), k - k_activities - k_restaurants)  # Remaining
        
        # Take top from each category
        top_activities = activities[:k_activities]
        top_restaurants = restaurants[:k_restaurants]
        top_hotels = hotels[:k_hotels]
        
        # Combine and sort by score
        balanced_recommendations = top_activities + top_restaurants + top_hotels
        balanced_recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Convert to (Place, score) tuples
        top_k = [(place_dict[pid], score) for pid, score in balanced_recommendations if pid in place_dict]
        
        logger.info(f"Generated top {len(top_k)} balanced recommendations:")
        logger.info(f"  - {len(top_activities)} activities ({len(top_activities)/len(top_k)*100:.0f}%)")
        logger.info(f"  - {len(top_restaurants)} restaurants ({len(top_restaurants)/len(top_k)*100:.0f}%)")
        logger.info(f"  - {len(top_hotels)} hotels ({len(top_hotels)/len(top_k)*100:.0f}%)")
        
        # Log top 5 for debugging
        for i, (place, score) in enumerate(top_k[:5], 1):
            logger.info(f"  {i}. {place.name} (score: {score:.3f}, rating: {place.rating})")
        
        return top_k
    
    def filter_by_criteria(
        self,
        places: List[Place],
        user_pref: UserPreference
    ) -> List[Place]:
        """
        Filter places based on user criteria (budget, interests, etc.)
        
        Args:
            places: List of places to filter
            user_pref: User preferences
            
        Returns:
            Filtered list of places
        """
        filtered = []
        
        # Budget filtering
        budget_map = {
            "low": [0, 1],
            "medium": [1, 2, 3],
            "high": [2, 3, 4]
        }
        
        allowed_price_levels = budget_map.get(user_pref.budget_range, [0, 1, 2, 3, 4])
        
        for place in places:
            # Price filter
            if place.price_level > 0 and place.price_level not in allowed_price_levels:
                continue
            
            # Rating filter (minimum 3.0 stars)
            if place.rating < 3.0:
                continue
            
            # Interest filter (if user has specific interests)
            if user_pref.interests:
                place_categories = set(place.types)
                
                # Check if place matches any interest
                matches_interest = False
                
                interest_type_map = {
                    "landmarks": ["tourist_attraction", "cultural_landmark", "historical_landmark"],
                    "museums": ["museum", "art_gallery"],
                    "parks": ["park", "garden", "nature_reserve"],
                    "shopping": ["shopping_mall", "store", "market"],
                    "food": ["restaurant", "cafe", "food"],
                    "nightlife": ["night_club", "bar", "casino"],
                    "entertainment": ["amusement_park", "movie_theater", "casino"]
                }
                
                for interest in user_pref.interests:
                    # Direct match: if interest matches any place type
                    if interest in place_categories:
                        matches_interest = True
                        break
                    
                    # Mapped match: check interest_type_map
                    if interest in interest_type_map:
                        relevant_types = set(interest_type_map[interest])
                        if place_categories & relevant_types:
                            matches_interest = True
                            break
                
                # For accommodation and dining, always include
                if "hotel" in place.types or "lodging" in place.types:
                    matches_interest = True
                if "restaurant" in place.types or "cafe" in place.types:
                    matches_interest = True
                
                if not matches_interest:
                    continue
            
            filtered.append(place)
        
        logger.info(f"Filtered {len(places)} places down to {len(filtered)} matching criteria")
        return filtered
