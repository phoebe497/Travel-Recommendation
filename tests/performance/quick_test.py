"""
Quick Performance Test
Chạy nhanh để kiểm tra cơ bản với data có sẵn
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmark_speed import SpeedBenchmark


def main():
    """Run quick performance test"""
    print("="*70)
    print("⚡ QUICK PERFORMANCE TEST")
    print("="*70)
    
    benchmark = SpeedBenchmark()
    
    # Run single test
    result = benchmark.benchmark_full_pipeline(
        city="Ho Chi Minh City",
        num_days=3,
        max_places=100
    )
    
    if "error" in result:
        print(f"\n❌ Test failed: {result['error']}")
        return 1
    
    # Print summary
    print("\n" + "="*70)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*70)
    print(f"Total time: {result['timings']['total_recommendation_time']:.2f}s")
    print(f"Places processed: {result['num_places']}")
    print(f"Places scheduled: {result['num_scheduled_places']}")
    print(f"Total cost: ${result['total_cost_usd']:.2f}")
    print("="*70)
    
    # Save results
    output_file = benchmark.save_results(result)
    print(f"\n📄 Full report: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
