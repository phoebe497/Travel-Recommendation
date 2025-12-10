"""
Benchmark Speed - Đo tốc độ từng bước của hệ thống
Đo thời gian cho: Load Data -> BERT Embeddings -> SVD Scoring -> Graph Building -> Scheduling
"""

import sys
from pathlib import Path
import time
import json
from typing import Dict, List
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import MongoDBHandler
from src.models import Place, UserPreference
from src.smart_itinerary_planner import SmartItineraryPlanner
from src.hybrid_recommender import HybridRecommender
from src.graph_builder import PlaceGraph


class SpeedBenchmark:
    """Benchmark tốc độ hệ thống"""
    
    def __init__(self):
        self.db = MongoDBHandler()
        self.results = {}
        
    def benchmark_full_pipeline(
        self, 
        city: str = "Ho Chi Minh City",
        num_days: int = 3,
        max_places: int = 200
    ) -> Dict:
        """
        Benchmark toàn bộ pipeline từ đầu đến cuối
        
        Returns:
            Dict với thời gian từng bước
        """
        print("="*70)
        print(f"🚀 SPEED BENCHMARK - {city} - {num_days} days - {max_places} places")
        print("="*70)
        
        timings = {}
        total_start = time.time()
        
        # Step 1: Load places from MongoDB
        print("\n⏱️  Step 1: Load Places from MongoDB...")
        step_start = time.time()
        places = self._load_places_from_db(city, max_places)
        timings["1_load_places"] = time.time() - step_start
        print(f"   ✅ Loaded {len(places)} places in {timings['1_load_places']:.3f}s")
        
        if len(places) == 0:
            print("❌ No places found! Cannot continue benchmark.")
            return {"error": "No places found", "city": city}
        
        # Step 2: Precompute BERT embeddings
        print("\n⏱️  Step 2: Precompute BERT Embeddings...")
        step_start = time.time()
        recommender = HybridRecommender()
        recommender.content_filter.precompute_embeddings(places)
        timings["2_bert_embeddings"] = time.time() - step_start
        print(f"   ✅ Computed embeddings in {timings['2_bert_embeddings']:.3f}s")
        
        # Step 3: Calculate hybrid scores
        print("\n⏱️  Step 3: Calculate Hybrid Scores (BERT + SVD)...")
        user_pref = self._create_sample_user_pref(city, num_days, places)
        step_start = time.time()
        
        try:
            scored_places = recommender.get_top_recommendations(
                user_pref=user_pref,
                candidate_places=places,
                selected_places=[],
                k=len(places)
            )
            hybrid_scores = {p.place_id: score for p, score in scored_places}
            timings["3_hybrid_scoring"] = time.time() - step_start
            print(f"   ✅ Calculated scores in {timings['3_hybrid_scoring']:.3f}s")
        except Exception as e:
            print(f"   ⚠️  Hybrid scoring failed: {e}. Using rating-based scoring.")
            hybrid_scores = None
            timings["3_hybrid_scoring"] = 0.0
        
        # Step 4: Build graph (Dijkstra preprocessing)
        print("\n⏱️  Step 4: Build Graph & Precompute Routes (Dijkstra)...")
        step_start = time.time()
        graph = PlaceGraph(places)
        timings["4_graph_building"] = time.time() - step_start
        print(f"   ✅ Built graph in {timings['4_graph_building']:.3f}s")
        
        # Step 5: Schedule itinerary
        print("\n⏱️  Step 5: Schedule Itinerary (Greedy Block Scheduling)...")
        step_start = time.time()
        
        from src.itinerary_builder import ItineraryBuilder
        builder = ItineraryBuilder(places)
        tour = builder.build_itinerary(
            user_pref=user_pref,
            start_date=None,
            hybrid_scores=hybrid_scores
        )
        timings["5_scheduling"] = time.time() - step_start
        print(f"   ✅ Scheduled {num_days} days in {timings['5_scheduling']:.3f}s")
        
        # Step 6: Optimize routes
        print("\n⏱️  Step 6: Optimize Routes (Transport Selection)...")
        step_start = time.time()
        tour = builder.optimize_itinerary(tour)
        timings["6_route_optimization"] = time.time() - step_start
        print(f"   ✅ Optimized routes in {timings['6_route_optimization']:.3f}s")
        
        # Total time (excluding file I/O)
        timings["total_recommendation_time"] = time.time() - total_start
        
        # Results
        print("\n" + "="*70)
        print("📊 TIMING BREAKDOWN")
        print("="*70)
        for key, value in timings.items():
            percentage = (value / timings["total_recommendation_time"] * 100) if timings["total_recommendation_time"] > 0 else 0
            print(f"   {key:30s}: {value:8.3f}s ({percentage:5.1f}%)")
        
        print("\n" + "="*70)
        print(f"🎯 TOTAL RECOMMENDATION TIME: {timings['total_recommendation_time']:.3f}s")
        print("="*70)
        
        # Additional metrics
        metrics = {
            "city": city,
            "num_days": num_days,
            "num_places": len(places),
            "num_scheduled_places": tour.get_total_places(),
            "total_cost_usd": tour.get_total_cost(),
            "timings": timings,
            "throughput_places_per_second": len(places) / timings["total_recommendation_time"] if timings["total_recommendation_time"] > 0 else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    
    def benchmark_scalability(self, city: str = "Ho Chi Minh City"):
        """
        Test scalability với số lượng places khác nhau
        """
        print("\n" + "="*70)
        print("📈 SCALABILITY BENCHMARK")
        print("="*70)
        
        test_sizes = [50, 100, 200]
        scalability_results = []
        
        for size in test_sizes:
            print(f"\n🔍 Testing with {size} places...")
            result = self.benchmark_full_pipeline(city=city, num_days=3, max_places=size)
            if "error" not in result:
                scalability_results.append(result)
                print(f"   ⏱️  Total time: {result['timings']['total_recommendation_time']:.3f}s")
        
        return scalability_results
    
    def _load_places_from_db(self, city: str, max_places: int) -> List[Place]:
        """Load places từ MongoDB"""
        places_collection = self.db.get_collection("places")
        
        # Query places in city, sorted by rating
        query = {"city": city}
        cursor = places_collection.find(query).sort("rating", -1).limit(max_places)
        
        places = []
        for doc in cursor:
            try:
                place = Place.from_dict(doc)
                places.append(place)
            except Exception as e:
                print(f"   ⚠️  Failed to load place: {e}")
                continue
        
        return places
    
    def _create_sample_user_pref(
        self, 
        city: str, 
        num_days: int, 
        places: List[Place]
    ) -> UserPreference:
        """Tạo user preference mẫu cho test"""
        # Randomly select some places as liked (top 5 by rating)
        selected_places = [p.place_id for p in sorted(places, key=lambda x: x.rating, reverse=True)[:5]]
        
        return UserPreference(
            user_id="benchmark_user",
            destination_city=city,
            trip_duration_days=num_days,
            selected_places=selected_places,
            interests=["culture", "food", "nature"],
            budget_range="medium",
            travel_party="couple"
        )
    
    def save_results(self, results: Dict, output_path: str = None):
        """Lưu kết quả vào JSON file"""
        if output_path is None:
            output_path = Path(__file__).parent / "reports" / f"speed_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")
        return str(output_path)


def main():
    """Main entry point"""
    benchmark = SpeedBenchmark()
    
    # Run single benchmark
    print("\n🎯 Running single benchmark...")
    result = benchmark.benchmark_full_pipeline(
        city="Ho Chi Minh City",
        num_days=3,
        max_places=200
    )
    
    # Run scalability test
    print("\n\n📊 Running scalability test...")
    scalability_results = benchmark.benchmark_scalability(city="Ho Chi Minh City")
    
    # Save results
    all_results = {
        "single_benchmark": result,
        "scalability_benchmark": scalability_results
    }
    benchmark.save_results(all_results)
    
    print("\n✅ Benchmark completed!")


if __name__ == "__main__":
    main()
