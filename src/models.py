"""
Data models for the Smart Travel Recommendation System
Defines the structure of places, tours, and user preferences
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Place:
    """Place/Location model"""
    place_id: str
    name: str
    city: str
    types: List[str]
    rating: float
    latitude: float
    longitude: float
    price_level: int = 0
    avg_price: float = 0.0
    user_rating_count: int = 0
    opening_hours: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Place':
        """Create Place from dictionary (MongoDB format)"""
        # Handle location field which is a dict with latitude/longitude
        location = data.get("location", {})
        
        # Handle displayName which can be dict or string
        display_name = data.get("displayName", {})
        if isinstance(display_name, dict):
            name = display_name.get("text", "")
        else:
            name = str(display_name) if display_name else ""
        
        # Fallback to 'name' field if displayName is empty
        if not name:
            name = data.get("name", "Unknown Place")
        
        # Handle priceLevel which can be string (PRICE_LEVEL_MODERATE) or int
        price_level_raw = data.get("priceLevel", 0)
        if isinstance(price_level_raw, str):
            # Map string values to numeric levels
            price_map = {
                "PRICE_LEVEL_FREE": 0,
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4
            }
            price_level = price_map.get(price_level_raw, 2)  # Default to moderate
        else:
            price_level = int(price_level_raw) if price_level_raw else 0
        
        return cls(
            place_id=data.get("id", ""),
            name=name,
            city=data.get("city", ""),
            types=data.get("types", []),
            rating=float(data.get("rating", 0.0)),
            latitude=float(location.get("latitude", 0.0)),
            longitude=float(location.get("longitude", 0.0)),
            price_level=price_level,
            avg_price=float(data.get("avg_price", 0.0)),
            user_rating_count=int(data.get("userRatingCount", 0)),
            opening_hours=data.get("regularOpeningHours", {})
        )
    
    def get_category(self) -> str:
        """Determine the main category of this place"""
        from .config import config
        
        for place_type in self.types:
            if place_type in config.PLACE_CATEGORIES:
                return config.PLACE_CATEGORIES[place_type]
        
        return "activity"  # Default category


@dataclass
class UserPreference:
    """User preference model"""
    user_id: str
    selected_places: List[str] = field(default_factory=list)  # Liked places (combined from all categories)
    disliked_places: List[str] = field(default_factory=list)  # Disliked places (to exclude from recommendations)
    destination_city: str = ""
    trip_duration_days: int = 3
    budget_range: str = "medium"
    interests: List[str] = field(default_factory=list)
    travel_party: str = "solo"
    accommodation_type: str = "hotel"
    dietary_restrictions: List[str] = field(default_factory=list)
    accessibility_needs: List[str] = field(default_factory=list)
    
    # Private field to cache loaded Place objects for alpha calculation
    # This is set by TourGenerator after loading places from database
    _selected_place_objects: Optional[List['Place']] = field(default=None, repr=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreference':
        """Create UserPreference from dictionary (API format)"""
        return cls(
            user_id=data.get("user_id", ""),
            selected_places=data.get("selected_places", []),
            disliked_places=data.get("disliked_places", []),
            destination_city=data.get("destination_city", ""),
            trip_duration_days=data.get("trip_duration_days", 3),
            budget_range=data.get("budget_range", "medium"),
            interests=data.get("interests", []),
            travel_party=data.get("travel_party", "solo"),
            accommodation_type=data.get("accommodation_type", "hotel"),
            dietary_restrictions=data.get("dietary_restrictions", []),
            accessibility_needs=data.get("accessibility_needs", [])
        )
    
    @classmethod
    def from_mongo(cls, data: Dict[str, Any], trip_duration_days: int = 3, 
                   budget_range: str = "medium", travel_party: str = "solo") -> 'UserPreference':
        """
        Create UserPreference from MongoDB user_preferences collection format
        
        Args:
            data: Document from user_preferences collection with structure:
                  {"user_id": "...", "city_name": "...", 
                   "liked_restaurants": [...], "liked_hotels": [...], "liked_activities": [...],
                   "disliked_restaurants": [...], "disliked_hotels": [...], "disliked_activities": [...]}
            trip_duration_days: Number of days for the trip (default: 3)
            budget_range: Budget range (default: "medium")
            travel_party: Travel party type (default: "solo")
            
        Returns:
            UserPreference object
        """
        # Combine all liked places from different categories
        liked_restaurants = data.get("liked_restaurants", [])
        liked_hotels = data.get("liked_hotels", [])
        liked_activities = data.get("liked_activities", [])
        selected_places = liked_restaurants + liked_hotels + liked_activities
        
        # Combine all disliked places
        disliked_restaurants = data.get("disliked_restaurants", [])
        disliked_hotels = data.get("disliked_hotels", [])
        disliked_activities = data.get("disliked_activities", [])
        disliked_places = disliked_restaurants + disliked_hotels + disliked_activities
        
        # Infer interests from liked place types
        interests = []
        if liked_restaurants:
            interests.append("food")
        if liked_hotels:
            interests.append("accommodation")
        if liked_activities:
            interests.extend(["landmarks", "culture"])
        
        return cls(
            user_id=data.get("user_id", ""),
            selected_places=selected_places,
            disliked_places=disliked_places,
            destination_city=data.get("city_name", ""),
            trip_duration_days=trip_duration_days,
            budget_range=budget_range,
            interests=list(set(interests)),  # Remove duplicates
            travel_party=travel_party,
            accommodation_type="hotel",
            dietary_restrictions=[],
            accessibility_needs=[]
        )
    
    def set_selected_places_data(self, places: List['Place']) -> None:
        """
        Cache loaded Place objects for diversity-aware alpha calculation.
        Should be called by TourGenerator after loading selected places from database.
        
        Args:
            places: List of Place objects that user has selected
        """
        self._selected_place_objects = places
    
    def calculate_alpha(self, total_available_places: int = 30) -> float:
        """
        Calculate alpha for hybrid recommendation based on selection rate and trip intensity.
        
        Alpha = weight between content-based (personal preference) and collaborative filtering (popular places).
        Formula: hybrid_score = α × content_score + (1-α) × collaborative_score
        
        Method: Two-tier linear scaling based on selection_rate with engagement bonus.
        - Tier 1 (rate < 50%): α ∈ [0.3, 0.6] - User selects little, trust collaborative more
        - Tier 2 (rate ≥ 50%): α ∈ [0.6, 0.9] - User selects a lot, trust content more
        - Bonus: +0.05 if places_per_day ≥ 5 (high engagement)
        
        Args:
            total_available_places: Clipped pool size that user can see/interact with.
                                   Use max(30, min(200, len(candidate_places)))
                                   NOT the full DB size. See docs/ALPHA_CALCULATION.md
        
        Returns:
            Alpha value ∈ [0.3, 0.9]
        See docs/ALPHA_CALCULATION.md for detailed explanation and examples.
        """
        num_selected = len(self.selected_places)
        
        # Cold start: chưa chọn gì → dựa vào content-based (BERT)
        if num_selected == 0:
            return 0.9  # User mới, không có lịch sử → dùng semantic similarity
        
        # Tính selection rate (tỷ lệ chọn)
        selection_rate = num_selected / total_available_places  # 0.0 → 1.0
        
        # Tính places per day (mật độ)
        num_days = self.trip_duration_days
        places_per_day = num_selected / num_days if num_days > 0 else num_selected
        
        # ══════════════════════════════════════════════════════════════════
        # KHOẢNG 1: selection_rate < 0.5 (chọn < 15/30 places)
        # ══════════════════════════════════════════════════════════════════
        if selection_rate < 0.5:
            # User chọn ít → chưa rõ sở thích → dựa collaborative nhiều
            # Alpha range: 0.3 → 0.6
            # Formula: α = 0.3 + 0.3 × (rate / 0.5)
            # • rate=0.0 → α=0.3 (min)
            # • rate=0.25 → α=0.45
            # • rate=0.5 → α=0.6
            alpha = 0.3 + 0.3 * (selection_rate / 0.5)
        
        # ══════════════════════════════════════════════════════════════════
        # KHOẢNG 2: selection_rate ≥ 0.5 (chọn ≥ 15/30 places)
        # ══════════════════════════════════════════════════════════════════
        else:
            # User chọn nhiều → rõ sở thích → dựa content nhiều
            # Alpha range: 0.6 → 0.9
            # Formula: α = 0.6 + 0.3 × ((rate - 0.5) / 0.5)
            # • rate=0.5 → α=0.6
            # • rate=0.75 → α=0.75
            # • rate=1.0 → α=0.9 (max)
            alpha = 0.6 + 0.3 * ((selection_rate - 0.5) / 0.5)
            
            # Bonus: Nếu places_per_day cao → tăng alpha thêm
            # Lý do: Nhiều places/ngày → user rất chủ động → tin content hơn
            if places_per_day >= 5:
                alpha = min(0.9, alpha + 0.05)  # +5% bonus, max 0.9
        
        # Giới hạn [0.3, 0.9]
        alpha = max(0.3, min(0.9, alpha))
        
        return round(alpha, 2)


@dataclass
class TimeBlock:
    """Time block for scheduling"""
    name: str
    start_time: str
    end_time: str
    block_type: str  # 'activity', 'meal', 'rest'
    duration_hours: float
    
    def __str__(self) -> str:
        return f"{self.name} ({self.start_time}-{self.end_time})"


@dataclass
class ScheduledPlace:
    """Place with scheduling information"""
    place: Place
    start_time: str
    duration_hours: float
    time_block: str
    transport_to_next: Optional[str] = None
    distance_to_next_km: Optional[float] = None
    travel_time_hours: Optional[float] = None
    score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        result = {
            "place_id": self.place.place_id,
            "name": self.place.name,
            "start_time": self.start_time,
            "duration_hours": round(self.duration_hours, 2),
            "time_block": self.time_block,
            "types": self.place.types,
            "rating": self.place.rating,
            "score": round(self.score, 3)
        }
        
        if self.transport_to_next:
            result["transport_to_next"] = self.transport_to_next
            result["distance_to_next_km"] = round(self.distance_to_next_km, 2)
            result["travel_time_hours"] = round(self.travel_time_hours, 2)
        
        return result


@dataclass
class DayItinerary:
    """Itinerary for a single day"""
    day_number: int
    date: str
    places: List[ScheduledPlace] = field(default_factory=list)
    total_distance_km: float = 0.0
    estimated_cost: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return {
            "day_number": self.day_number,
            "date": self.date,
            "places": [p.to_dict() for p in self.places],
            "total_distance_km": round(self.total_distance_km, 2),
            "estimated_cost": round(self.estimated_cost, 2)
        }


@dataclass
class TourRecommendation:
    """Complete tour recommendation"""
    tour_id: str
    destination: str
    duration_days: int
    user_preference: UserPreference
    itinerary: List[DayItinerary] = field(default_factory=list)
    total_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return {
            "tour_id": self.tour_id,
            "destination": self.destination,
            "duration_days": self.duration_days,
            "user_preferences": {
                "destination_city": self.user_preference.destination_city,
                "trip_duration_days": self.user_preference.trip_duration_days,
                "budget_range": self.user_preference.budget_range,
                "interests": self.user_preference.interests,
                "travel_party": self.user_preference.travel_party
            },
            "itinerary": [day.to_dict() for day in self.itinerary],
            "total_cost_usd": round(self.total_cost, 2),
            "created_at": self.created_at.isoformat()
        }
