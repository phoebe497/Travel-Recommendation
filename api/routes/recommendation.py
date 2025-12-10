"""
Recommendation Endpoints (without scheduling)
"""
from fastapi import APIRouter, HTTPException, status
from api.schemas.request import GetRecommendationsRequest
from api.schemas.response import RecommendationsResponse, RecommendationItem, ErrorResponse
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/recommendations",
    response_model=RecommendationsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get Place Recommendations",
    description="""
Get personalized place recommendations without scheduling.
Useful for:
- Showing recommendations to users for selection
- Pre-filtering before itinerary generation
- Exploring places in a city
    """
)
async def get_recommendations(request: GetRecommendationsRequest):
    """
    Get Top-K place recommendations for a city
    
    **Example Request:**
    ```json
    {
      "city": "Bangkok",
      "interests": ["temples", "food"],
      "num_recommendations": 20
    }
    ```
    
    **Example Response:**
    ```json
    {
      "city": "Bangkok",
      "total_candidates": 150,
      "recommendations": [
        {
          "place_id": "ChIJ...",
          "name": "Wat Pho",
          "rating": 4.7,
          "score": 0.92,
          "types": ["temple", "tourist_attraction"]
        }
      ],
      "processing_time_ms": 1200
    }
    ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"Getting recommendations for {request.city}, k={request.num_recommendations}")
        
        # Import here
        from src.database import MongoDBHandler
        from src.hybrid_recommender import HybridRecommender
        from src.models import UserPreference, Place
        
        # Initialize
        db = MongoDBHandler()
        recommender = HybridRecommender()
        
        # Load places
        places_collection = db.get_collection("places")
        places_cursor = places_collection.find({"city": request.city}).sort("rating", -1)
        
        places = []
        for doc in places_cursor:
            try:
                place = Place.from_dict(doc)
                places.append(place)
            except Exception as e:
                logger.warning(f"Failed to parse place: {e}")
                continue
        
        if len(places) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No places found for {request.city}"
            )
        
        logger.info(f"Loaded {len(places)} places for {request.city}")
        
        # Create temporary user preference
        user_pref = UserPreference(
            user_id="api_user",
            destination_city=request.city,
            trip_duration_days=3,  # Dummy value
            interests=request.interests,
            selected_places=request.selected_place_ids or []
        )
        
        # Get recommendations
        scored_places = recommender.get_top_recommendations(
            user_pref=user_pref,
            candidate_places=places,
            selected_places=request.selected_place_ids or [],
            k=request.num_recommendations
        )
        
        # Convert to response
        recommendations = []
        for place, score in scored_places:
            recommendations.append(RecommendationItem(
                place_id=place.place_id,
                name=place.name,
                rating=place.rating,
                price_level=place.price_level,
                types=place.types[:3] if hasattr(place, 'types') else [],
                score=round(score, 4),
                avg_price_usd=round(place.avg_price_usd, 2)
            ))
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        response = RecommendationsResponse(
            city=request.city,
            total_candidates=len(places),
            recommendations=recommendations,
            processing_time_ms=processing_time_ms
        )
        
        logger.info(f"Returned {len(recommendations)} recommendations in {processing_time_ms}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )
