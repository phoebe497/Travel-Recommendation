"""
Smart Itinerary Planner
Main entry point for the new itinerary planning system
Integrates with existing TourGenerator
"""

import logging
from typing import List, Dict, Optional
from datetime import date

from src.models import Place, UserPreference
from src.database import MongoDBHandler
from src.graph_builder import PlaceGraph
from src.itinerary_builder import ItineraryBuilder, TourItinerary
from src.hybrid_recommender import HybridRecommender

logger = logging.getLogger(__name__)


class SmartItineraryPlanner:
    """
    Smart Itinerary Planner
    
    Features:
    - Graph-based routing with Dijkstra algorithm
    - Time block scheduling (meals/activities/rest)
    - Opening hours filtering
    - Transport mode selection (walking/motorbike/taxi)
    - Activity sequence optimization
    - BERT + SVD hybrid recommendations
    """
    
    def __init__(
        self,
        db_handler: Optional[MongoDBHandler] = None,
        use_hybrid_scoring: bool = True
    ):
        """
        Initialize Smart Itinerary Planner
        
        Args:
            db_handler: MongoDB handler (creates new if None)
            use_hybrid_scoring: Whether to use BERT+SVD hybrid scoring
        """
        self.db = db_handler or MongoDBHandler()
        self.use_hybrid_scoring = use_hybrid_scoring
        
        if use_hybrid_scoring:
            self.recommender = HybridRecommender()
            logger.info("Initialized with BERT+SVD hybrid scoring")
        else:
            self.recommender = None
            logger.info("Initialized without hybrid scoring (rating-based)")
    
    def generate_itinerary(
        self,
        user_pref: UserPreference,
        start_date: Optional[date] = None,
        max_places: int = 200
    ) -> TourItinerary:
        """
        Generate complete itinerary for a trip
        
        Args:
            user_pref: User preferences
            start_date: Tour start date (defaults to today)
            max_places: Maximum places to consider
            
        Returns:
            TourItinerary with complete schedule
        """
        logger.info(
            f"Generating itinerary for {user_pref.trip_duration_days} days "
            f"in {user_pref.destination_city}"
        )
        
        # Step 1: Load places from database
        places = self._load_places(user_pref.destination_city, max_places)
        
        if not places:
            raise ValueError(f"No places found in {user_pref.destination_city}")
        
        logger.info(f"Loaded {len(places)} places")
        
        # Step 2: Calculate hybrid scores (if enabled)
        hybrid_scores = None
        if self.use_hybrid_scoring and self.recommender:
            hybrid_scores = self._calculate_hybrid_scores(places, user_pref)
        
        # Step 3: Build itinerary
        builder = ItineraryBuilder(places)
        tour = builder.build_itinerary(
            user_pref=user_pref,
            start_date=start_date,
            hybrid_scores=hybrid_scores
        )
        
        # Step 4: Optimize itinerary (add transport connections)
        tour = builder.optimize_itinerary(tour)
        
        logger.info(
            f"Itinerary generated: {tour.get_total_places()} places, "
            f"${tour.get_total_cost():.2f} total"
        )
        
        return tour
    
    def _load_places(self, destination_city: str, max_places: int) -> List[Place]:
        """Load places from database"""
        places_collection = self.db.get_collection("places")
        
        # Query places in destination city, sorted by rating
        query = {"city": destination_city}
        cursor = places_collection.find(query).sort("rating", -1).limit(max_places)
        
        places = []
        for doc in cursor:
            try:
                # Use from_dict to handle MongoDB schema correctly
                place = Place.from_dict(doc)
                places.append(place)
            except Exception as e:
                logger.warning(f"Failed to load place {doc.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Loaded {len(places)} places from {destination_city}")
        return places
    
    def _calculate_hybrid_scores(
        self,
        places: List[Place],
        user_pref: UserPreference
    ) -> Dict[str, float]:
        """Calculate hybrid recommendation scores"""
        logger.info("Calculating hybrid scores with BERT+SVD...")
        
        try:
            # Precompute BERT embeddings
            self.recommender.content_filter.precompute_embeddings(places)
            
            # Convert selected place IDs to Place objects
            place_dict = {p.place_id: p for p in places}
            selected_place_objects = []
            if user_pref.selected_places:
                selected_place_objects = [
                    place_dict[pid] for pid in user_pref.selected_places 
                    if pid in place_dict
                ]
            
            # Get scored recommendations
            scored_places = self.recommender.get_top_recommendations(
                user_pref=user_pref,
                candidate_places=places,
                selected_places=selected_place_objects,
                k=len(places)
            )
            
            # Convert to dict
            hybrid_scores = {p.place_id: score for p, score in scored_places}
            
            logger.info(f"Calculated hybrid scores for {len(hybrid_scores)} places")
            return hybrid_scores
            
        except Exception as e:
            logger.warning(f"Hybrid scoring failed: {e}. Using ratings.")
            return {}
    
    def save_itinerary(self, tour: TourItinerary, output_path: str) -> str:
        """
        Save itinerary to JSON file
        
        Args:
            tour: TourItinerary to save
            output_path: Path to output file
            
        Returns:
            Path to saved file
        """
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tour.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Itinerary saved to {output_file}")
        return str(output_file)
    
    def get_itinerary_summary(self, tour: TourItinerary) -> dict:
        """Get summary statistics of an itinerary"""
        return {
            "destination": tour.destination,
            "duration_days": tour.duration_days,
            "total_places": tour.get_total_places(),
            "total_cost_usd": round(tour.get_total_cost(), 2),
            "daily_breakdown": [
                {
                    "day": day.day_number,
                    "date": day.date,
                    "places": len(day.get_all_scheduled_places()),
                    "cost_usd": round(day.get_total_cost(), 2),
                    "score": round(day.get_total_score(), 3)
                }
                for day in tour.daily_itineraries
            ]
        }
