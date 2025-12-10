"""
Smart Travel Recommendation System
Main entry point and example usage

This system combines:
1. Content-based filtering (BERT embeddings + user preference vectors)
2. Collaborative filtering (SVD Matrix Factorization)
3. Hybrid scoring (weighted combination)
4. Graph-based routing (Dijkstra shortest path)
5. Time-block based itinerary generation (meals/activities/rest)
6. Opening hours filtering and transport mode selection
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from src.models import UserPreference
from src.smart_itinerary_planner import SmartItineraryPlanner
from src.database import MongoDBHandler
from utils import save_tour_with_timestamp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_example_user_preference(db_handler: MongoDBHandler) -> UserPreference:
    """
    Load user preference from MongoDB
    
    Args:
        db_handler: MongoDB database handler
        
    Returns:
        UserPreference object loaded from database
    """
    import sys
    
    # Load all valid user preferences
    all_prefs = db_handler.get_all_user_preferences_with_places()
    
    if not all_prefs:
        raise ValueError("No valid user preferences found in database")
    
    # Use first user or specific user_id from command line
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
        user_pref_doc = db_handler.get_user_preference(user_id)
        if not user_pref_doc:
            raise ValueError(f"User {user_id} not found")
    else:
        # Use first available user
        user_pref_doc = all_prefs[0]
    
    # Convert to UserPreference object
    user_pref = UserPreference.from_mongo(
        user_pref_doc,
        trip_duration_days=3,
        budget_range="medium",
        travel_party="solo"
    )
    
    logger.info(f"Loaded user {user_pref.user_id[:16]}... for {user_pref.destination_city}")
    
    return user_pref


def generate_tour_example():
    """
    Example: Generate a tour recommendation from MongoDB data
    """
    logger.info("=" * 60)
    logger.info("SMART TRAVEL RECOMMENDATION SYSTEM - EXAMPLE")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        db_handler = MongoDBHandler()
        
        # Step 1: Load user preferences from MongoDB
        logger.info("\n1. Loading user preferences from MongoDB...")
        user_pref = create_example_user_preference(db_handler)
        logger.info(f"   Destination: {user_pref.destination_city}")
        logger.info(f"   Duration: {user_pref.trip_duration_days} days")
        logger.info(f"   Budget: {user_pref.budget_range}")
        logger.info(f"   Interests: {', '.join(user_pref.interests)}")
        
        # Step 2: Initialize itinerary planner
        logger.info("\n2. Initializing smart itinerary planner...")
        # Enable hybrid scoring with BERT+SVD for better recommendations
        planner = SmartItineraryPlanner(use_hybrid_scoring=True)
        
        # Step 3: Train recommender with historical data (if hybrid scoring enabled)
        logger.info("\n3. Preparing recommender system...")
        if planner.use_hybrid_scoring:
            planner.recommender.train_models()
            logger.info("   ✓ BERT+SVD models trained")
        else:
            logger.info("   ✓ Using rating-based scoring")
        
        # Step 4: Generate itinerary
        logger.info("\n4. Generating personalized itinerary...")
        start_date = datetime(2025, 12, 1).date()  # Example start date
        tour = planner.generate_itinerary(user_pref, start_date)
        
        # Step 5: Display results
        logger.info("\n5. Itinerary Generation Complete!")
        logger.info("=" * 60)
        logger.info(f"Destination: {tour.destination}")
        logger.info(f"Duration: {tour.duration_days} days")
        logger.info(f"Total Cost: ${tour.get_total_cost():.2f}")
        logger.info(f"Total Places: {tour.get_total_places()}")
        
        # Display daily itineraries
        logger.info("\nDaily Itineraries:")
        logger.info("-" * 60)
        
        for day in tour.daily_itineraries:
            logger.info(f"\nDay {day.day_number} - {day.date}")
            all_places = day.get_all_scheduled_places()
            logger.info(f"  Places: {len(all_places)}")
            logger.info(f"  Estimated Cost: ${day.get_total_cost():.2f}")
            logger.info(f"  Total Score: {day.get_total_score():.3f}")
            
            # Display by time blocks
            for block_type, scheduled_places in [
                ('breakfast', day.breakfast),
                ('morning', day.morning_activities),
                ('lunch', day.lunch),
                ('afternoon', day.afternoon_activities),
                ('evening', day.evening_activities)
            ]:
                if scheduled_places:
                    logger.info(f"\n  [{block_type.upper()}]")
                    for i, sp in enumerate(scheduled_places, 1):
                        place = sp.place
                        logger.info(f"    {i}. {place.name}")
                        logger.info(f"       Time: {sp.start_time} ({sp.duration_hours:.1f}h)")
                        logger.info(f"       Rating: {place.rating}/5.0")
                        if sp.score:
                            logger.info(f"       Score: {sp.score:.3f}")
                        if sp.transport_to_next:
                            logger.info(f"       → {sp.transport_to_next}: {sp.travel_time_hours*60:.0f} min")
        
        # Step 6: Save tour to database (optional)
        logger.info("\n6. Saving itinerary to database...")
        try:
            tour_dict = tour.to_dict()
            db_id = planner.db.create_tour(tour_dict)
            logger.info(f"   Itinerary saved with ID: {db_id}")
        # Step 7: Export to JSON with timestamp and city name
        logger.info("\n7. Exporting itinerary to JSON...")
        
        # Save to outputs directory with timestamp and city name
        from pathlib import Path
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_city_name = tour.destination.replace(" ", "_").replace("/", "-")
        output_filename = f"{safe_city_name}_{timestamp}.json"
        output_file = outputs_dir / output_filename
        
        tour_json = tour.to_dict()
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tour_json, f, indent=2, ensure_ascii=False)
        
        logger.info(f"   Itinerary exported to: {output_file}")
        output_file = planner.save_itinerary(tour, "outputs/latest_tour.json")
        
        logger.info(f"   Itinerary exported to: {output_file}")
        
        logger.info("\n" + "=" * 60)
        logger.info("EXAMPLE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
        return tour
        
    except Exception as e:
        logger.error(f"Error generating tour: {e}", exc_info=True)
        raise


def custom_tour_generation(
    user_id: str,
    destination: str,
    duration_days: int,
    budget: str,
    interests: list,
    selected_places: list = None
) -> Dict[str, Any]:
    """
    Generate a custom tour with specific parameters
    
    Args:
        user_id: User identifier
        destination: Destination city
        duration_days: Number of days
        budget: Budget range ('low', 'medium', 'high')
        interests: List of interests
        selected_places: Optional list of pre-selected place IDs
        
    Returns:
        Tour dictionary
    """
    logger.info(f"Generating custom tour for user {user_id}")
    
    # Create user preference
    user_pref = UserPreference(
        user_id=user_id,
        destination_city=destination,
        trip_duration_days=duration_days,
        budget_range=budget,
        interests=interests,
        selected_places=selected_places or []
    )
    
    # Generate tour
    planner = SmartItineraryPlanner(use_hybrid_scoring=True)
    if planner.use_hybrid_scoring:
        planner.recommender.train_models()
    
    tour = planner.generate_itinerary(user_pref)
    
    return tour.to_dict()


if __name__ == "__main__":
    # Run example
    tour = generate_tour_example()
    
    # Uncomment to try custom generation
    # custom_tour = custom_tour_generation(
    #     user_id="user_123",
    #     destination="Bangkok",
    #     duration_days=5,
    #     budget="medium",
    #     interests=["temples", "food", "nightlife"],
    #     selected_places=[]
    # )
