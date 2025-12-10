"""
Pydantic Response Models for API
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date


class TransportInfo(BaseModel):
    """Transport information between places"""
    mode: str = Field(..., description="Transport mode: walking, motorbike, taxi")
    distance_km: float = Field(..., description="Distance in kilometers")
    duration_minutes: float = Field(..., description="Travel time in minutes")
    cost_usd: float = Field(..., description="Estimated cost in USD")


class PlaceDetail(BaseModel):
    """Detailed place information in itinerary"""
    place_id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Place name")
    rating: float = Field(..., description="Average rating (0-5)")
    price_level: Optional[int] = Field(None, description="Price level (1-4)")
    types: List[str] = Field(default=[], description="Place categories")
    
    # Time information
    arrival_time: str = Field(..., description="Arrival time (HH:MM)", example="09:00")
    departure_time: str = Field(..., description="Departure time (HH:MM)", example="11:30")
    visit_duration_hours: float = Field(..., description="Visit duration in hours")
    
    # Cost
    estimated_cost_usd: float = Field(..., description="Estimated visit cost in USD")
    
    # Transport to next place
    transport_to_next: Optional[TransportInfo] = Field(
        None,
        description="Transport info to next place"
    )


class DayItinerary(BaseModel):
    """Single day itinerary"""
    day: int = Field(..., description="Day number (1-indexed)", example=1)
    date: str = Field(..., description="Date (YYYY-MM-DD)", example="2025-12-20")
    
    # Places scheduled for this day
    places: List[PlaceDetail] = Field(..., description="List of places to visit")
    
    # Summary statistics
    total_places: int = Field(..., description="Number of places")
    total_cost_usd: float = Field(..., description="Total cost for the day")
    total_distance_km: float = Field(..., description="Total distance traveled")
    total_duration_hours: float = Field(..., description="Total duration including visits and travel")


class ItineraryResponse(BaseModel):
    """Complete itinerary response"""
    
    # Trip information
    destination: str = Field(..., description="Destination city")
    start_date: str = Field(..., description="Trip start date")
    duration_days: int = Field(..., description="Number of days")
    
    # Daily itineraries
    daily_itineraries: List[DayItinerary] = Field(..., description="Day-by-day schedule")
    
    # Summary
    total_places: int = Field(..., description="Total places in itinerary")
    total_cost_usd: float = Field(..., description="Total estimated cost")
    total_distance_km: float = Field(..., description="Total distance")
    
    # Performance
    processing_time_ms: int = Field(..., description="API processing time in milliseconds")
    
    # Metadata
    generated_at: str = Field(..., description="Timestamp when generated")
    
    @classmethod
    def from_tour_itinerary(cls, tour, start_date: date, processing_time_ms: int):
        """Convert TourItinerary object to API response"""
        from datetime import datetime
        
        daily_itineraries = []
        for day in tour.daily_itineraries:
            places = []
            for scheduled_place in day.get_all_scheduled_places():
                place = scheduled_place.place
                
                # Build place detail
                place_detail = PlaceDetail(
                    place_id=place.place_id,
                    name=place.name,
                    rating=place.rating,
                    price_level=place.price_level,
                    types=place.types[:3] if hasattr(place, 'types') else [],
                    arrival_time=scheduled_place.arrival_time.strftime("%H:%M"),
                    departure_time=scheduled_place.departure_time.strftime("%H:%M"),
                    visit_duration_hours=scheduled_place.visit_duration_hours,
                    estimated_cost_usd=round(place.avg_price_usd, 2),
                    transport_to_next=TransportInfo(
                        mode=scheduled_place.transport_mode,
                        distance_km=round(scheduled_place.distance_to_next, 2),
                        duration_minutes=round(scheduled_place.travel_time_to_next * 60, 1),
                        cost_usd=round(scheduled_place.transport_cost, 2)
                    ) if scheduled_place.distance_to_next > 0 else None
                )
                places.append(place_detail)
            
            # Calculate day date
            day_date = start_date
            if hasattr(day, 'date') and day.date:
                day_date = day.date
            else:
                from datetime import timedelta
                day_date = start_date + timedelta(days=day.day_number - 1)
            
            daily_itineraries.append(DayItinerary(
                day=day.day_number,
                date=str(day_date),
                places=places,
                total_places=len(places),
                total_cost_usd=round(day.get_total_cost(), 2),
                total_distance_km=round(day.get_total_distance(), 2),
                total_duration_hours=round(day.get_total_duration(), 2)
            ))
        
        return cls(
            destination=tour.destination,
            start_date=str(start_date),
            duration_days=tour.duration_days,
            daily_itineraries=daily_itineraries,
            total_places=tour.get_total_places(),
            total_cost_usd=round(tour.get_total_cost(), 2),
            total_distance_km=round(tour.get_total_distance(), 2),
            processing_time_ms=processing_time_ms,
            generated_at=datetime.now().isoformat()
        )


class RecommendationItem(BaseModel):
    """Single recommended place"""
    place_id: str
    name: str
    rating: float
    price_level: Optional[int]
    types: List[str]
    score: float = Field(..., description="Recommendation score (0-1)")
    avg_price_usd: float


class RecommendationsResponse(BaseModel):
    """List of recommended places"""
    city: str
    total_candidates: int = Field(..., description="Total places considered")
    recommendations: List[RecommendationItem]
    processing_time_ms: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
