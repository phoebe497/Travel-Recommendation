"""
Pydantic Request Models for API
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import date, datetime
from src.models import UserPreference


class GenerateItineraryRequest(BaseModel):
    """Request model for generating travel itinerary"""
    
    # Required fields
    city: str = Field(
        ...,
        description="Destination city name",
        example="Ho Chi Minh City",
        min_length=2
    )
    num_days: int = Field(
        ...,
        description="Number of days for the trip",
        ge=1,
        le=14,
        example=3
    )
    start_date: date = Field(
        ...,
        description="Start date of the trip (YYYY-MM-DD)",
        example="2025-12-20"
    )
    
    # User preferences
    interests: List[str] = Field(
        default=["culture", "food"],
        description="List of user interests",
        example=["culture", "food", "nature", "shopping"]
    )
    budget: str = Field(
        default="medium",
        description="Budget range: low, medium, high",
        example="medium"
    )
    travel_party: str = Field(
        default="solo",
        description="Travel party type: solo, couple, family, friends",
        example="solo"
    )
    accommodation_type: str = Field(
        default="hotel",
        description="Accommodation type: hotel, hostel, resort",
        example="hotel"
    )
    
    # Optional overrides
    selected_place_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional: Pre-selected place IDs to include",
        example=None
    )
    hotel_place_id: Optional[str] = Field(
        default=None,
        description="Optional: Specific hotel place ID",
        example=None
    )
    
    @validator('budget')
    def validate_budget(cls, v):
        valid_budgets = ['low', 'medium', 'high']
        if v not in valid_budgets:
            raise ValueError(f'Budget must be one of: {valid_budgets}')
        return v
    
    @validator('travel_party')
    def validate_travel_party(cls, v):
        valid_parties = ['solo', 'couple', 'family', 'friends']
        if v not in valid_parties:
            raise ValueError(f'Travel party must be one of: {valid_parties}')
        return v
    
    @validator('start_date')
    def validate_start_date(cls, v):
        if v < date.today():
            raise ValueError('Start date cannot be in the past')
        return v
    
    def to_user_preference(self) -> UserPreference:
        """Convert request to UserPreference model"""
        return UserPreference(
            user_id="api_user",
            destination_city=self.city,
            trip_duration_days=self.num_days,
            interests=self.interests,
            budget_range=self.budget,
            travel_party=self.travel_party,
            accommodation_type=self.accommodation_type,
            selected_places=self.selected_place_ids or []
        )
    
    class Config:
        schema_extra = {
            "example": {
                "city": "Singapore",
                "num_days": 3,
                "start_date": "2025-12-20",
                "interests": ["landmarks", "food", "shopping"],
                "budget": "medium",
                "travel_party": "couple",
                "accommodation_type": "hotel",
                "selected_place_ids": None,
                "hotel_place_id": None
            }
        }


class GetRecommendationsRequest(BaseModel):
    """Request model for getting place recommendations only (without scheduling)"""
    
    city: str = Field(..., description="Destination city", example="Bangkok")
    interests: List[str] = Field(
        default=["culture"],
        description="User interests",
        example=["temples", "food", "markets"]
    )
    num_recommendations: int = Field(
        default=20,
        description="Number of recommendations to return",
        ge=5,
        le=50,
        example=20
    )
    selected_place_ids: Optional[List[str]] = Field(
        default=None,
        description="Pre-selected places",
        example=None
    )
    
    class Config:
        schema_extra = {
            "example": {
                "city": "Bangkok",
                "interests": ["temples", "food"],
                "num_recommendations": 20,
                "selected_place_ids": None
            }
        }
