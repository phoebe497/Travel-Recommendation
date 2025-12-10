"""
Block Scheduler
Schedule places within time blocks with optimization
"""

import logging
from typing import List, Dict, Optional, Tuple
from itertools import combinations, permutations
from dataclasses import dataclass
from datetime import time, datetime, timedelta

from src.models import Place
from src.graph_builder import PlaceGraph
from src.transport_manager import TransportManager, TransportMode
from src.config import TimeBlock, BlockType, TimeBlockConfig
from src.place_filter import PlaceFilter

logger = logging.getLogger(__name__)


@dataclass
class ScheduledPlace:
    """A place scheduled in a time block"""
    place: Place
    arrival_time: time
    departure_time: time
    visit_duration_hours: float
    score: float
    # Transport to next place
    transport_to_next: Optional[str] = None
    distance_to_next_km: Optional[float] = None
    travel_time_to_next_hours: Optional[float] = None
    travel_cost_to_next: Optional[float] = None


@dataclass
class BlockSchedule:
    """Schedule for a single time block"""
    block: TimeBlock
    scheduled_places: List[ScheduledPlace]
    total_score: float
    total_travel_time_hours: float
    total_visit_time_hours: float
    total_cost: float
    success: bool
    reason: str


class BlockScheduler:
    """
    Schedule places within time blocks with optimization
    Handles meals, activities, and rest blocks
    """
    
    # Default visit durations by block type (hours)
    DEFAULT_VISIT_DURATIONS = {
        BlockType.BREAKFAST: 0.75,  # 45 minutes
        BlockType.LUNCH: 1.0,       # 1 hour
        BlockType.DINNER: 1.5,      # 1.5 hours
        BlockType.MORNING: 1.0,     # 1 hour per activity
        BlockType.AFTERNOON: 1.25,  # 1.25 hours per activity
        BlockType.EVENING: 1.0,     # 1 hour
        BlockType.HOTEL: 9.0,       # Full night
    }
    
    def __init__(self, graph: PlaceGraph, all_places: List[Place]):
        """
        Initialize block scheduler
        
        Args:
            graph: PlaceGraph for distance calculations
            all_places: All available places
        """
        self.graph = graph
        self.all_places = all_places
        
    def schedule_meal_block(
        self,
        block: TimeBlock,
        candidates: List[Place],
        previous_location: Optional[Place] = None,
        hybrid_scores: Optional[Dict[str, float]] = None
    ) -> BlockSchedule:
        """
        Schedule a meal block (breakfast/lunch/dinner)
        
        Args:
            block: TimeBlock for the meal
            candidates: Candidate places (pre-filtered)
            previous_location: Previous place (for travel calculation)
            hybrid_scores: Hybrid recommendation scores
            
        Returns:
            BlockSchedule with 1 selected place
        """
        if not candidates:
            return BlockSchedule(
                block=block,
                scheduled_places=[],
                total_score=0,
                total_travel_time_hours=0,
                total_visit_time_hours=0,
                total_cost=0,
                success=False,
                reason="No candidates available"
            )
        
        # Sort by score (use hybrid score if available, else rating)
        if hybrid_scores:
            scored_candidates = [
                (p, hybrid_scores.get(p.place_id, p.rating / 5.0))
                for p in candidates
            ]
        else:
            scored_candidates = [(p, p.rating / 5.0) for p in candidates]
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Select best place considering travel time from previous location
        best_place = None
        best_score = 0
        best_travel_info = None
        
        for place, score in scored_candidates[:10]:  # Check top 10
            travel_info = None
            penalty = 0
            
            if previous_location:
                # Calculate travel time and cost
                distance = self.graph.get_shortest_distance(
                    previous_location.place_id,
                    place.place_id
                )
                
                # Get transport info
                transport_info = TransportManager.get_transport_info(
                    distance,
                    available_time_hours=0.5  # Max 30 min travel
                )
                
                travel_info = transport_info
                
                # Penalize distant places
                if transport_info['travel_time_hours'] > 0.3:  # > 18 min
                    penalty = 0.1 * transport_info['travel_time_hours']
            
            adjusted_score = score - penalty
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_place = place
                best_travel_info = travel_info
        
        if not best_place:
            best_place = scored_candidates[0][0]
            best_score = scored_candidates[0][1]
        
        # Schedule the place
        visit_duration = self.DEFAULT_VISIT_DURATIONS[block.block_type]
        
        # Calculate times
        arrival_time = block.start_time
        departure_dt = datetime.combine(datetime.today(), arrival_time) + \
                       timedelta(hours=visit_duration)
        departure_time = departure_dt.time()
        
        scheduled = ScheduledPlace(
            place=best_place,
            arrival_time=arrival_time,
            departure_time=departure_time,
            visit_duration_hours=visit_duration,
            score=best_score
        )
        
        total_cost = 0
        if best_travel_info:
            total_cost = best_travel_info.get('cost_usd', 0)
        
        return BlockSchedule(
            block=block,
            scheduled_places=[scheduled],
            total_score=best_score,
            total_travel_time_hours=best_travel_info['travel_time_hours'] if best_travel_info else 0,
            total_visit_time_hours=visit_duration,
            total_cost=total_cost,
            success=True,
            reason=f"Selected {best_place.name} (score: {best_score:.3f})"
        )
    
    def schedule_activity_block(
        self,
        block: TimeBlock,
        candidates: List[Place],
        previous_location: Optional[Place] = None,
        hybrid_scores: Optional[Dict[str, float]] = None
    ) -> BlockSchedule:
        """
        Schedule an activity block (morning/afternoon/evening)
        Optimizes combination of places within time constraints
        
        Args:
            block: TimeBlock for activities
            candidates: Candidate places (pre-filtered)
            previous_location: Previous place
            hybrid_scores: Hybrid recommendation scores
            
        Returns:
            BlockSchedule with optimized places
        """
        if not candidates:
            return BlockSchedule(
                block=block,
                scheduled_places=[],
                total_score=0,
                total_travel_time_hours=0,
                total_visit_time_hours=0,
                total_cost=0,
                success=False,
                reason="No candidates available"
            )
        
        num_places = block.num_places
        available_hours = block.get_available_hours()
        visit_duration = self.DEFAULT_VISIT_DURATIONS.get(block.block_type, 1.0)
        
        # Get scores
        if hybrid_scores:
            scored_candidates = [
                (p, hybrid_scores.get(p.place_id, p.rating / 5.0))
                for p in candidates
            ]
        else:
            scored_candidates = [(p, p.rating / 5.0) for p in candidates]
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Limit candidates to top K for performance
        top_k = min(20, len(scored_candidates))
        top_candidates = scored_candidates[:top_k]
        
        # Try combinations
        best_schedule = None
        best_total_score = 0
        
        # Special case: only 1 place needed
        if num_places == 1:
            place, score = top_candidates[0]
            
            scheduled_place = ScheduledPlace(
                place=place,
                arrival_time=block.start_time,
                departure_time=(datetime.combine(
                    datetime.today(),
                    block.start_time
                ) + timedelta(hours=visit_duration)).time(),
                visit_duration_hours=visit_duration,
                score=score
            )
            
            return BlockSchedule(
                block=block,
                scheduled_places=[scheduled_place],
                total_score=score,
                total_travel_time_hours=0,
                total_visit_time_hours=visit_duration,
                total_cost=0,
                success=True,
                reason=f"Selected {place.name}"
            )
        
        # Try combinations of num_places
        for combo in combinations([p for p, s in top_candidates], num_places):
            # Try different orderings
            for perm in permutations(combo):
                schedule = self._evaluate_activity_sequence(
                    list(perm),
                    block,
                    previous_location,
                    visit_duration,
                    available_hours,
                    hybrid_scores
                )
                
                if schedule and schedule.success:
                    if schedule.total_score > best_total_score:
                        best_total_score = schedule.total_score
                        best_schedule = schedule
        
        if best_schedule:
            return best_schedule
        
        # Fallback: just take top places without optimization
        fallback_places = [p for p, s in top_candidates[:num_places]]
        return self._create_simple_schedule(
            fallback_places,
            block,
            visit_duration,
            hybrid_scores
        )
    
    def _evaluate_activity_sequence(
        self,
        places: List[Place],
        block: TimeBlock,
        previous_location: Optional[Place],
        visit_duration: float,
        available_hours: float,
        hybrid_scores: Optional[Dict[str, float]]
    ) -> Optional[BlockSchedule]:
        """Evaluate if a sequence of places fits in block"""
        
        scheduled_places = []
        current_time_dt = datetime.combine(datetime.today(), block.start_time)
        total_travel_time = 0
        total_cost = 0
        total_score = 0
        
        current_location = previous_location
        
        for i, place in enumerate(places):
            # Calculate travel FROM previous location TO current place
            travel_time = 0
            travel_cost = 0
            
            if current_location:
                distance = self.graph.get_shortest_distance(
                    current_location.place_id,
                    place.place_id
                )
                
                transport_info = TransportManager.get_transport_info(distance)
                travel_time = transport_info['travel_time_hours']
                travel_cost = transport_info['cost_usd']
                
                # Add travel time
                current_time_dt += timedelta(hours=travel_time)
                total_travel_time += travel_time
                total_cost += travel_cost
            
            # Arrival time (includes travel time)
            arrival_time = current_time_dt.time()
            
            # Visit
            current_time_dt += timedelta(hours=visit_duration)
            departure_time = current_time_dt.time()
            
            # Check if we exceed block
            block_end_dt = datetime.combine(datetime.today(), block.end_time)
            if block.end_time < block.start_time:  # Overnight
                block_end_dt += timedelta(days=1)
            
            if current_time_dt > block_end_dt:
                # Doesn't fit
                return None
            
            # Get score
            score = hybrid_scores.get(place.place_id, place.rating / 5.0) \
                    if hybrid_scores else place.rating / 5.0
            total_score += score
            
            # Calculate transport TO NEXT place (if not last)
            transport_to_next = None
            distance_to_next = None
            travel_time_to_next = None
            travel_cost_to_next = None
            
            if i < len(places) - 1:
                next_place = places[i + 1]
                distance_to_next = self.graph.get_shortest_distance(
                    place.place_id,
                    next_place.place_id
                )
                next_transport_info = TransportManager.get_transport_info(distance_to_next)
                transport_to_next = next_transport_info['mode']
                travel_time_to_next = next_transport_info['travel_time_hours']
                travel_cost_to_next = next_transport_info['cost_usd']
            
            # Create scheduled place
            scheduled = ScheduledPlace(
                place=place,
                arrival_time=arrival_time,
                departure_time=departure_time,
                visit_duration_hours=visit_duration,
                score=score,
                transport_to_next=transport_to_next,
                distance_to_next_km=distance_to_next,
                travel_time_to_next_hours=travel_time_to_next,
                travel_cost_to_next=travel_cost_to_next
            )
            
            scheduled_places.append(scheduled)
            current_location = place
        
        # Check total time
        total_time = total_travel_time + visit_duration * len(places)
        if total_time > available_hours:
            return None
        
        return BlockSchedule(
            block=block,
            scheduled_places=scheduled_places,
            total_score=total_score,
            total_travel_time_hours=total_travel_time,
            total_visit_time_hours=visit_duration * len(places),
            total_cost=total_cost,
            success=True,
            reason=f"Optimized {len(places)} activities"
        )
    
    def _create_simple_schedule(
        self,
        places: List[Place],
        block: TimeBlock,
        visit_duration: float,
        hybrid_scores: Optional[Dict[str, float]]
    ) -> BlockSchedule:
        """Create simple schedule without optimization"""
        
        scheduled_places = []
        current_time_dt = datetime.combine(datetime.today(), block.start_time)
        total_score = 0
        
        for place in places:
            score = hybrid_scores.get(place.place_id, place.rating / 5.0) \
                    if hybrid_scores else place.rating / 5.0
            total_score += score
            
            scheduled = ScheduledPlace(
                place=place,
                arrival_time=current_time_dt.time(),
                departure_time=(current_time_dt + timedelta(hours=visit_duration)).time(),
                visit_duration_hours=visit_duration,
                score=score
            )
            
            scheduled_places.append(scheduled)
            current_time_dt += timedelta(hours=visit_duration + 0.5)  # Add buffer
        
        return BlockSchedule(
            block=block,
            scheduled_places=scheduled_places,
            total_score=total_score,
            total_travel_time_hours=0,
            total_visit_time_hours=visit_duration * len(places),
            total_cost=0,
            success=True,
            reason="Simple schedule (fallback)"
        )
    
    def schedule_hotel_block(
        self,
        block: TimeBlock,
        candidates: List[Place],
        previous_location: Optional[Place] = None,
        hybrid_scores: Optional[Dict[str, float]] = None
    ) -> BlockSchedule:
        """
        Schedule hotel block
        Select hotel close to last activity
        
        Args:
            block: Hotel time block
            candidates: Candidate hotels
            previous_location: Last activity location
            hybrid_scores: Hybrid scores
            
        Returns:
            BlockSchedule with selected hotel
        """
        if not candidates:
            return BlockSchedule(
                block=block,
                scheduled_places=[],
                total_score=0,
                total_travel_time_hours=0,
                total_visit_time_hours=9.0,
                total_cost=0,
                success=False,
                reason="No hotels available"
            )
        
        # Score hotels by rating and proximity to last location
        scored_hotels = []
        
        for hotel in candidates:
            score = hybrid_scores.get(hotel.place_id, hotel.rating / 5.0) \
                    if hybrid_scores else hotel.rating / 5.0
            
            # Bonus for proximity to previous location
            if previous_location:
                distance = self.graph.get_shortest_distance(
                    previous_location.place_id,
                    hotel.place_id
                )
                
                # Prefer hotels within 5km
                proximity_bonus = max(0, 0.2 * (1 - distance / 5.0))
                score += proximity_bonus
            
            scored_hotels.append((hotel, score))
        
        scored_hotels.sort(key=lambda x: x[1], reverse=True)
        best_hotel, best_score = scored_hotels[0]
        
        # Schedule hotel
        scheduled = ScheduledPlace(
            place=best_hotel,
            arrival_time=block.start_time,
            departure_time=block.end_time,
            visit_duration_hours=9.0,
            score=best_score
        )
        
        return BlockSchedule(
            block=block,
            scheduled_places=[scheduled],
            total_score=best_score,
            total_travel_time_hours=0,
            total_visit_time_hours=9.0,
            total_cost=0,
            success=True,
            reason=f"Selected {best_hotel.name} (score: {best_score:.3f})"
        )
    
    def schedule_block(
        self,
        block: TimeBlock,
        candidates: List[Place],
        previous_location: Optional[Place] = None,
        hybrid_scores: Optional[Dict[str, float]] = None
    ) -> BlockSchedule:
        """
        Schedule any type of block
        
        Args:
            block: TimeBlock to schedule
            candidates: Candidate places
            previous_location: Previous location
            hybrid_scores: Hybrid scores
            
        Returns:
            BlockSchedule
        """
        if TimeBlockConfig.is_meal_block(block.block_type):
            return self.schedule_meal_block(
                block, candidates, previous_location, hybrid_scores
            )
        elif TimeBlockConfig.is_activity_block(block.block_type):
            return self.schedule_activity_block(
                block, candidates, previous_location, hybrid_scores
            )
        elif TimeBlockConfig.is_rest_block(block.block_type):
            return self.schedule_hotel_block(
                block, candidates, previous_location, hybrid_scores
            )
        else:
            raise ValueError(f"Unknown block type: {block.block_type}")
