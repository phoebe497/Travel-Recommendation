"""
Place Filter
Filter places based on type, opening hours, and time blocks
"""

import logging
from typing import List, Dict, Optional, Set, Any
from datetime import time, datetime, timedelta

from src.models import Place
from src.config import TimeBlock, BlockType, PlaceCategory, TimeBlockConfig

logger = logging.getLogger(__name__)


class PlaceFilter:
    """
    Filter places based on various criteria
    - Place types (restaurant, cafe, hotel, activity)
    - Opening hours
    - Time block compatibility
    """
    
    @staticmethod
    def parse_opening_hours(opening_hours_data: Optional[Dict[str, Any]]) -> Dict[str, List[tuple]]:
        """
        Parse opening hours from MongoDB regularOpeningHours structure
        
        Args:
            opening_hours_data: Dict from MongoDB with 'periods' key containing:
                [{"open": {"day": 0-6, "hour": 0-23, "minute": 0-59},
                  "close": {"day": 0-6, "hour": 0-23, "minute": 0-59}}]
                where day: 0=Sunday, 1=Monday, ..., 6=Saturday
            
        Returns:
            Dict mapping day_of_week to list of (open_time, close_time) tuples
            
        Example:
            {
                "monday": [(time(8, 0), time(22, 0))],
                "tuesday": [(time(8, 0), time(22, 0))]
            }
        """
        if not opening_hours_data or not isinstance(opening_hours_data, dict):
            # No opening hours info - assume always open (for compatibility)
            logger.debug("No opening hours info, assuming default 8am-10pm")
            return {"all_days": [(time(8, 0), time(22, 0))]}
        
        periods = opening_hours_data.get("periods", [])
        if not periods:
            logger.debug("No periods in opening hours, assuming default 8am-10pm")
            return {"all_days": [(time(8, 0), time(22, 0))]}
        
        # Day mapping: Google uses 0=Sunday, we use Monday=0
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        hours_by_day = {day: [] for day in day_names}
        
        for period in periods:
            try:
                open_info = period.get("open", {})
                close_info = period.get("close", {})
                
                if not open_info:
                    continue
                
                # Get day (0=Sunday in Google format)
                google_day = open_info.get("day", 0)
                # Convert: 0=Sunday → 6, 1=Monday → 0, etc.
                our_day = (google_day - 1) % 7
                day_name = day_names[our_day]
                
                # Get open time
                open_hour = open_info.get("hour", 8)
                open_minute = open_info.get("minute", 0)
                open_time = time(open_hour, open_minute)
                
                # Get close time
                close_hour = close_info.get("hour", 22) if close_info else 22
                close_minute = close_info.get("minute", 0) if close_info else 0
                close_time = time(close_hour, close_minute)
                
                hours_by_day[day_name].append((open_time, close_time))
                
            except Exception as e:
                logger.warning(f"Failed to parse period {period}: {e}")
                continue
        
        # Remove empty days and return
        result = {day: hours for day, hours in hours_by_day.items() if hours}
        
        if not result:
            logger.debug("No valid periods parsed, assuming default 8am-10pm")
            return {"all_days": [(time(8, 0), time(22, 0))]}
        
        return result
    
    @staticmethod
    def is_open_during_block(
        opening_hours_data: Optional[Dict[str, Any]],
        block: TimeBlock,
        day_of_week: int = 0,  # 0=Monday
        required_coverage: float = 0.7
    ) -> bool:
        """
        Check if place is open during time block
        
        Args:
            opening_hours_data: Opening hours dict from MongoDB (regularOpeningHours)
            block: TimeBlock to check
            day_of_week: 0=Monday, 6=Sunday
            required_coverage: Fraction of block that must be covered (0.7 = 70%)
            
        Returns:
            True if place is open for at least required_coverage of the block
        """
        hours_dict = PlaceFilter.parse_opening_hours(opening_hours_data)
        
        if not hours_dict:
            return False  # Closed
        
        # Get day name
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_name = day_names[day_of_week]
        
        # Get open periods for this day
        if day_name in hours_dict:
            open_periods = hours_dict[day_name]
        elif "all_days" in hours_dict:
            open_periods = hours_dict["all_days"]
        else:
            # Try to get any day as fallback
            open_periods = next(iter(hours_dict.values()), []) if hours_dict else []
        
        if not open_periods:
            return False
        
        # Check coverage
        block_start = block.start_time
        block_end = block.end_time
        
        # Convert times to minutes for easier calculation
        def time_to_minutes(t: time) -> int:
            return t.hour * 60 + t.minute
        
        block_start_min = time_to_minutes(block_start)
        block_end_min = time_to_minutes(block_end)
        
        # Handle overnight blocks
        if block_end_min < block_start_min:
            block_end_min += 24 * 60
        
        block_duration = block_end_min - block_start_min
        
        # Check overlap with open periods
        covered_minutes = 0
        for open_time, close_time in open_periods:
            open_min = time_to_minutes(open_time)
            close_min = time_to_minutes(close_time)
            
            # Handle overnight open periods
            if close_min < open_min:
                close_min += 24 * 60
            
            # Calculate overlap
            overlap_start = max(block_start_min, open_min)
            overlap_end = min(block_end_min, close_min)
            
            if overlap_end > overlap_start:
                covered_minutes += (overlap_end - overlap_start)
        
        coverage = covered_minutes / block_duration if block_duration > 0 else 0
        
        return coverage >= required_coverage
    
    @staticmethod
    def filter_by_types(
        places: List[Place],
        allowed_types: List[str]
    ) -> List[Place]:
        """
        Filter places by allowed types
        
        Args:
            places: List of places
            allowed_types: List of allowed place types
            
        Returns:
            Filtered list of places
        """
        allowed_set = set(t.lower() for t in allowed_types)
        
        filtered = []
        for place in places:
            place_types = set(t.lower() for t in place.types)
            if place_types & allowed_set:  # Intersection
                filtered.append(place)
        
        logger.debug(f"Filtered {len(places)} places → {len(filtered)} by types")
        return filtered
    
    @staticmethod
    def filter_by_block(
        places: List[Place],
        block: TimeBlock,
        day_of_week: int = 0,  # 0=Monday
        required_coverage: float = 0.7
    ) -> List[Place]:
        """
        Filter places suitable for a time block
        
        Args:
            places: List of places
            block: TimeBlock to filter for
            day_of_week: Day of week (0=Monday, 6=Sunday)
            required_coverage: Required opening hours coverage
            
        Returns:
            Filtered list of places
        """
        # First filter by type
        allowed_types = TimeBlockConfig.get_place_types_for_block(block.block_type)
        type_filtered = PlaceFilter.filter_by_types(places, allowed_types)
        
        # For rest blocks (hotels), skip opening hours check - hotels are always "open"
        if TimeBlockConfig.is_rest_block(block.block_type):
            logger.info(
                f"Filtered for {block.block_type.value} block: "
                f"{len(places)} → {len(type_filtered)} (by type) → "
                f"{len(type_filtered)} (skipped opening hours for hotels)"
            )
            return type_filtered
        
        # Adjust coverage requirement for breakfast (more lenient)
        if block.block_type == BlockType.BREAKFAST:
            required_coverage = 0.3  # Only need 30% coverage for breakfast
        
        # Then filter by opening hours
        time_filtered = []
        for place in type_filtered:
            if PlaceFilter.is_open_during_block(
                place.opening_hours,
                block,
                day_of_week,
                required_coverage
            ):
                time_filtered.append(place)
        
        logger.info(
            f"Filtered for {block.block_type.value} block: "
            f"{len(places)} → {len(type_filtered)} (by type) → "
            f"{len(time_filtered)} (by opening hours)"
        )
        
        return time_filtered
    
    @staticmethod
    def filter_by_user_preferences(
        places: List[Place],
        interests: List[str],
        min_rating: float = 3.5
    ) -> List[Place]:
        """
        Filter places by user preferences
        
        Args:
            places: List of places
            interests: User interests (keywords)
            min_rating: Minimum rating threshold
            
        Returns:
            Filtered list of places
        """
        filtered = []
        
        interest_keywords = set(i.lower() for i in interests)
        
        for place in places:
            # Rating filter
            if place.rating < min_rating:
                continue
            
            # Interest filter (check if any interest matches place types or name)
            if interest_keywords:
                place_text = " ".join([
                    place.name.lower(),
                    *[t.lower() for t in place.types]
                ])
                
                if not any(keyword in place_text for keyword in interest_keywords):
                    # Allow through anyway if rating is very high
                    if place.rating < 4.5:
                        continue
            
            filtered.append(place)
        
        logger.debug(
            f"Filtered by preferences: {len(places)} → {len(filtered)} "
            f"(min_rating={min_rating})"
        )
        
        return filtered
    
    @staticmethod
    def get_candidate_places(
        all_places: List[Place],
        block: TimeBlock,
        day_of_week: int = 0,  # 0=Monday
        user_interests: Optional[List[str]] = None,
        min_rating: float = 3.5,
        top_k: Optional[int] = None
    ) -> List[Place]:
        """
        Get candidate places for a time block
        
        Args:
            all_places: All available places
            block: TimeBlock to get candidates for
            day_of_week: Day of week (0=Monday, 6=Sunday)
            user_interests: User interests for filtering
            min_rating: Minimum rating
            top_k: Maximum number of candidates (sorted by rating)
            
        Returns:
            Filtered and sorted list of candidate places
        """
        # Filter by block requirements
        candidates = PlaceFilter.filter_by_block(all_places, block, day_of_week)
        
        # Filter by user preferences
        if user_interests:
            candidates = PlaceFilter.filter_by_user_preferences(
                candidates,
                user_interests,
                min_rating
            )
        else:
            # Just filter by rating
            candidates = [p for p in candidates if p.rating >= min_rating]
        
        # Sort by rating (descending)
        candidates.sort(key=lambda p: p.rating, reverse=True)
        
        # Limit to top K
        if top_k:
            candidates = candidates[:top_k]
        
        logger.info(
            f"Got {len(candidates)} candidates for {block.block_type.value} block"
        )
        
        return candidates
    
    @staticmethod
    def is_restaurant(place: Place) -> bool:
        """
        Check if place is primarily a restaurant/food place
        
        Args:
            place: Place to check
            
        Returns:
            True if place is a restaurant/food place
        """
        restaurant_types = [
            'restaurant', 'food', 'cafe', 'bar', 'bakery',
            'meal_takeaway', 'meal_delivery', 'bistro', 'diner',
            'chinese_restaurant', 'italian_restaurant', 'japanese_restaurant',
            'thai_restaurant', 'vietnamese_restaurant', 'korean_restaurant',
            'indian_restaurant', 'french_restaurant', 'mexican_restaurant',
            'vegetarian_restaurant', 'vegan_restaurant', 'seafood_restaurant',
            'steak_house', 'pizza_restaurant', 'hamburger_restaurant',
            'fast_food_restaurant', 'sandwich_shop', 'ramen_restaurant',
            'breakfast_restaurant', 'brunch_restaurant', 'coffee_shop'
        ]
        return any(t in place.types for t in restaurant_types)
    
    @staticmethod
    def is_hotel(place: Place) -> bool:
        """
        Check if place is a hotel/lodging
        
        Args:
            place: Place to check
            
        Returns:
            True if place is a hotel/lodging
        """
        hotel_types = ['hotel', 'lodging', 'motel', 'hostel', 'guest_house', 'inn']
        return any(t in place.types for t in hotel_types)
    
    @staticmethod
    def is_activity(place: Place) -> bool:
        """
        Check if place is an activity/attraction
        Activities are places that are NOT primarily restaurants or hotels
        
        Args:
            place: Place to check
            
        Returns:
            True if place is an activity
        """
        # If it's a restaurant or hotel, it's NOT an activity
        if PlaceFilter.is_restaurant(place) or PlaceFilter.is_hotel(place):
            return False
        
        # Otherwise it's an activity (tourist attraction, park, museum, etc.)
        return True

