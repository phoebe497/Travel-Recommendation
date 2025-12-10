"""
Test MongoDB Schema Loading
Verify that data loading works with actual MongoDB schema
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_database
from src.models import Place
from src.place_filter import PlaceFilter
from src.config import TimeBlockConfig, BlockType
from datetime import time


def test_load_places():
    """Test loading places from MongoDB"""
    print("=" * 80)
    print("TEST 1: Load Places from MongoDB")
    print("=" * 80)
    
    db = get_database()
    places_collection = db.get_collection("places")
    
    # Load diverse places from Bangkok (various types, sorted by rating)
    cursor = places_collection.find({"city": "Hanoi"}).sort("rating", -1).limit(50)
    
    places = []
    for doc in cursor:
        try:
            place = Place.from_dict(doc)
            places.append(place)
            
            if len(places) <= 5:  # Show details for first 5
                print(f"\n✓ Loaded: {place.name}")
                print(f"  - ID: {place.place_id}")
                print(f"  - City: {place.city}")
                print(f"  - Rating: {place.rating}")
                print(f"  - Types: {place.types[:3]}")  # First 3 types
                print(f"  - Location: ({place.latitude:.4f}, {place.longitude:.4f})")
                print(f"  - Avg Price: ${place.avg_price:.2f}")
                print(f"  - Has Opening Hours: {place.opening_hours is not None}")
            
        except Exception as e:
            print(f"\n✗ Failed to load place: {e}")
            print(f"  Document ID: {doc.get('_id')}")
            continue
    
    # Show type distribution
    type_counts = {}
    for place in places:
        for ptype in place.types[:2]:  # Count first 2 types
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
    
    print(f"\n{'=' * 80}")
    print(f"Successfully loaded {len(places)} places")
    print(f"\n📊 Type Distribution:")
    for ptype, count in sorted(type_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {ptype}: {count}")
    print(f"{'=' * 80}\n")
    
    return places


def test_opening_hours_parsing(places):
    """Test opening hours parsing"""
    print("=" * 80)
    print("TEST 2: Opening Hours Parsing")
    print("=" * 80)
    
    for place in places[:5]:  # Test first 5
        print(f"\n📍 {place.name}")
        
        if place.opening_hours:
            hours_dict = PlaceFilter.parse_opening_hours(place.opening_hours)
            
            if "all_days" in hours_dict:
                print(f"  ⏰ Default hours: {hours_dict['all_days']}")
            else:
                for day, periods in list(hours_dict.items())[:3]:  # First 3 days
                    print(f"  ⏰ {day.capitalize()}: {periods}")
        else:
            print("  ⏰ No opening hours data")
    
    print(f"\n{'=' * 80}\n")


def test_block_filtering(places):
    """Test filtering places for time blocks"""
    print("=" * 80)
    print("TEST 3: Block Filtering")
    print("=" * 80)
    
    # Test breakfast block
    breakfast_block = TimeBlockConfig.BLOCKS[BlockType.BREAKFAST]
    print(f"\n🍳 Testing Breakfast Block: {breakfast_block.start_time} - {breakfast_block.end_time}")
    
    breakfast_candidates = PlaceFilter.get_candidate_places(
        all_places=places,
        block=breakfast_block,
        day_of_week=0,  # Monday
        min_rating=3.0
    )
    
    print(f"  Found {len(breakfast_candidates)} candidates")
    for place in breakfast_candidates[:3]:
        print(f"    - {place.name} (rating: {place.rating}, types: {place.types[:2]})")
    
    # Test lunch block
    lunch_block = TimeBlockConfig.BLOCKS[BlockType.LUNCH]
    print(f"\n🍱 Testing Lunch Block: {lunch_block.start_time} - {lunch_block.end_time}")
    
    lunch_candidates = PlaceFilter.get_candidate_places(
        all_places=places,
        block=lunch_block,
        day_of_week=0,  # Monday
        min_rating=3.0
    )
    
    print(f"  Found {len(lunch_candidates)} candidates")
    for place in lunch_candidates[:3]:
        print(f"    - {place.name} (rating: {place.rating}, types: {place.types[:2]})")
    
    # Test morning activities
    morning_block = TimeBlockConfig.BLOCKS[BlockType.MORNING]
    print(f"\n🌅 Testing Morning Activities: {morning_block.start_time} - {morning_block.end_time}")
    
    morning_candidates = PlaceFilter.get_candidate_places(
        all_places=places,
        block=morning_block,
        day_of_week=0,  # Monday
        min_rating=3.0
    )
    
    print(f"  Found {len(morning_candidates)} candidates")
    for place in morning_candidates[:3]:
        print(f"    - {place.name} (rating: {place.rating}, types: {place.types[:2]})")
    
    print(f"\n{'=' * 80}\n")


def test_opening_hours_coverage():
    """Test opening hours coverage calculation"""
    print("=" * 80)
    print("TEST 4: Opening Hours Coverage")
    print("=" * 80)
    
    # Create sample opening hours data (restaurant open 6:30 AM - 11:00 PM)
    sample_hours = {
        "periods": [
            {
                "open": {"day": 1, "hour": 6, "minute": 30},   # Monday 6:30 AM
                "close": {"day": 1, "hour": 23, "minute": 0}   # Monday 11:00 PM
            }
        ]
    }
    
    # Test with breakfast (7:00-8:00)
    breakfast_block = TimeBlockConfig.BLOCKS[BlockType.BREAKFAST]
    is_open = PlaceFilter.is_open_during_block(
        sample_hours,
        breakfast_block,
        day_of_week=0,  # Monday
        required_coverage=0.7
    )
    print(f"\n🍳 Breakfast (7:00-8:00): {'✓ OPEN' if is_open else '✗ CLOSED'}")
    
    # Test with lunch (11:00-13:00)
    lunch_block = TimeBlockConfig.BLOCKS[BlockType.LUNCH]
    is_open = PlaceFilter.is_open_during_block(
        sample_hours,
        lunch_block,
        day_of_week=0,  # Monday
        required_coverage=0.7
    )
    print(f"🍱 Lunch (11:00-13:00): {'✓ OPEN' if is_open else '✗ CLOSED'}")
    
    # Test with early morning (1:00-2:00) - should be closed
    early_morning_block = type('Block', (), {
        'start_time': time(1, 0),
        'end_time': time(2, 0),
        'block_type': BlockType.MORNING
    })()
    is_open = PlaceFilter.is_open_during_block(
        sample_hours,
        early_morning_block,
        day_of_week=0,  # Monday
        required_coverage=0.7
    )
    print(f"🌙 Early Morning (1:00-2:00): {'✓ OPEN' if is_open else '✗ CLOSED (expected)'}")
    
    print(f"\n{'=' * 80}\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MONGODB SCHEMA INTEGRATION TEST")
    print("=" * 80 + "\n")
    
    try:
        # Test 1: Load places
        places = test_load_places()
        
        if not places:
            print("❌ No places loaded, cannot continue tests")
            return
        
        # Test 2: Parse opening hours
        test_opening_hours_parsing(places)
        
        # Test 3: Filter by blocks
        test_block_filtering(places)
        
        # Test 4: Opening hours coverage
        test_opening_hours_coverage()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
