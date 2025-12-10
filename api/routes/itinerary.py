"""
Itinerary Generation Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from api.schemas.request import GenerateItineraryRequest
from api.schemas.response import ItineraryResponse, ErrorResponse
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/generate-itinerary",
    response_model=ItineraryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        404: {"model": ErrorResponse, "description": "City not found or no places available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Generate Travel Itinerary",
    description="""
Generate a complete personalized travel itinerary with scheduled places, transport, and costs.

**Process:**
1. Load places from database for specified city
2. Generate recommendations using Hybrid algorithm (BERT + SVD)
3. Schedule places into daily itinerary (7 time slots per day)
4. Optimize routes using Dijkstra + Transport selection
5. Return complete itinerary with timing and costs

**Response Time:**
- Cold run (first time): ~40-50 seconds
- Warm run (cached): ~5-10 seconds
    """
)
async def generate_itinerary(request: GenerateItineraryRequest):
    """
    Generate a personalized travel itinerary
    
    **Example Request:**
    ```json
    {
      "city": "Singapore",
      "num_days": 3,
      "start_date": "2025-12-20",
      "interests": ["landmarks", "food"],
      "budget": "medium",
      "travel_party": "couple"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "destination": "Singapore",
      "duration_days": 3,
      "daily_itineraries": [
        {
          "day": 1,
          "date": "2025-12-20",
          "places": [
            {
              "name": "Marina Bay Sands",
              "arrival_time": "09:00",
              "departure_time": "11:30",
              "estimated_cost_usd": 50.0
            }
          ],
          "total_cost_usd": 250.0
        }
      ],
      "total_cost_usd": 750.0,
      "processing_time_ms": 5200
    }
    ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"Generating itinerary for {request.city}, {request.num_days} days")
        
        # Import here to avoid slow startup
        from src.database import MongoDBHandler
        from src.smart_itinerary_planner import SmartItineraryPlanner
        
        # Initialize
        db = MongoDBHandler()
        planner = SmartItineraryPlanner(db)
        
        # Convert request to UserPreference
        user_pref = request.to_user_preference()
        
        # Generate itinerary
        tour = planner.generate_itinerary(
            user_pref=user_pref,
            start_date=request.start_date,
            num_days=request.num_days
        )
        
        if not tour or tour.get_total_places() == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No places found for {request.city}. Please check city name or try another destination."
            )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Convert to response
        response = ItineraryResponse.from_tour_itinerary(
            tour=tour,
            start_date=request.start_date,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(
            f"Itinerary generated successfully: {response.total_places} places, "
            f"${response.total_cost_usd:.2f}, {processing_time_ms}ms"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate itinerary: {str(e)}"
        )
