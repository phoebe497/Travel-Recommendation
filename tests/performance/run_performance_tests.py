"""
Run All Performance Tests
Script tổng hợp để chạy tất cả các tests: Speed + Accuracy
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark_speed import SpeedBenchmark
from evaluate_recommendation import RecommendationEvaluator


def run_all_performance_tests(city: str = "Ho Chi Minh City"):
    """
    Chạy tất cả performance tests
    
    Args:
        city: Thành phố để test
    """
    print("="*70)
    print("🚀 PERFORMANCE TEST SUITE - TRAVEL RECOMMENDATION SYSTEM")
    print("="*70)
    print(f"City: {city}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    all_results = {
        "city": city,
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # ==========================================
    # TEST 1: Speed Benchmark
    # ==========================================
    print("\n\n" + "🔥"*35)
    print("TEST 1: SPEED BENCHMARK")
    print("🔥"*35)
    
    try:
        speed_benchmark = SpeedBenchmark()
        
        # Single benchmark
        print("\n📊 Running single benchmark (100 places, 3 days)...")
        single_result = speed_benchmark.benchmark_full_pipeline(
            city=city,
            num_days=3,
            max_places=100
        )
        
        # Scalability test
        print("\n📈 Running scalability test...")
        scalability_results = speed_benchmark.benchmark_scalability(city=city)
        
        # Save speed results
        speed_results = {
            "single_benchmark": single_result,
            "scalability_benchmark": scalability_results
        }
        speed_output = speed_benchmark.save_results(speed_results)
        
        all_results["tests"]["speed_benchmark"] = {
            "status": "success",
            "summary": {
                "total_time": single_result.get("timings", {}).get("total_recommendation_time", 0),
                "num_places": single_result.get("num_places", 0),
                "throughput": single_result.get("throughput_places_per_second", 0)
            }
        }
        
        print("\n✅ Speed Benchmark completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Speed Benchmark failed: {e}")
        all_results["tests"]["speed_benchmark"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # ==========================================
    # TEST 2: Recommendation Quality Evaluation
    # ==========================================
    print("\n\n" + "🎯"*35)
    print("TEST 2: RECOMMENDATION QUALITY EVALUATION")
    print("🎯"*35)
    
    try:
        evaluator = RecommendationEvaluator()
        
        # Evaluate with Top-20 recommendations
        print("\n📊 Evaluating with Top-20 recommendations...")
        eval_result = evaluator.evaluate_with_tour_history(
            city=city,
            k_recommendations=20
        )
        
        if "error" not in eval_result:
            # Save evaluation results
            eval_output = evaluator.save_results(eval_result)
            
            all_results["tests"]["recommendation_evaluation"] = {
                "status": "success",
                "output_file": eval_output,
                "summary": {
                    "num_users": eval_result.get("num_users_evaluated", 0),
                    "precision": eval_result.get("average_metrics", {}).get("Precision", 0),
                    "recall_pod": eval_result.get("average_metrics", {}).get("POD", 0),
                    "f1_score": eval_result.get("average_metrics", {}).get("F1", 0),
                    "far": eval_result.get("average_metrics", {}).get("FAR", 0)
                }
            }
            
            print("\n✅ Recommendation Evaluation completed successfully!")
        else:
            all_results["tests"]["recommendation_evaluation"] = {
                "status": "failed",
                "error": eval_result["error"]
            }
            print(f"\n❌ Recommendation Evaluation failed: {eval_result['error']}")
            
    except Exception as e:
        print(f"\n❌ Recommendation Evaluation failed: {e}")
        all_results["tests"]["recommendation_evaluation"] = {
            "status": "failed",
            "error": str(e)
        }
    
    # ==========================================
    # Save Summary Report
    # ==========================================
    print("\n\n" + "="*70)
    print("📝 GENERATING SUMMARY REPORT")
    print("="*70)
    
    report_path = Path(__file__).parent / "reports" / f"performance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Summary report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*70)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("="*70)
    
    for test_name, test_result in all_results["tests"].items():
        status_icon = "✅" if test_result["status"] == "success" else "❌"
        print(f"\n{status_icon} {test_name.upper().replace('_', ' ')}")
        print(f"   Status: {test_result['status']}")
        
        if test_result["status"] == "success":
            if "summary" in test_result:
                print("   Summary:")
                for key, value in test_result["summary"].items():
                    if isinstance(value, float):
                        print(f"      {key}: {value:.3f}")
                    else:
                        print(f"      {key}: {value}")
            if "output_file" in test_result:
                print(f"   Output: {test_result['output_file']}")
        else:
            print(f"   Error: {test_result.get('error', 'Unknown error')}")
    
    print("\n" + "="*70)
    print("🎉 ALL TESTS COMPLETED!")
    print("="*70)
    
    return all_results


def main():
    """Main entry point"""
    # Test with Ho Chi Minh City (default)
    results = run_all_performance_tests(city="Ho Chi Minh City")
    
    # Check if all tests passed
    all_passed = all(
        test["status"] == "success" 
        for test in results["tests"].values()
    )
    
    if all_passed:
        print("\n✅ All performance tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the reports for details.")
        return 1


if __name__ == "__main__":
    exit(main())
