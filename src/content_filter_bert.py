"""
Content-Based Filtering Module with Multilingual BERT Embeddings
Uses sentence-transformers for semantic similarity across English and Vietnamese
Optimized with embedding cache to minimize inference time
"""

import numpy as np
from typing import List, Dict, Optional
import logging
import pickle
import os
from pathlib import Path

from .models import Place, UserPreference

logger = logging.getLogger(__name__)


class ContentBasedFilterBERT:
    """
    Content-based filtering using Multilingual BERT embeddings
    
    Features:
    - Semantic similarity (understands both English types and Vietnamese names)
    - Embedding cache (pre-compute and store embeddings)
    - Fast inference (~1ms per place after initial encoding)
    - 768-dimensional dense vectors
    """
    
    def __init__(self, cache_dir: str = "data/embeddings_cache"):
        """
        Initialize content-based filter with BERT
        
        Args:
            cache_dir: Directory to store/load embedding cache
        """
        self.model = None
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "place_embeddings.pkl"
        
        # Load model lazily (only when needed)
        self._model_loaded = False
        
        # Load cache if exists
        self._load_cache()
        
        logger.info(f"ContentBasedFilterBERT initialized with cache dir: {cache_dir}")
        logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
    
    def _load_model(self):
        """Lazy load sentence-transformers model"""
        if self._model_loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info("Loading multilingual BERT model (paraphrase-multilingual-mpnet-base-v2)...")
            self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
            self._model_loaded = True
            logger.info("Model loaded successfully (768 dimensions)")
            
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            raise
    
    def _load_cache(self):
        """Load embedding cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.embedding_cache = pickle.load(f)
                logger.info(f"Loaded {len(self.embedding_cache)} embeddings from cache")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.embedding_cache = {}
        else:
            logger.info("No cache file found, starting fresh")
    
    def _save_cache(self):
        """Save embedding cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            logger.info(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _create_place_text(self, place: Place) -> str:
        """
        Create text representation of a place for embedding
        
        Combines:
        - Types (English): "restaurant food point_of_interest"
        - Name (Vietnamese/English): "Phở Hà Nội"
        - City: "Hanoi"
        
        Args:
            place: Place object
            
        Returns:
            Text string for embedding
        """
        components = []
        
        # Types (multi-word, space-separated)
        if place.types:
            types_text = ' '.join(place.types)
            components.append(types_text)
        
        # Name
        if place.name:
            components.append(place.name)
        
        # City (helps differentiate similar places in different cities)
        if place.city:
            components.append(place.city)
        
        # Join with space
        text = ' '.join(components)
        
        return text
    
    def _create_place_embedding(self, place: Place, use_cache: bool = True) -> np.ndarray:
        """
        Create embedding for a place
        
        Uses cache if available, otherwise encodes with BERT model
        
        Args:
            place: Place object
            use_cache: Whether to use/update cache
            
        Returns:
            Embedding vector (768 dimensions)
        """
        # Check cache first
        if use_cache and place.place_id in self.embedding_cache:
            return self.embedding_cache[place.place_id]
        
        # Load model if not loaded
        self._load_model()
        
        # Create text representation
        text = self._create_place_text(place)
        
        # Encode with BERT
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        # Cache the embedding
        if use_cache:
            self.embedding_cache[place.place_id] = embedding
        
        return embedding
    
    def precompute_embeddings(self, places: List[Place], save_cache: bool = True):
        """
        Precompute embeddings for all places (batch processing)
        
        This is the optimization that makes subsequent queries fast!
        Run this once when loading places from database.
        
        Args:
            places: List of all places
            save_cache: Whether to save cache to disk after computation
        """
        # Load model
        self._load_model()
        
        # Find places not in cache
        places_to_encode = [p for p in places if p.place_id not in self.embedding_cache]
        
        if not places_to_encode:
            logger.info("All places already in cache")
            return
        
        logger.info(f"Encoding {len(places_to_encode)} new places...")
        
        # Batch encode for efficiency
        texts = [self._create_place_text(p) for p in places_to_encode]
        
        # Encode in batch (much faster than one-by-one)
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=True,
            batch_size=32  # Adjust based on available memory
        )
        
        # Update cache
        for place, embedding in zip(places_to_encode, embeddings):
            self.embedding_cache[place.place_id] = embedding
        
        logger.info(f"Encoded {len(places_to_encode)} places successfully")
        
        # Save cache
        if save_cache:
            self._save_cache()
    
    def _create_user_embedding(
        self,
        user_pref: UserPreference,
        selected_places: List[Place]
    ) -> np.ndarray:
        """
        Create user preference embedding
        
        Strategy: Average of selected place embeddings
        
        Args:
            user_pref: User preferences
            selected_places: Places user has selected
            
        Returns:
            User embedding vector (768 dimensions)
        """
        if not selected_places:
            # Cold start: return zero vector
            # Collaborative filtering will handle this case
            return np.zeros(768)
        
        # Get embeddings for selected places
        selected_embeddings = [
            self._create_place_embedding(place) 
            for place in selected_places
        ]
        
        # Average pooling
        user_embedding = np.mean(selected_embeddings, axis=0)
        
        # Normalize
        norm = np.linalg.norm(user_embedding)
        if norm > 0:
            user_embedding = user_embedding / norm
        
        return user_embedding
    
    def calculate_content_scores(
        self,
        user_pref: UserPreference,
        candidate_places: List[Place],
        selected_places: List[Place]
    ) -> Dict[str, float]:
        """
        Calculate content-based scores for candidate places
        
        Uses cosine similarity between user embedding and place embeddings
        
        Args:
            user_pref: User preferences
            candidate_places: Places to score
            selected_places: Places user has selected
            
        Returns:
            Dict mapping place_id to content score [0, 1]
        """
        # Create user embedding
        user_embedding = self._create_user_embedding(user_pref, selected_places)
        
        # If cold start (no selected places), return neutral scores
        if np.allclose(user_embedding, 0):
            logger.warning("Cold start: no selected places, returning neutral scores")
            return {place.place_id: 0.5 for place in candidate_places}
        
        # Calculate scores
        scores = {}
        
        for place in candidate_places:
            # Skip if already selected
            if place.place_id in [p.place_id for p in selected_places]:
                continue
            
            # Get place embedding (from cache if available)
            place_embedding = self._create_place_embedding(place, use_cache=True)
            
            # Cosine similarity (already normalized, so just dot product)
            # Since embeddings are normalized, dot product = cosine similarity
            similarity = np.dot(user_embedding, place_embedding)
            
            # Convert from [-1, 1] to [0, 1]
            # In practice, with normalized embeddings, similarity is usually in [0, 1]
            # But we clip to be safe
            score = np.clip((similarity + 1) / 2, 0, 1)
            
            # Add small rating boost (places with higher ratings get slight preference)
            rating_boost = (place.rating / 5.0) * 0.1  # Max 0.1 boost
            
            # Final score
            final_score = min(1.0, score + rating_boost)
            
            scores[place.place_id] = float(final_score)
        
        logger.info(f"Calculated content scores for {len(scores)} candidate places")
        
        # Log some statistics
        if scores:
            avg_score = np.mean(list(scores.values()))
            max_score = max(scores.values())
            min_score = min(scores.values())
            logger.info(f"Score stats - avg: {avg_score:.3f}, min: {min_score:.3f}, max: {max_score:.3f}")
        
        return scores
    
    def clear_cache(self):
        """Clear embedding cache (useful for testing or updates)"""
        self.embedding_cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cached_embeddings': len(self.embedding_cache),
            'cache_file_exists': self.cache_file.exists(),
            'cache_dir': str(self.cache_dir),
            'model_loaded': self._model_loaded
        }
