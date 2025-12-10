"""
Evaluate Recommendation Quality
Đánh giá độ chính xác của thuật toán recommendation sử dụng:
- Binary Classification Metrics: TP, FP, FN, TN, POD (Recall), FAR, Precision, F1-Score
- Sử dụng tour history làm ground truth
"""

import sys
from pathlib import Path
import json
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import MongoDBHandler
from src.models import Place, UserPreference
from src.hybrid_recommender import HybridRecommender


class RecommendationEvaluator:
    """Đánh giá chất lượng recommendation"""
    
    def __init__(self):
        self.db = MongoDBHandler()
        
    def evaluate_with_tour_history(
        self, 
        city: str = "Ho Chi Minh City",
        k_recommendations: int = 20
    ) -> Dict:
        """
        Đánh giá recommendation bằng tour history
        
        Ground Truth: Places mà users đã từng chọn trong tours
        Predictions: Top-K recommendations từ hệ thống
        
        Args:
            city: Thành phố để test
            k_recommendations: Số lượng recommendations (top-K)
            
        Returns:
            Dict chứa metrics: TP, FP, FN, TN, POD, FAR, Precision, F1
        """
        print("="*70)
        print(f"📊 RECOMMENDATION QUALITY EVALUATION - {city}")
        print("="*70)
        
        # Step 1: Load all places
        print("\n⏱️  Step 1: Load Places...")
        places = self._load_places_from_db(city)
        if len(places) == 0:
            print("❌ No places found!")
            return {"error": "No places found"}
        
        place_dict = {p.place_id: p for p in places}
        print(f"   ✅ Loaded {len(places)} places")
        
        # Step 2: Get user-place interactions from tours
        print("\n⏱️  Step 2: Extract Ground Truth from Tours...")
        user_interactions = self._get_user_interactions_from_tours(city)
        
        if len(user_interactions) == 0:
            print("❌ No tour data found!")
            return {"error": "No tour data found"}
        
        print(f"   ✅ Found {len(user_interactions)} users with tour history")
        
        # Step 3: Evaluate recommendations for each user
        print("\n⏱️  Step 3: Evaluate Recommendations...")
        recommender = HybridRecommender()
        
        # Precompute BERT embeddings once
        recommender.content_filter.precompute_embeddings(places)
        
        all_metrics = []
        
        for user_id, liked_places in user_interactions.items():
            # Create user preference
            user_pref = UserPreference(
                user_id=user_id,
                destination_city=city,
                trip_duration_days=3,
                selected_places=liked_places[:3],  # Use first 3 as seed
                interests=["culture", "food"],
                budget_range="medium"
            )
            
            # Get recommendations
            try:
                selected_place_objects = [place_dict[pid] for pid in user_pref.selected_places if pid in place_dict]
                
                scored_places = recommender.get_top_recommendations(
                    user_pref=user_pref,
                    candidate_places=places,
                    selected_places=selected_place_objects,
                    k=k_recommendations
                )
                
                recommended_ids = [p.place_id for p, score in scored_places]
                
                # Calculate metrics
                metrics = self._calculate_binary_metrics(
                    recommended_places=recommended_ids,
                    ground_truth_liked=liked_places,
                    all_candidates=[p.place_id for p in places]
                )
                
                all_metrics.append(metrics)
                
            except Exception as e:
                print(f"   ⚠️  Failed to evaluate user {user_id}: {e}")
                continue
        
        # Aggregate metrics
        print(f"\n   ✅ Evaluated {len(all_metrics)} users")
        
        if len(all_metrics) == 0:
            print("❌ No successful evaluations!")
            return {"error": "No successful evaluations"}
        
        # Average metrics
        avg_metrics = self._average_metrics(all_metrics)
        
        # Print results
        print("\n" + "="*70)
        print("📊 EVALUATION RESULTS")
        print("="*70)
        print(f"   Number of users evaluated: {len(all_metrics)}")
        print(f"   Top-K recommendations: {k_recommendations}")
        print(f"\n   Confusion Matrix (Average):")
        print(f"      True Positives  (TP): {avg_metrics['TP']:.1f}")
        print(f"      False Positives (FP): {avg_metrics['FP']:.1f}")
        print(f"      False Negatives (FN): {avg_metrics['FN']:.1f}")
        print(f"      True Negatives  (TN): {avg_metrics['TN']:.1f}")
        print(f"\n   Performance Metrics:")
        print(f"      POD (Recall)    : {avg_metrics['POD']:.3f} ({avg_metrics['POD']*100:.1f}%)")
        print(f"      Precision       : {avg_metrics['Precision']:.3f} ({avg_metrics['Precision']*100:.1f}%)")
        print(f"      F1-Score        : {avg_metrics['F1']:.3f}")
        print(f"      FAR (False Alarm): {avg_metrics['FAR']:.3f} ({avg_metrics['FAR']*100:.1f}%)")
        print("="*70)
        
        result = {
            "city": city,
            "k_recommendations": k_recommendations,
            "num_users_evaluated": len(all_metrics),
            "average_metrics": avg_metrics,
            "all_user_metrics": all_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _load_places_from_db(self, city: str) -> List[Place]:
        """Load places từ MongoDB"""
        places_collection = self.db.get_collection("places")
        query = {"city": city}
        cursor = places_collection.find(query)
        
        places = []
        for doc in cursor:
            try:
                place = Place.from_dict(doc)
                places.append(place)
            except Exception as e:
                continue
        
        return places
    
    def _get_user_interactions_from_tours(self, city: str) -> Dict[str, List[str]]:
        """
        Lấy user-place interactions từ tours collection
        
        Returns:
            Dict[user_id] -> List[place_ids] (places user đã visit)
        """
        tours_collection = self.db.get_collection("tours")
        
        # Query tours by destination field (not destination_city)
        query = {"destination": city}
        tours = list(tours_collection.find(query))
        
        if len(tours) == 0:
            # Try alternative field names
            query = {"destination_city": city}
            tours = list(tours_collection.find(query))
        
        print(f"   📍 Found {len(tours)} tours in {city}")
        
        # Extract user-place interactions
        user_interactions = defaultdict(list)
        
        for tour in tours:
            # Get user_id from participants or user_id field
            user_id = None
            if "participants" in tour and isinstance(tour["participants"], list) and len(tour["participants"]) > 0:
                user_id = str(tour["participants"][0])  # Use first participant
            elif "user_id" in tour:
                user_id = tour["user_id"]
            
            if not user_id:
                continue
            
            # Extract place IDs from tour
            place_ids = []
            
            # Try different tour formats
            if "itinerary" in tour:
                # Standard format with itinerary
                for day in tour.get("itinerary", []):
                    # Get places from places array
                    for place in day.get("places", []):
                        if "place_id" in place:
                            place_ids.append(place["place_id"])
            
            elif "daily_itineraries" in tour:
                # New format with daily itineraries
                for day in tour.get("daily_itineraries", []):
                    for block_name, place in day.items():
                        if isinstance(place, dict) and "place_id" in place:
                            place_ids.append(place["place_id"])
            
            # Add to user interactions
            if place_ids:
                user_interactions[user_id].extend(place_ids)
        
        # Remove duplicates for each user
        for user_id in user_interactions:
            user_interactions[user_id] = list(set(user_interactions[user_id]))
        
        # Print sample for debugging
        if user_interactions:
            sample_user = list(user_interactions.keys())[0]
            print(f"   📌 Sample: User {sample_user[:20]}... visited {len(user_interactions[sample_user])} places")
        
        return dict(user_interactions)
    
    def _calculate_binary_metrics(
        self,
        recommended_places: List[str],
        ground_truth_liked: List[str],
        all_candidates: List[str]
    ) -> Dict:
        """
        Calculate binary classification metrics
        
        Args:
            recommended_places: Places được recommend (Positive predictions)
            ground_truth_liked: Places user thực sự thích (Ground truth positives)
            all_candidates: Tất cả places có thể recommend
            
        Returns:
            Dict với TP, FP, FN, TN, POD, FAR, Precision, F1
        """
        recommended_set = set(recommended_places)
        liked_set = set(ground_truth_liked)
        all_set = set(all_candidates)
        
        # Confusion matrix
        TP = len(recommended_set & liked_set)  # Recommended AND liked
        FP = len(recommended_set - liked_set)  # Recommended but NOT liked
        FN = len(liked_set - recommended_set)  # NOT recommended but liked
        TN = len(all_set - recommended_set - liked_set)  # NOT recommended AND NOT liked
        
        # Metrics
        POD = TP / (TP + FN) if (TP + FN) > 0 else 0.0  # Recall
        Precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        F1 = 2 * (Precision * POD) / (Precision + POD) if (Precision + POD) > 0 else 0.0
        FAR = FP / (FP + TN) if (FP + TN) > 0 else 0.0
        
        return {
            "TP": TP,
            "FP": FP,
            "FN": FN,
            "TN": TN,
            "POD": POD,
            "FAR": FAR,
            "Precision": Precision,
            "F1": F1
        }
    
    def _average_metrics(self, all_metrics: List[Dict]) -> Dict:
        """Tính trung bình các metrics"""
        if not all_metrics:
            return {}
        
        avg = {
            "TP": np.mean([m["TP"] for m in all_metrics]),
            "FP": np.mean([m["FP"] for m in all_metrics]),
            "FN": np.mean([m["FN"] for m in all_metrics]),
            "TN": np.mean([m["TN"] for m in all_metrics]),
            "POD": np.mean([m["POD"] for m in all_metrics]),
            "FAR": np.mean([m["FAR"] for m in all_metrics]),
            "Precision": np.mean([m["Precision"] for m in all_metrics]),
            "F1": np.mean([m["F1"] for m in all_metrics])
        }
        
        return avg
    
    def save_results(self, results: Dict, output_path: str = None):
        """Lưu kết quả vào JSON file"""
        if output_path is None:
            output_path = Path(__file__).parent / "reports" / f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
        return str(output_path)


def main():
    """Main entry point"""
    evaluator = RecommendationEvaluator()
    
    # Evaluate with different K values
    for k in [10, 20, 50]:
        print(f"\n{'='*70}")
        print(f"Testing with Top-{k} Recommendations")
        print(f"{'='*70}")
        
        result = evaluator.evaluate_with_tour_history(
            city="Ho Chi Minh City",
            k_recommendations=k
        )
        
        if "error" not in result:
            # Save results
            output_path = Path(__file__).parent / "reports" / f"evaluation_top{k}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            evaluator.save_results(result, str(output_path))
    
    print("\n✅ Evaluation completed!")


if __name__ == "__main__":
    main()
