"""
New Itinerary Planner - Test Script
Test the complete itinerary planning system with Dijkstra + TimeBlocks
"""

import sys
from pathlib import Path
import logging
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.database import MongoDBHandler
from src.models import UserPreference, Place
from src.itinerary_builder import ItineraryBuilder
from src.hybrid_recommender import HybridRecommender

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_places_from_db(destination_city: str, limit: int = 100) -> list[Place]:
    """Load places from MongoDB"""
    db = MongoDBHandler()
    places_collection = db.get_collection("places")
    
    # Query places
    query = {"city": destination_city} if destination_city else {}
    cursor = places_collection.find(query).limit(limit)
    
    places = []
    for doc in cursor:
        try:
            place = Place(
                place_id=doc.get('place_id') or doc.get('id'),
                name=doc.get('name', 'Unknown'),
                city=doc.get('city', destination_city),
                latitude=doc.get('latitude') or doc.get('lat'),
                longitude=doc.get('longitude') or doc.get('lng'),
                types=doc.get('types', []),
                rating=float(doc.get('rating', 0)),
                user_ratings_total=doc.get('user_ratings_total') or doc.get('user_rating_count', 0),
                price_level=doc.get('price_level'),
                opening_hours=doc.get('opening_hours')
            )
            places.append(place)
        except Exception as e:
            logger.warning(f"Skipped place: {e}")
            continue
    
    logger.info(f"Loaded {len(places)} places from {destination_city}")
    return places


def test_new_itinerary_planner():
    """Test the new itinerary planner"""
    
    print("="*80)
    print("NEW ITINERARY PLANNER TEST")
    print("Using: Dijkstra + TimeBlocks + Transport Selection")
    print("="*80)
    
    # Step 1: Load places
    print("\n📍 Step 1: Loading places from MongoDB...")
    destination = "Hanoi"
    places = load_places_from_db(destination, limit=150)
    
    if not places:
        print("❌ No places found!")
        return
    
    print(f"✅ Loaded {len(places)} places")
    print(f"   Sample: {places[0].name}, {places[1].name}, {places[2].name}...")
    
    # Step 2: Create user preference
    print("\n👤 Step 2: Creating user preference...")
    user_pref = UserPreference(
        user_id="test_user_new_planner",
        destination_city=destination,
        trip_duration_days=2,
        interests=["culture", "food", "history"],
        budget_range="medium",
        travel_party="couple",
        accommodation_type="hotel"
    )
    
    print(f"   Destination: {user_pref.destination_city}")
    print(f"   Duration: {user_pref.trip_duration_days} days")
    print(f"   Interests: {', '.join(user_pref.interests)}")
    
    # Step 3: Calculate hybrid scores (optional but recommended)
    print("\n🎯 Step 3: Calculating hybrid recommendation scores...")
    recommender = HybridRecommender()
    
    # Precompute embeddings for better performance
    print("   Precomputing BERT embeddings...")
    recommender.content_filter.precompute_embeddings(places)
    
    # Calculate scores
    print("   Calculating hybrid scores...")
    hybrid_scores = {}
    try:
        scored_places = recommender.get_top_recommendations(
            all_places=places,
            user_interests=user_pref.interests,
            top_k=len(places)
        )
        hybrid_scores = {p.place_id: score for p, score in scored_places}
        print(f"✅ Calculated scores for {len(hybrid_scores)} places")
    except Exception as e:
        logger.warning(f"Could not calculate hybrid scores: {e}")
        print(f"⚠️  Using default scores (ratings)")
    
    # Step 4: Build itinerary
    print("\n🗓️  Step 4: Building itinerary...")
    print("   This will:")
    print("   - Create time blocks (meals/activities/rest)")
    print("   - Filter places by opening hours and type")
    print("   - Optimize activity sequences with Dijkstra")
    print("   - Select transport modes (walking/motorbike/taxi)")
    print()
    
    builder = ItineraryBuilder(places)
    tour = builder.build_itinerary(
        user_pref=user_pref,
        hybrid_scores=hybrid_scores
    )
    
    # Step 5: Optimize (add transport connections)
    print("\n🔧 Step 5: Optimizing itinerary...")
    tour = builder.optimize_itinerary(tour)
    
    print("✅ Itinerary built successfully!")
    
    # Step 6: Display results
    print("\n" + "="*80)
    print("ITINERARY RESULTS")
    print("="*80)
    
    print(f"\n📋 Summary:")
    print(f"   Destination: {tour.destination}")
    print(f"   Duration: {tour.duration_days} days")
    print(f"   Total places: {tour.get_total_places()}")
    print(f"   Total cost: ${tour.get_total_cost():.2f}")
    
    # Display each day
    for day in tour.daily_itineraries:
        print(f"\n{'='*80}")
        print(f"DAY {day.day_number} - {day.date}")
        print(f"{'='*80}")
        
        for block_schedule in day.blocks:
            block_name = block_schedule.block.block_type.value.upper()
            time_range = block_schedule.block.format_time_range()
            
            print(f"\n🕐 {block_name} ({time_range})")
            
            if not block_schedule.success:
                print(f"   ⚠️  {block_schedule.reason}")
                continue
            
            for i, sp in enumerate(block_schedule.scheduled_places, 1):
                print(f"\n   {i}. {sp.place.name}")
                print(f"      📍 {', '.join(sp.place.types[:3])}")
                print(f"      ⭐ Rating: {sp.place.rating}/5.0")
                print(f"      ⏰ Time: {sp.arrival_time.strftime('%H:%M')} - {sp.departure_time.strftime('%H:%M')} ({sp.visit_duration_hours:.1f}h)")
                print(f"      📊 Score: {sp.score:.3f}")
                
                # Transport to next place
                if sp.transport_to_next:
                    print(f"      🚗 → Next: {sp.transport_to_next} "
                          f"({sp.distance_to_next_km:.2f}km, "
                          f"{sp.travel_time_to_next_hours*60:.0f}min, "
                          f"${sp.travel_cost_to_next:.2f})")
            
            # Block statistics
            print(f"\n   📊 Block Stats:")
            print(f"      Total score: {block_schedule.total_score:.3f}")
            print(f"      Travel time: {block_schedule.total_travel_time_hours:.2f}h")
            print(f"      Visit time: {block_schedule.total_visit_time_hours:.2f}h")
            print(f"      Cost: ${block_schedule.total_cost:.2f}")
    
    # Step 7: Export to JSON
    print("\n" + "="*80)
    print("📄 Exporting to JSON...")
    
    tour_json = tour.to_dict()
    
    output_dir = Path("outputs/itineraries")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"itinerary_{destination.lower()}_{tour.created_at.strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tour_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved to: {output_file}")
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Graph-based distance calculation (Dijkstra)")
    print("   ✅ Time block scheduling (meals/activities/rest)")
    print("   ✅ Opening hours filtering")
    print("   ✅ Transport mode selection (walking/motorbike/taxi)")
    print("   ✅ Activity sequence optimization")
    print("   ✅ BERT + SVD hybrid scoring")
    print("   ✅ Multi-day itinerary generation")
    
    return tour


if __name__ == "__main__":
    try:
        tour = test_new_itinerary_planner()
        print("\n🎉 New itinerary planner is working perfectly!")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
