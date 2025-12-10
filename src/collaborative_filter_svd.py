"""
Collaborative Filtering Module with SVD (Singular Value Decomposition)
Optimized for sparse user-item interaction matrices
"""

import numpy as np
from typing import List, Dict, Optional
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
import logging
import pickle
from pathlib import Path

from .models import Place

logger = logging.getLogger(__name__)


class CollaborativeFilterSVD:
    """
    Collaborative filtering using SVD matrix factorization
    
    Features:
    - SVD decomposition: R ≈ U × Σ × V^T
    - User embeddings (U): (n_users, k) dimensions
    - Place embeddings (V): (n_places, k) dimensions  
    - Fast prediction: dot product of user and place vectors
    - Model persistence: save/load trained model
    """
    
    def __init__(self, n_factors: int = 50, model_dir: str = "data/models"):
        """
        Initialize collaborative filter with SVD
        
        Args:
            n_factors: Number of latent factors (embedding dimensions)
            model_dir: Directory to save/load trained model
        """
        self.n_factors = n_factors
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Model components
        self.user_embeddings: Optional[np.ndarray] = None  # (n_users, k)
        self.place_embeddings: Optional[np.ndarray] = None  # (n_places, k)
        self.sigma: Optional[np.ndarray] = None  # (k,) singular values
        
        # Index mappings
        self.user_to_idx: Dict[str, int] = {}
        self.idx_to_user: Dict[int, str] = {}
        self.place_to_idx: Dict[str, int] = {}
        self.idx_to_place: Dict[int, str] = {}
        
        # Training status
        self.is_trained = False
        
        # Statistics
        self.global_mean_rating = 3.0
        
        logger.info(f"CollaborativeFilterSVD initialized (k={n_factors} factors)")
    
    def _build_interaction_matrix(
        self,
        interactions: List[Dict]
    ) -> csr_matrix:
        """
        Build sparse user-item interaction matrix
        
        Args:
            interactions: [{"user_id": "u1", "place_id": "p1", "rating": 5}, ...]
            
        Returns:
            Sparse rating matrix (n_users × n_places)
        """
        # Extract unique users and places
        users = sorted(set(i['user_id'] for i in interactions))
        places = sorted(set(i['place_id'] for i in interactions))
        
        # Build index mappings
        self.user_to_idx = {u: idx for idx, u in enumerate(users)}
        self.idx_to_user = {idx: u for u, idx in self.user_to_idx.items()}
        
        self.place_to_idx = {p: idx for idx, p in enumerate(places)}
        self.idx_to_place = {idx: p for p, idx in self.place_to_idx.items()}
        
        # Build sparse matrix
        n_users = len(users)
        n_places = len(places)
        
        rows = []
        cols = []
        data = []
        ratings_sum = 0
        
        for interaction in interactions:
            user_id = interaction['user_id']
            place_id = interaction['place_id']
            rating = interaction.get('rating', 0)
            
            if rating > 0:  # Only include non-zero ratings
                u_idx = self.user_to_idx[user_id]
                p_idx = self.place_to_idx[place_id]
                
                rows.append(u_idx)
                cols.append(p_idx)
                data.append(rating)
                ratings_sum += rating
        
        # Calculate global mean
        if len(data) > 0:
            self.global_mean_rating = ratings_sum / len(data)
        
        # Create sparse matrix
        R = csr_matrix(
            (data, (rows, cols)),
            shape=(n_users, n_places),
            dtype=np.float32
        )
        
        # Calculate density
        density = len(data) / (n_users * n_places) * 100
        
        logger.info(f"Built interaction matrix: {n_users} users × {n_places} places")
        logger.info(f"Interactions: {len(data)}, Density: {density:.2f}%")
        logger.info(f"Global mean rating: {self.global_mean_rating:.2f}")
        
        return R
    
    def fit(self, interactions: List[Dict], save_model: bool = True):
        """
        Train collaborative filter using SVD
        
        Args:
            interactions: List of user-place interactions
            save_model: Whether to save trained model to disk
        """
        if not interactions or len(interactions) == 0:
            logger.warning("No interactions provided, cannot train collaborative filter")
            self.is_trained = False
            return
        
        logger.info(f"Training SVD collaborative filter with {len(interactions)} interactions...")
        
        # Build interaction matrix
        R = self._build_interaction_matrix(interactions)
        
        n_users, n_places = R.shape
        
        # Adjust k if necessary
        k = min(self.n_factors, min(n_users, n_places) - 1)
        if k < self.n_factors:
            logger.warning(f"Reducing k from {self.n_factors} to {k} due to matrix size")
        
        # Perform SVD: R ≈ U × Σ × V^T
        try:
            logger.info(f"Computing SVD (k={k})...")
            
            # svds returns (u, sigma, vt)
            # u: (n_users, k)
            # sigma: (k,) - singular values
            # vt: (k, n_places)
            U, sigma, Vt = svds(R.astype(np.float32), k=k)
            
            # SVD returns components in ascending order, we want descending
            # Reverse the order
            U = U[:, ::-1]
            sigma = sigma[::-1]
            Vt = Vt[::-1, :]
            
            # Store embeddings
            # User embedding: U × sqrt(Σ)
            # Place embedding: V × sqrt(Σ) where V = Vt.T
            sqrt_sigma = np.sqrt(sigma)
            
            self.user_embeddings = U * sqrt_sigma  # (n_users, k)
            self.place_embeddings = Vt.T * sqrt_sigma  # (n_places, k)
            self.sigma = sigma
            
            self.is_trained = True
            
            logger.info("SVD training completed successfully")
            logger.info(f"User embeddings shape: {self.user_embeddings.shape}")
            logger.info(f"Place embeddings shape: {self.place_embeddings.shape}")
            
            # Log variance explained
            variance_explained = np.sum(sigma) / np.sum(sigma) * 100
            logger.info(f"Top {k} factors explain {variance_explained:.1f}% variance")
            
            # Save model
            if save_model:
                self._save_model()
            
        except Exception as e:
            logger.error(f"SVD training failed: {e}")
            self.is_trained = False
    
    def predict(self, user_id: str, place_id: str) -> float:
        """
        Predict rating for user-place pair
        
        Args:
            user_id: User ID
            place_id: Place ID
            
        Returns:
            Predicted rating [0, 5]
        """
        if not self.is_trained:
            return self.global_mean_rating
        
        # Check if user/place in training set
        if user_id not in self.user_to_idx or place_id not in self.place_to_idx:
            # Cold start: return global mean
            return self.global_mean_rating
        
        # Get indices
        u_idx = self.user_to_idx[user_id]
        p_idx = self.place_to_idx[place_id]
        
        # Get embeddings
        user_vec = self.user_embeddings[u_idx]  # (k,)
        place_vec = self.place_embeddings[p_idx]  # (k,)
        
        # Predicted rating = dot product
        predicted = np.dot(user_vec, place_vec)
        
        # Clip to valid range
        predicted = np.clip(predicted, 0, 5)
        
        return float(predicted)
    
    def calculate_collaborative_scores(
        self,
        user_id: str,
        candidate_places: List[Place]
    ) -> Dict[str, float]:
        """
        Calculate collaborative scores for candidate places
        
        Args:
            user_id: User ID
            candidate_places: Places to score
            
        Returns:
            Dict mapping place_id to collaborative score [0, 1]
        """
        if not self.is_trained:
            logger.warning("Model not trained, returning default scores (0.5)")
            return {place.place_id: 0.5 for place in candidate_places}
        
        # Cold start for new user
        if user_id not in self.user_to_idx:
            logger.info(f"User {user_id} not in training set (cold start), returning default scores")
            return {place.place_id: 0.5 for place in candidate_places}
        
        # Get user embedding
        u_idx = self.user_to_idx[user_id]
        user_vec = self.user_embeddings[u_idx]  # (k,)
        
        # Score each candidate
        scores = {}
        
        for place in candidate_places:
            if place.place_id in self.place_to_idx:
                # Place in training set - predict rating
                p_idx = self.place_to_idx[place.place_id]
                place_vec = self.place_embeddings[p_idx]
                
                # Predicted rating
                predicted_rating = np.dot(user_vec, place_vec)
                predicted_rating = np.clip(predicted_rating, 0, 5)
                
                # Normalize to [0, 1]
                normalized_score = predicted_rating / 5.0
                
            else:
                # New place (not in training) - use average
                normalized_score = self.global_mean_rating / 5.0
            
            scores[place.place_id] = float(normalized_score)
        
        logger.info(f"Calculated collaborative scores for {len(scores)} candidate places")
        
        # Log statistics
        if scores:
            avg_score = np.mean(list(scores.values()))
            logger.info(f"Avg collaborative score: {avg_score:.3f}")
        
        return scores
    
    def get_similar_places(
        self,
        place_id: str,
        k: int = 10,
        candidate_places: Optional[List[Place]] = None
    ) -> List[tuple]:
        """
        Find places similar to given place
        
        Uses cosine similarity between place embeddings
        
        Args:
            place_id: Reference place ID
            k: Number of similar places to return
            candidate_places: Optional list to search within
            
        Returns:
            List of (place_id, similarity_score) tuples
        """
        if not self.is_trained or place_id not in self.place_to_idx:
            return []
        
        # Get reference place embedding
        p_idx = self.place_to_idx[place_id]
        ref_vec = self.place_embeddings[p_idx]
        ref_norm = np.linalg.norm(ref_vec)
        
        if ref_norm == 0:
            return []
        
        # Calculate similarity with all places
        similarities = []
        
        # Determine search space
        if candidate_places:
            search_place_ids = [p.place_id for p in candidate_places if p.place_id in self.place_to_idx]
        else:
            search_place_ids = list(self.place_to_idx.keys())
        
        for pid in search_place_ids:
            if pid == place_id:
                continue  # Skip self
            
            p_idx = self.place_to_idx[pid]
            place_vec = self.place_embeddings[p_idx]
            place_norm = np.linalg.norm(place_vec)
            
            if place_norm > 0:
                # Cosine similarity
                similarity = np.dot(ref_vec, place_vec) / (ref_norm * place_norm)
                similarities.append((pid, float(similarity)))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    def _save_model(self):
        """Save trained model to disk"""
        if not self.is_trained:
            logger.warning("Model not trained, nothing to save")
            return
        
        model_file = self.model_dir / "collaborative_svd_model.pkl"
        
        model_data = {
            'user_embeddings': self.user_embeddings,
            'place_embeddings': self.place_embeddings,
            'sigma': self.sigma,
            'user_to_idx': self.user_to_idx,
            'idx_to_user': self.idx_to_user,
            'place_to_idx': self.place_to_idx,
            'idx_to_place': self.idx_to_place,
            'global_mean_rating': self.global_mean_rating,
            'n_factors': self.n_factors
        }
        
        try:
            with open(model_file, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"Model saved to {model_file}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def load_model(self) -> bool:
        """
        Load trained model from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        model_file = self.model_dir / "collaborative_svd_model.pkl"
        
        if not model_file.exists():
            logger.warning(f"Model file not found: {model_file}")
            return False
        
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.user_embeddings = model_data['user_embeddings']
            self.place_embeddings = model_data['place_embeddings']
            self.sigma = model_data['sigma']
            self.user_to_idx = model_data['user_to_idx']
            self.idx_to_user = model_data['idx_to_user']
            self.place_to_idx = model_data['place_to_idx']
            self.idx_to_place = model_data['idx_to_place']
            self.global_mean_rating = model_data['global_mean_rating']
            self.n_factors = model_data['n_factors']
            
            self.is_trained = True
            
            logger.info(f"Model loaded from {model_file}")
            logger.info(f"Users: {len(self.user_to_idx)}, Places: {len(self.place_to_idx)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def get_model_stats(self) -> Dict:
        """Get model statistics"""
        if not self.is_trained:
            return {'trained': False}
        
        return {
            'trained': True,
            'n_users': len(self.user_to_idx),
            'n_places': len(self.place_to_idx),
            'n_factors': self.n_factors,
            'global_mean_rating': self.global_mean_rating,
            'top_singular_value': float(self.sigma[0]) if self.sigma is not None else None
        }
