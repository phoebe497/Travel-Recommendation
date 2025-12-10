"""
Test loading real user preferences from MongoDB
Validates integration with user_preferences and tours collections
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database import MongoDBHandler
from src.models import UserPreference, Place
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_load_user_preferences():
    """Test loading user preferences from MongoDB"""
    print("=" * 80)
    print("TEST: Load Real User Preferences from MongoDB")
    print("=" * 80)
    
    db = MongoDBHandler()
    
    # Test 1: Get all valid user preferences (cities with places)
    print("\n📊 Step 1: Load user preferences with valid cities...")
    valid_prefs = db.get_all_user_preferences_with_places()
    
    print(f"✅ Found {len(valid_prefs)} users with cities that have places")
    
    if not valid_prefs:
        print("❌ No valid user preferences found!")
        return
    
    # Test 2: Convert to UserPreference objects
    print("\n👤 Step 2: Convert MongoDB docs to UserPreference objects...")
    user_preferences = []
    
    for pref_doc in valid_prefs[:5]:  # Test first 5 users
        user_pref = UserPreference.from_mongo(
            pref_doc,
            trip_duration_days=3,
            budget_range="medium",
            travel_party="solo"
        )
        user_preferences.append(user_pref)
        
        print(f"\n  User: {user_pref.user_id[:16]}...")
        print(f"  City: {user_pref.destination_city}")
        print(f"  Liked places: {len(user_pref.selected_places)}")
        print(f"  Disliked places: {len(user_pref.disliked_places)}")
        print(f"  Interests: {', '.join(user_pref.interests)}")
        
        # Calculate alpha
        alpha = user_pref.calculate_alpha()
        print(f"  Calculated alpha: {alpha}")
    
    # Test 3: Validate selected places exist in places collection
    print("\n\n🔍 Step 3: Validate selected places exist in DB...")
    
    test_user = user_preferences[0]
    print(f"Testing user: {test_user.user_id[:16]}... ({test_user.destination_city})")
    
    places_collection = db.get_collection("places")
    found_count = 0
    missing_count = 0
    
    for place_id in test_user.selected_places[:10]:  # Check first 10
        place_doc = places_collection.find_one({"id": place_id})
        if place_doc:
            place = Place.from_dict(place_doc)
            print(f"  ✅ {place.name} (rating: {place.rating})")
            found_count += 1
        else:
            print(f"  ❌ Missing: {place_id}")
            missing_count += 1
    
    print(f"\n  Found: {found_count}, Missing: {missing_count}")
    
    # Test 4: Check city has places
    print(f"\n\n🏙️  Step 4: Verify city has places...")
    city_name = test_user.destination_city
    has_places = db.city_has_places(city_name)
    
    if has_places:
        total_places = places_collection.count_documents({"city": city_name})
        print(f"  ✅ {city_name} has {total_places} places in DB")
    else:
        print(f"  ❌ {city_name} has NO places in DB")
    
    print("\n" + "=" * 80)
    print("✅ USER PREFERENCES TEST COMPLETE")
    print("=" * 80)


def test_load_tour_interactions():
    """Test loading tour interactions for collaborative filter"""
    print("\n" + "=" * 80)
    print("TEST: Load Tour Interactions for Collaborative Filter")
    print("=" * 80)
    
    db = MongoDBHandler()
    
    # Load interactions
    print("\n📚 Loading tour interactions...")
    interactions = db.get_tour_interactions_for_collaborative_filter()
    
    print(f"✅ Loaded {len(interactions)} interactions")
    
    if interactions:
        # Show sample
        print("\n📋 Sample interactions:")
        for interaction in interactions[:10]:
            print(f"  User: {interaction['user_id'][:16]}... → "
                  f"Place: {interaction['place_id'][:20]}... → "
                  f"Rating: {interaction['rating']}")
        
        # Statistics
        unique_users = len(set(i['user_id'] for i in interactions))
        unique_places = len(set(i['place_id'] for i in interactions))
        avg_rating = sum(i['rating'] for i in interactions) / len(interactions)
        
        print(f"\n📊 Statistics:")
        print(f"  Unique users: {unique_users}")
        print(f"  Unique places: {unique_places}")
        print(f"  Average rating: {avg_rating:.2f}")
        print(f"  Interactions per user: {len(interactions) / unique_users:.1f}")
    
    print("\n" + "=" * 80)
    print("✅ TOUR INTERACTIONS TEST COMPLETE")
    print("=" * 80)


def test_city_validation():
    """Test city validation - ensure we skip cities without places"""
    print("\n" + "=" * 80)
    print("TEST: City Validation (Skip cities without places)")
    print("=" * 80)
    
    db = MongoDBHandler()
    
    # Get ALL user preferences (without filtering)
    collection = db.get_collection("user_preferences")
    all_prefs = list(collection.find())
    
    print(f"\n📊 Total user preferences in DB: {len(all_prefs)}")
    
    # Check each city
    cities_with_places = 0
    cities_without_places = 0
    
    cities_checked = set()
    
    for pref in all_prefs:
        city_name = pref.get("city_name", "")
        if city_name and city_name not in cities_checked:
            cities_checked.add(city_name)
            has_places = db.city_has_places(city_name)
            
            if has_places:
                places_count = db.get_collection("places").count_documents({"city": city_name})
                print(f"  ✅ {city_name}: {places_count} places")
                cities_with_places += 1
            else:
                print(f"  ❌ {city_name}: NO places (will be skipped)")
                cities_without_places += 1
    
    print(f"\n📊 Summary:")
    print(f"  Cities with places: {cities_with_places}")
    print(f"  Cities without places: {cities_without_places}")
    print(f"  Coverage: {cities_with_places / len(cities_checked) * 100:.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ CITY VALIDATION TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_load_user_preferences()
        test_load_tour_interactions()
        test_city_validation()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ TEST FAILED: {e}")
