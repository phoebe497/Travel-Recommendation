"""Quick test script for full system with real MongoDB data"""

from src.database import MongoDBHandler
from src.models import UserPreference
from src.smart_itinerary_planner import SmartItineraryPlanner
from pathlib import Path
from datetime import datetime
import json

def test_itinerary_generation():
    print("="*80)
    print("QUICK SYSTEM TEST")
    print("="*80)
    
    # Initialize
    db = MongoDBHandler()
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    # Load user preferences
    print("\n1. Loading user preferences...")
    all_prefs = db.get_all_user_preferences_with_places()
    print(f"   Found {len(all_prefs)} valid users")
    
    # Test with Seoul user (should have diverse places)
    print("\n2. Selecting Seoul user...")
    seoul_user = [p for p in all_prefs if p.get("city_name") == "Seoul"][0]
    user_pref = UserPreference.from_mongo(seoul_user, trip_duration_days=2)
    
    print(f"   User: {user_pref.user_id[:16]}...")
    print(f"   City: {user_pref.destination_city}")
    print(f"   Selected places: {len(user_pref.selected_places)}")
    print(f"   Alpha: {user_pref.calculate_alpha():.2f}")
    
    # Generate itinerary
    print("\n3. Generating itinerary...")
    planner = SmartItineraryPlanner(db_handler=db, use_hybrid_scoring=True)
    tour = planner.generate_itinerary(user_pref)
    
    print(f"   Generated: {len(tour.daily_itineraries)} days")
    print(f"   Total places: {tour.get_total_places()}")
    print(f"   Total cost: ${tour.get_total_cost():.2f}")
    
    # Check place diversity
    print("\n4. Checking place diversity...")
    for day_idx, day in enumerate(tour.daily_itineraries, 1):
        places = []
        for block in day.blocks:
            for sp in block.scheduled_places:
                places.append(sp.place.name)
        
        unique = len(set(places))
        total = len(places)
        print(f"   Day {day_idx}: {total} visits, {unique} unique places")
        print(f"      Places: {', '.join(places[:5])}{'...' if len(places) > 5 else ''}")
    
    # Save output
    print("\n5. Saving output...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Seoul_{timestamp}.json"
    filepath = outputs_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(tour.to_dict(), f, indent=2, ensure_ascii=False)
    
    print(f"   Saved: {filepath}")
    
    # Verify output format
    print("\n6. Verifying output format...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check first place in first block
    first_day = data["daily_itineraries"][0]
    first_block = None
    for block in first_day["blocks"]:
        if block["places"]:
            first_block = block
            break
    
    if first_block:
        first_place = first_block["places"][0]
        print(f"   Sample place format:")
        print(f"      Name: {first_place['name']}")
        print(f"      Rating: {first_place['rating']}")
        print(f"      Avg price: ${first_place.get('avg_price_usd', 0):.2f}")
        print(f"      Time: {first_place['arrival_time']} - {first_place['departure_time']}")
        
        # Check summary
        summary = first_day["summary"]
        print(f"\n   Day summary:")
        print(f"      Total places: {summary['total_places']}")
        print(f"      Transport cost: ${summary.get('transport_cost_usd', 0):.2f}")
        print(f"      Total cost: ${summary['total_cost_usd']:.2f}")
    
    print("\n" + "="*80)
    print("✓ TEST COMPLETED SUCCESSFULLY!")
    print("="*80)

if __name__ == "__main__":
    try:
        test_itinerary_generation()
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
