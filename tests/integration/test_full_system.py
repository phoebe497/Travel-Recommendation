"""
Full System Integration Test
Tests the complete itinerary generation pipeline with real MongoDB data
Outputs are saved to /outputs with timestamps and city names
"""

import sys
import io
from pathlib import Path
from datetime import datetime
import json
import logging

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.smart_itinerary_planner import SmartItineraryPlanner
from src.database import MongoDBHandler
from src.models import UserPreference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_outputs_directory():
    """Create outputs directory if it doesn't exist"""
    outputs_dir = Path(__file__).parent.parent.parent / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir


def save_itinerary_to_file(itinerary_dict: dict, city_name: str, outputs_dir: Path):
    """Save itinerary to JSON file with timestamp and city name"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sanitize city name for filename
    safe_city_name = city_name.replace(" ", "_").replace("/", "-")
    filename = f"{safe_city_name}_{timestamp}.json"
    
    filepath = outputs_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(itinerary_dict, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Saved itinerary to: {filepath}")
    return filepath


def test_single_user(db: MongoDBHandler, user_pref_doc: dict, outputs_dir: Path):
    """Test itinerary generation for a single user"""
    user_id = user_pref_doc.get("user_id", "unknown")
    city_name = user_pref_doc.get("city_name", "Unknown")
    
    print(f"\n{'='*80}")
    print(f"Testing User: {user_id[:16]}... → {city_name}")
    print(f"{'='*80}")
    
    try:
        # Step 1: Convert to UserPreference object
        print(f"\n📋 Step 1: Loading user preferences...")
        user_pref = UserPreference.from_mongo(
            user_pref_doc,
            trip_duration_days=3,
            budget_range="medium",
            travel_party="solo"
        )
        
        print(f"  ✅ User ID: {user_pref.user_id[:16]}...")
        print(f"  ✅ Destination: {user_pref.destination_city}")
        print(f"  ✅ Duration: {user_pref.trip_duration_days} days")
        print(f"  ✅ Selected places: {len(user_pref.selected_places)}")
        print(f"  ✅ Disliked places: {len(user_pref.disliked_places)}")
        print(f"  ✅ Interests: {', '.join(user_pref.interests)}")
        print(f"  ✅ Alpha: {user_pref.calculate_alpha()}")
        
        # Step 2: Initialize planner
        print(f"\n🚀 Step 2: Initializing SmartItineraryPlanner...")
        planner = SmartItineraryPlanner(
            db_handler=db,
            use_hybrid_scoring=True
        )
        print(f"  ✅ Planner initialized")
        
        # Step 3: Generate itinerary
        print(f"\n🗓️  Step 3: Generating itinerary...")
        tour = planner.generate_itinerary(user_pref)
        
        if not tour:
            print(f"  ❌ Failed to generate itinerary")
            return None
        
        print(f"  ✅ Itinerary generated successfully!")
        
        # Step 4: Display summary
        print(f"\n📊 Step 4: Itinerary Summary")
        print(f"  Destination: {tour.destination}")
        print(f"  Days: {len(tour.daily_itineraries)}")
        
        total_places = sum(len(day.get_all_scheduled_places()) for day in tour.daily_itineraries)
        print(f"  Total places: {total_places}")
        
        for day_idx, day in enumerate(tour.daily_itineraries, 1):
            print(f"\n  Day {day_idx}: {len(day.get_all_scheduled_places())} places")
            all_places = day.get_all_scheduled_places()
            for place in all_places[:3]:  # Show first 3 places
                print(f"    • {place.place.name} (rating: {place.place.rating})")
            if len(all_places) > 3:
                print(f"    ... and {len(all_places) - 3} more places")
        
        # Step 5: Save to file
        print(f"\n💾 Step 5: Saving to outputs directory...")
        itinerary_dict = tour.to_dict()
        filepath = save_itinerary_to_file(itinerary_dict, city_name, outputs_dir)
        
        print(f"\n✅ SUCCESS! Itinerary saved to: {filepath.name}")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Failed to generate itinerary for {city_name}: {e}", exc_info=True)
        print(f"❌ Error: {e}")
        return None


def test_full_system():
    """Test full system with real MongoDB data"""
    print("=" * 80)
    print("FULL SYSTEM INTEGRATION TEST")
    print("Testing with Real MongoDB Data")
    print("=" * 80)
    
    # Initialize
    db = MongoDBHandler()
    outputs_dir = ensure_outputs_directory()
    
    print(f"\nOutputs directory: {outputs_dir}")
    print(f"MongoDB: Connected")
    
    # Load all valid user preferences
    print(f"\nLoading user preferences from MongoDB...")
    all_user_prefs = db.get_all_user_preferences_with_places()
    
    print(f"Found {len(all_user_prefs)} valid user preferences")
    
    if not all_user_prefs:
        print("❌ No user preferences found!")
        return
    
    # Test with first 3 users (different cities)
    print(f"\n🎯 Testing with first 3 users...")
    
    successful = 0
    failed = 0
    generated_files = []
    
    for i, user_pref_doc in enumerate(all_user_prefs[:3], 1):
        print(f"\n{'#'*80}")
        print(f"Test {i}/3")
        print(f"{'#'*80}")
        
        filepath = test_single_user(db, user_pref_doc, outputs_dir)
        
        if filepath:
            successful += 1
            generated_files.append(filepath)
        else:
            failed += 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {successful + failed}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if generated_files:
        print(f"\n📁 Generated files:")
        for filepath in generated_files:
            print(f"  • {filepath.name}")
    
    print("\n" + "=" * 80)
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} TEST(S) FAILED")
    print("=" * 80)


def test_specific_city(city_name: str):
    """Test itinerary generation for a specific city"""
    print("=" * 80)
    print(f"TESTING SPECIFIC CITY: {city_name}")
    print("=" * 80)
    
    db = MongoDBHandler()
    outputs_dir = ensure_outputs_directory()
    
    # Find user preference for this city
    collection = db.get_collection("user_preferences")
    user_pref_doc = collection.find_one({"city_name": city_name})
    
    if not user_pref_doc:
        print(f"❌ No user preference found for {city_name}")
        return
    
    # Verify city has places
    if not db.city_has_places(city_name):
        print(f"❌ City {city_name} has no places in database")
        return
    
    # Test
    filepath = test_single_user(db, user_pref_doc, outputs_dir)
    
    if filepath:
        print(f"\n🎉 SUCCESS! Generated itinerary for {city_name}")
    else:
        print(f"\n❌ FAILED to generate itinerary for {city_name}")


if __name__ == "__main__":
    import sys
    
    try:
        # Check if specific city was provided
        if len(sys.argv) > 1:
            city_name = " ".join(sys.argv[1:])
            test_specific_city(city_name)
        else:
            # Run full system test
            test_full_system()
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")
