"""
Configuration module for Smart Travel Recommendation System
Handles environment variables and system-wide settings
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from datetime import time, datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration class for the recommendation system"""
    
    # MongoDB Settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "smart_travel")
    
    # API Settings
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
    RAPIDAPI_HOST: str = os.getenv("RAPIDAPI_HOST", "real-time-distance-calculator-with-map.p.rapidapi.com")
    
    # Google Maps API (Optional fallback)
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    
    # Use real distance API (RapidAPI or Haversine)
    USE_REAL_DISTANCE: bool = os.getenv("USE_REAL_DISTANCE", "true").lower() == "true"
    
    # Algorithm Parameters (used by new system)
    DEFAULT_ALPHA: float = float(os.getenv("DEFAULT_ALPHA", "0.7"))
    DEFAULT_BETA: float = float(os.getenv("DEFAULT_BETA", "0.5"))
    TOP_K_PLACES: int = int(os.getenv("TOP_K_PLACES", "50"))


# ============================================================================
# NEW ITINERARY PLANNER CONFIGURATION
# Moved from timeblock_config.py for centralized configuration management
# ============================================================================


class BlockType(Enum):
    """Types of time blocks"""
    # Meals
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    
    # Activities
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    
    # Rest
    HOTEL = "hotel"


class PlaceCategory(Enum):
    """Categories of places for filtering"""
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    HOTEL = "hotel"
    ACTIVITY = "activity"


@dataclass
class TimeBlock:
    """Represents a time block in the itinerary"""
    block_type: BlockType
    start_time: time
    end_time: time
    num_places: int  # Expected number of places in this block
    place_categories: List[PlaceCategory]  # Allowed place categories
    buffer_minutes: int = 15  # Safety buffer
    
    def get_duration_hours(self) -> float:
        """Get block duration in hours"""
        start_dt = datetime.combine(datetime.today(), self.start_time)
        end_dt = datetime.combine(datetime.today(), self.end_time)
        
        # Handle overnight blocks
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        duration = (end_dt - start_dt).total_seconds() / 3600
        return duration
    
    def get_available_hours(self) -> float:
        """Get available hours minus buffer"""
        return self.get_duration_hours() - (self.buffer_minutes / 60)
    
    def is_time_in_block(self, check_time: time) -> bool:
        """Check if a time falls within this block"""
        if self.start_time <= self.end_time:
            # Normal block (same day)
            return self.start_time <= check_time <= self.end_time
        else:
            # Overnight block
            return check_time >= self.start_time or check_time <= self.end_time
    
    def format_time_range(self) -> str:
        """Format block time range as string"""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class TimeBlockConfig:
    """
    Configuration for all time blocks in a day
    Based on user requirements
    """
    
    # Time block definitions
    BLOCKS = {
        # Meals - fixed blocks
        BlockType.BREAKFAST: TimeBlock(
            block_type=BlockType.BREAKFAST,
            start_time=time(7, 0),
            end_time=time(8, 0),
            num_places=1,
            place_categories=[PlaceCategory.CAFE],  # Light breakfast
            buffer_minutes=10
        ),
        BlockType.LUNCH: TimeBlock(
            block_type=BlockType.LUNCH,
            start_time=time(11, 0),
            end_time=time(13, 0),
            num_places=1,
            place_categories=[PlaceCategory.RESTAURANT],  # Must be restaurant
            buffer_minutes=15
        ),
        BlockType.DINNER: TimeBlock(
            block_type=BlockType.DINNER,
            start_time=time(18, 30),
            end_time=time(20, 30),
            num_places=1,
            place_categories=[PlaceCategory.RESTAURANT],  # Must be restaurant
            buffer_minutes=15
        ),
        
        # Activities - variable blocks
        BlockType.MORNING: TimeBlock(
            block_type=BlockType.MORNING,
            start_time=time(8, 0),
            end_time=time(11, 0),
            num_places=2,  # 2 activities
            place_categories=[PlaceCategory.ACTIVITY],
            buffer_minutes=20
        ),
        BlockType.AFTERNOON: TimeBlock(
            block_type=BlockType.AFTERNOON,
            start_time=time(13, 0),
            end_time=time(18, 30),
            num_places=3,  # 3 activities (5.5 hours available)
            place_categories=[PlaceCategory.ACTIVITY],
            buffer_minutes=30
        ),
        BlockType.EVENING: TimeBlock(
            block_type=BlockType.EVENING,
            start_time=time(20, 30),
            end_time=time(22, 0),
            num_places=1,  
            place_categories=[PlaceCategory.ACTIVITY, PlaceCategory.CAFE],
            buffer_minutes=10
        ),
        
        # Rest - fixed block
        BlockType.HOTEL: TimeBlock(
            block_type=BlockType.HOTEL,
            start_time=time(22, 0),
            end_time=time(7, 0),  # Next day 7:00
            num_places=1,
            place_categories=[PlaceCategory.HOTEL],
            buffer_minutes=0
        ),
    }
    
    # Daily schedule order
    DAILY_SCHEDULE = [
        BlockType.BREAKFAST,
        BlockType.MORNING,
        BlockType.LUNCH,
        BlockType.AFTERNOON,
        BlockType.DINNER,
        BlockType.EVENING,
        BlockType.HOTEL
    ]
    
    # Place type mappings
    PLACE_TYPE_MAPPING = {
        PlaceCategory.RESTAURANT: [
            'restaurant', 'meal_delivery', 'meal_takeaway',
            'vietnamese_restaurant', 'asian_restaurant', 'thai_restaurant',
            'chinese_restaurant', 'indian_restaurant', 'japanese_restaurant',
            'korean_restaurant', 'italian_restaurant', 'french_restaurant'
        ],
        PlaceCategory.CAFE: [
            'cafe', 'bakery', 'coffee_shop', 'breakfast_restaurant',
            'food'  # For breakfast foods
        ],
        PlaceCategory.HOTEL: [
            'lodging', 'hotel', 'hostel', 'guest_house', 'inn'
        ],
        PlaceCategory.ACTIVITY: [
            'tourist_attraction', 'museum',
            'park', 'zoo', 'aquarium', 'art_gallery', 'amusement_park',
            'shopping_mall', 'night_club', 'bar', 'pub', 'spa', 'gym',
            'movie_theater', 'library', 'church', 'place_of_worship',
            'historical_landmark', 'cultural_center', 'monument',
            'garden', 'beach', 'viewpoint', 'temple', 'shrine'
        ]
    }
    
    @classmethod
    def get_block(cls, block_type: BlockType) -> TimeBlock:
        """Get time block configuration"""
        return cls.BLOCKS[block_type]
    
    @classmethod
    def get_daily_schedule(cls) -> List[TimeBlock]:
        """Get all blocks in daily order"""
        return [cls.BLOCKS[bt] for bt in cls.DAILY_SCHEDULE]
    
    @classmethod
    def get_place_types_for_category(cls, category: PlaceCategory) -> List[str]:
        """Get place types for a category"""
        return cls.PLACE_TYPE_MAPPING.get(category, [])
    
    @classmethod
    def get_place_types_for_block(cls, block_type: BlockType) -> List[str]:
        """Get all allowed place types for a block"""
        block = cls.BLOCKS[block_type]
        all_types = []
        for category in block.place_categories:
            all_types.extend(cls.get_place_types_for_category(category))
        return list(set(all_types))  # Remove duplicates
    
    @classmethod
    def is_meal_block(cls, block_type: BlockType) -> bool:
        """Check if block is a meal"""
        return block_type in [BlockType.BREAKFAST, BlockType.LUNCH, BlockType.DINNER]
    
    @classmethod
    def is_activity_block(cls, block_type: BlockType) -> bool:
        """Check if block is an activity"""
        return block_type in [BlockType.MORNING, BlockType.AFTERNOON, BlockType.EVENING]
    
    @classmethod
    def is_rest_block(cls, block_type: BlockType) -> bool:
        """Check if block is rest"""
        return block_type == BlockType.HOTEL
    
    @classmethod
    def to_json(cls) -> dict:
        """Export configuration to JSON format"""
        return {
            "timeblocks": {
                "meals": {
                    "breakfast": {
                        "start": cls.BLOCKS[BlockType.BREAKFAST].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.BREAKFAST].end_time.strftime("%H:%M")
                    },
                    "lunch": {
                        "start": cls.BLOCKS[BlockType.LUNCH].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.LUNCH].end_time.strftime("%H:%M")
                    },
                    "dinner": {
                        "start": cls.BLOCKS[BlockType.DINNER].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.DINNER].end_time.strftime("%H:%M")
                    }
                },
                "activities": {
                    "morning": {
                        "start": cls.BLOCKS[BlockType.MORNING].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.MORNING].end_time.strftime("%H:%M")
                    },
                    "afternoon": {
                        "start": cls.BLOCKS[BlockType.AFTERNOON].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.AFTERNOON].end_time.strftime("%H:%M")
                    },
                    "evening": {
                        "start": cls.BLOCKS[BlockType.EVENING].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.EVENING].end_time.strftime("%H:%M")
                    }
                },
                "rest": {
                    "hotel": {
                        "start": cls.BLOCKS[BlockType.HOTEL].start_time.strftime("%H:%M"),
                        "end": cls.BLOCKS[BlockType.HOTEL].end_time.strftime("%H:%M")
                    }
                }
            }
        }


# Create singleton instance
config = Config()
