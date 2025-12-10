"""
Itinerary Builder
Build complete multi-day itineraries from scheduled blocks
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field

from src.models import Place, UserPreference
from src.graph_builder import PlaceGraph
from src.transport_manager import TransportManager
from src.config import TimeBlock, BlockType, TimeBlockConfig
from src.place_filter import PlaceFilter
from src.block_scheduler import BlockScheduler, BlockSchedule, ScheduledPlace

logger = logging.getLogger(__name__)


@dataclass
class DayItinerary:
    """Itinerary for a single day"""
    day_number: int
    date: str
    blocks: List[BlockSchedule] = field(default_factory=list)
    
    def get_all_scheduled_places(self) -> List[ScheduledPlace]:
        """Get all scheduled places across all blocks"""
        all_places = []
        for block_schedule in self.blocks:
            all_places.extend(block_schedule.scheduled_places)
        return all_places
    
    def get_total_cost(self) -> float:
        """Calculate total cost for the day (places + transport)"""
        transport_cost = sum(block.total_cost for block in self.blocks)
        
        # Calculate total place prices
        place_cost = 0.0
        for block in self.blocks:
            for sp in block.scheduled_places:
                if hasattr(sp.place, 'avg_price') and sp.place.avg_price:
                    place_cost += sp.place.avg_price
        
        return transport_cost + place_cost
    
    def get_total_score(self) -> float:
        """Calculate total score for the day"""
        return sum(block.total_score for block in self.blocks)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output"""
        transport_cost = sum(block.total_cost for block in self.blocks)
        
        # Calculate total place prices (avg_price_usd)
        place_cost = 0.0
        for block in self.blocks:
            for sp in block.scheduled_places:
                if hasattr(sp.place, 'avg_price') and sp.place.avg_price:
                    place_cost += sp.place.avg_price
        
        total_cost = transport_cost + place_cost
        
        return {
            "day_number": self.day_number,
            "date": self.date,
            "blocks": [self._block_to_dict(block) for block in self.blocks],
            "summary": {
                "total_places": sum(len(b.scheduled_places) for b in self.blocks),
                "places_cost_usd": round(place_cost, 2),
                "transport_cost_usd": round(transport_cost, 2),
                "total_cost_usd": round(total_cost, 2)
            }
        }
    
    def _block_to_dict(self, block_schedule: BlockSchedule) -> dict:
        """Convert block schedule to dictionary"""
        return {
            "block_type": block_schedule.block.block_type.value,
            "time_range": block_schedule.block.format_time_range(),
            "places": [self._place_to_dict(sp) for sp in block_schedule.scheduled_places]
        }
    
    def _place_to_dict(self, sp: ScheduledPlace) -> dict:
        """Convert scheduled place to dictionary"""
        place_dict = {
            "place_id": sp.place.place_id,
            "name": sp.place.name,
            "rating": sp.place.rating,
            "avg_price_usd": round(sp.place.avg_price, 2) if hasattr(sp.place, 'avg_price') and sp.place.avg_price else 0.0,
            "arrival_time": sp.arrival_time.strftime("%H:%M"),
            "departure_time": sp.departure_time.strftime("%H:%M"),
            "visit_duration_hours": round(sp.visit_duration_hours, 2)
        }
        
        # Add transport info if available
        if sp.transport_to_next:
            place_dict["transport_to_next"] = {
                "mode": sp.transport_to_next,
                "distance_km": round(sp.distance_to_next_km, 2),
                "travel_time_hours": round(sp.travel_time_to_next_hours, 3) if sp.travel_time_to_next_hours else 0,
                "cost_usd": round(sp.travel_cost_to_next, 2)
            }
        
        return place_dict


@dataclass
class TourItinerary:
    """Complete multi-day tour itinerary"""
    destination: str
    duration_days: int
    user_preferences: dict
    daily_itineraries: List[DayItinerary] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_total_cost(self) -> float:
        """Calculate total cost for entire tour"""
        return sum(day.get_total_cost() for day in self.daily_itineraries)
    
    def get_total_places(self) -> int:
        """Count total places in tour"""
        return sum(
            len(day.get_all_scheduled_places())
            for day in self.daily_itineraries
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output"""
        # Calculate totals
        total_places_cost = 0.0
        total_transport_cost = 0.0
        
        for day in self.daily_itineraries:
            for block in day.blocks:
                # Sum place costs
                for sp in block.scheduled_places:
                    if hasattr(sp.place, 'avg_price') and sp.place.avg_price:
                        total_places_cost += sp.place.avg_price
                # Sum transport costs
                total_transport_cost += block.total_cost
        
        return {
            "destination": self.destination,
            "duration_days": self.duration_days,
            "user_preferences": self.user_preferences,
            "daily_itineraries": [day.to_dict() for day in self.daily_itineraries],
            "summary": {
                "total_days": len(self.daily_itineraries),
                "total_places": self.get_total_places(),
                "places_cost_usd": round(total_places_cost, 2),
                "transport_cost_usd": round(total_transport_cost, 2),
                "total_cost_usd": round(total_places_cost + total_transport_cost, 2)
            },
            "created_at": self.created_at.isoformat(),
            "timeblock_configuration": TimeBlockConfig.to_json()
        }


class ItineraryBuilder:
    """
    Build complete itineraries from user preferences
    """
    
    def __init__(self, all_places: List[Place]):
        """
        Initialize itinerary builder
        
        Args:
            all_places: All available places in destination
        """
        self.all_places = all_places
        self.graph = PlaceGraph(all_places)
        self.scheduler = BlockScheduler(self.graph, all_places)
        
        logger.info(f"ItineraryBuilder initialized with {len(all_places)} places")
    
    def build_itinerary(
        self,
        user_pref: UserPreference,
        start_date: Optional[date] = None,
        hybrid_scores: Optional[Dict[str, float]] = None
    ) -> TourItinerary:
        """
        Build complete multi-day itinerary
        
        Args:
            user_pref: User preferences
            start_date: Tour start date (defaults to today)
            hybrid_scores: Pre-computed hybrid recommendation scores
            
        Returns:
            TourItinerary with all days scheduled
        """
        if start_date is None:
            start_date = date.today()
        
        logger.info(
            f"Building {user_pref.trip_duration_days}-day itinerary for "
            f"{user_pref.destination_city}"
        )
        
        tour = TourItinerary(
            destination=user_pref.destination_city,
            duration_days=user_pref.trip_duration_days,
            user_preferences={
                "interests": user_pref.interests,
                "budget_range": user_pref.budget_range,
                "travel_party": user_pref.travel_party,
                "accommodation_type": user_pref.accommodation_type
            }
        )
        
        # Build each day
        previous_hotel = None
        
        for day_num in range(1, user_pref.trip_duration_days + 1):
            current_date = start_date + timedelta(days=day_num - 1)
            
            logger.info(f"Planning day {day_num}/{user_pref.trip_duration_days}")
            
            day_itinerary = self._build_day_itinerary(
                day_num=day_num,
                current_date=current_date,
                user_pref=user_pref,
                previous_hotel=previous_hotel,
                hybrid_scores=hybrid_scores
            )
            
            tour.daily_itineraries.append(day_itinerary)
            
            # Get hotel for next day's starting point
            hotel_block = next(
                (b for b in day_itinerary.blocks if b.block.block_type == BlockType.HOTEL),
                None
            )
            if hotel_block and hotel_block.scheduled_places:
                previous_hotel = hotel_block.scheduled_places[0].place
        
        logger.info(
            f"Itinerary built: {tour.get_total_places()} places, "
            f"${tour.get_total_cost():.2f} total cost"
        )
        
        return tour
    
    def _build_day_itinerary(
        self,
        day_num: int,
        current_date: date,
        user_pref: UserPreference,
        previous_hotel: Optional[Place],
        hybrid_scores: Optional[Dict[str, float]]
    ) -> DayItinerary:
        """Build itinerary for a single day"""
        
        day_itinerary = DayItinerary(
            day_number=day_num,
            date=current_date.isoformat()
        )
        
        # Get daily schedule
        daily_blocks = TimeBlockConfig.get_daily_schedule()
        
        # Track current location for travel calculations
        current_location = previous_hotel
        
        # Track visited places TODAY (exclude hotels, they can repeat)
        visited_today = set()
        
        for block in daily_blocks:
            logger.info(f"  Scheduling {block.block_type.value} block")
            
            # Calculate day of week (0=Monday)
            day_of_week = current_date.weekday()
            
            # Get candidates for this block
            candidates = PlaceFilter.get_candidate_places(
                all_places=self.all_places,
                block=block,
                day_of_week=day_of_week,
                user_interests=user_pref.interests,
                min_rating=3.5,
                top_k=50  # Limit for performance
            )
            
            # Fallback for breakfast: if no candidates, use restaurants without opening hours check
            if block.block_type == BlockType.BREAKFAST and len(candidates) == 0:
                logger.info("    No breakfast places open, using all restaurants as fallback")
                allowed_types = TimeBlockConfig.get_place_types_for_block(block.block_type)
                candidates = PlaceFilter.filter_by_types(self.all_places, allowed_types)
                candidates = [p for p in candidates if p.rating >= 3.5]
                candidates.sort(key=lambda p: p.rating, reverse=True)
                candidates = candidates[:50]
            
            # For activity blocks (morning/afternoon/evening), exclude hotels
            if TimeBlockConfig.is_activity_block(block.block_type):
                candidates = [p for p in candidates if not PlaceFilter.is_hotel(p)]
            
            # Filter out already visited places TODAY (except hotels)
            if not TimeBlockConfig.is_rest_block(block.block_type):
                candidates = [p for p in candidates if p.place_id not in visited_today]
            
            logger.info(f"    Found {len(candidates)} candidates")
            
            # Schedule the block
            block_schedule = self.scheduler.schedule_block(
                block=block,
                candidates=candidates,
                previous_location=current_location,
                hybrid_scores=hybrid_scores
            )
            
            # Track visited places (except hotels)
            if block_schedule.scheduled_places and not TimeBlockConfig.is_rest_block(block.block_type):
                for sp in block_schedule.scheduled_places:
                    visited_today.add(sp.place.place_id)
            
            day_itinerary.blocks.append(block_schedule)
            
            # Update current location to last place in block
            if block_schedule.scheduled_places:
                current_location = block_schedule.scheduled_places[-1].place
                logger.info(
                    f"    Scheduled {len(block_schedule.scheduled_places)} place(s), "
                    f"score: {block_schedule.total_score:.3f}"
                )
            else:
                logger.warning(f"    No places scheduled: {block_schedule.reason}")
        
        return day_itinerary
    
    def optimize_itinerary(self, tour: TourItinerary) -> TourItinerary:
        """
        Post-process optimization of itinerary
        - Connect places with transport info
        - Balance daily schedules
        
        Args:
            tour: Initial tour itinerary
            
        Returns:
            Optimized tour itinerary
        """
        for day in tour.daily_itineraries:
            all_places = day.get_all_scheduled_places()
            
            # Add transport information between consecutive places
            for i in range(len(all_places) - 1):
                current = all_places[i]
                next_place = all_places[i + 1]
                
                # Calculate distance
                distance = self.graph.get_shortest_distance(
                    current.place.place_id,
                    next_place.place.place_id
                )
                
                # Get transport info
                transport_info = TransportManager.get_transport_info(distance)
                
                # Update current place with transport to next
                current.transport_to_next = transport_info['mode']
                current.distance_to_next_km = transport_info['distance_km']
                current.travel_time_to_next_hours = transport_info['travel_time_hours']
                current.travel_cost_to_next = transport_info['cost_usd']
        
        return tour
