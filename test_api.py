"""
Quick API Testing Script
========================
Tests both endpoints to ensure API is working correctly.

Usage:
    python test_api.py
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API Configuration
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_health_check():
    """Test health endpoint"""
    print("=" * 60)
    print("1. Testing Health Check...")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed! Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is it running?")
        print("Run: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_generate_itinerary():
    """Test generate itinerary endpoint"""
    print("\n" + "=" * 60)
    print("2. Testing Generate Itinerary (Full Pipeline)...")
    print("=" * 60)
    
    # Test payload
    payload = {
        "destination": "Ho Chi Minh",
        "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "num_days": 3,
        "budget": 5000000,
        "travel_party": "couple",
        "interests": ["food", "culture", "shopping"],
        "selected_place_ids": []  # Empty to test pure recommendation
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        print("\n⏳ Sending request (this may take 5-45 seconds)...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/generate-itinerary",
            json=payload,
            headers=HEADERS,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Itinerary generated successfully! (took {elapsed:.2f}s)")
            
            data = response.json()
            print(f"\n📋 Itinerary Summary:")
            print(f"  - Tour ID: {data.get('tour_id', 'N/A')}")
            print(f"  - Destination: {data.get('destination', 'N/A')}")
            print(f"  - Total Days: {data.get('total_days', 'N/A')}")
            print(f"  - Estimated Cost: {data.get('estimated_cost', 'N/A'):,} VND")
            print(f"  - Processing Time: {data.get('processing_time_seconds', 'N/A'):.2f}s")
            
            if 'days' in data and len(data['days']) > 0:
                print(f"\n📅 Day 1 Activities:")
                day1 = data['days'][0]
                for activity in day1.get('activities', [])[:3]:  # Show first 3
                    place = activity.get('place', {})
                    print(f"  • {activity.get('time_block', 'N/A')}: {place.get('name', 'N/A')} (⭐ {place.get('rating', 'N/A')})")
            
            # Save full response
            with open('test_itinerary_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Full response saved to: test_itinerary_response.json")
            
            return True
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out! API might be processing slowly.")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_get_recommendations():
    """Test recommendations endpoint"""
    print("\n" + "=" * 60)
    print("3. Testing Get Recommendations (No Scheduling)...")
    print("=" * 60)
    
    payload = {
        "destination": "Ho Chi Minh",
        "interests": ["nightlife", "shopping", "landmarks"],
        "budget": 3000000,
        "travel_party": "friends",
        "top_k": 10
    }
    
    print(f"Request payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    
    try:
        print("\n⏳ Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/recommendations",
            json=payload,
            headers=HEADERS,
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ Recommendations retrieved! (took {elapsed:.2f}s)")
            
            data = response.json()
            print(f"\n🎯 Top {len(data.get('recommendations', []))} Recommendations:")
            
            for i, rec in enumerate(data.get('recommendations', [])[:5], 1):  # Show top 5
                print(f"  {i}. {rec.get('name', 'N/A')} (Score: {rec.get('score', 0):.3f}, ⭐ {rec.get('rating', 'N/A')})")
            
            # Save response
            with open('test_recommendations_response.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Full response saved to: test_recommendations_response.json")
            
            return True
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🧪" * 30)
    print("API TESTING SUITE - Travel Recommendation System")
    print("🧪" * 30 + "\n")
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    if not results[0][1]:
        print("\n⚠️ API is not running. Start with: docker-compose up -d")
        return
    
    # Test 2: Generate itinerary
    results.append(("Generate Itinerary", test_generate_itinerary()))
    
    # Test 3: Get recommendations
    results.append(("Get Recommendations", test_get_recommendations()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! API is ready for integration.")
    else:
        print("\n⚠️ Some tests failed. Check logs and documentation.")

if __name__ == "__main__":
    main()
