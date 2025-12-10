"""
Transport Manager
Manages transport modes and selection logic
"""

import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransportMode(Enum):
    """Available transport modes"""
    WALKING = "walking"
    MOTORBIKE = "motorbike"
    TAXI = "taxi"


@dataclass
class TransportConfig:
    """Configuration for a transport mode"""
    mode: TransportMode
    max_distance_km: float
    avg_speed_kmh: float
    cost_per_km: float
    
    def calculate_travel_time_hours(self, distance_km: float) -> float:
        """Calculate travel time in hours"""
        return distance_km / self.avg_speed_kmh
    
    def calculate_cost(self, distance_km: float) -> float:
        """Calculate travel cost"""
        return distance_km * self.cost_per_km
    
    def is_valid_for_distance(self, distance_km: float) -> bool:
        """Check if this mode can be used for given distance"""
        return distance_km <= self.max_distance_km


class TransportManager:
    """
    Manages transport selection based on distance and time constraints
    Priority: walking → motorbike → taxi
    """
    
    # Transport configurations as specified
    TRANSPORT_CONFIGS = {
        TransportMode.WALKING: TransportConfig(
            mode=TransportMode.WALKING,
            max_distance_km=1.5,
            avg_speed_kmh=5,
            cost_per_km=0
        ),
        TransportMode.MOTORBIKE: TransportConfig(
            mode=TransportMode.MOTORBIKE,
            max_distance_km=30,
            avg_speed_kmh=35,
            cost_per_km=0.4
        ),
        TransportMode.TAXI: TransportConfig(
            mode=TransportMode.TAXI,
            max_distance_km=100,
            avg_speed_kmh=30,
            cost_per_km=0.75
        ),
    }
    
    @classmethod
    def select_transport(
        cls,
        distance_km: float,
        available_time_hours: Optional[float] = None
    ) -> Tuple[TransportConfig, str]:
        """
        Select best transport mode based on distance and time constraints
        
        Args:
            distance_km: Distance to travel in kilometers
            available_time_hours: Available time in hours (optional)
            
        Returns:
            Tuple of (selected_transport_config, reason)
        """
        # Priority order: walking → motorbike → taxi
        priority_order = [
            TransportMode.WALKING,
            TransportMode.MOTORBIKE,
            TransportMode.TAXI
        ]
        
        for mode in priority_order:
            config = cls.TRANSPORT_CONFIGS[mode]
            
            # Check distance constraint
            if not config.is_valid_for_distance(distance_km):
                continue
            
            # Check time constraint if provided
            if available_time_hours is not None:
                travel_time = config.calculate_travel_time_hours(distance_km)
                if travel_time > available_time_hours:
                    reason = (f"Skipped {mode.value}: travel time {travel_time:.2f}h "
                            f"exceeds available {available_time_hours:.2f}h")
                    logger.debug(reason)
                    continue
            
            # This mode works!
            reason = cls._get_selection_reason(mode, distance_km, available_time_hours)
            logger.debug(f"Selected {mode.value} for {distance_km:.2f}km: {reason}")
            return config, reason
        
        # No valid transport found - use taxi anyway (fallback)
        config = cls.TRANSPORT_CONFIGS[TransportMode.TAXI]
        reason = (f"No valid transport for {distance_km:.2f}km "
                 f"(max taxi range: {config.max_distance_km}km). Using taxi anyway.")
        logger.warning(reason)
        return config, reason
    
    @classmethod
    def _get_selection_reason(
        cls,
        mode: TransportMode,
        distance_km: float,
        available_time_hours: Optional[float]
    ) -> str:
        """Generate human-readable reason for transport selection"""
        config = cls.TRANSPORT_CONFIGS[mode]
        travel_time = config.calculate_travel_time_hours(distance_km)
        
        reasons = [
            f"Distance: {distance_km:.2f}km ≤ {config.max_distance_km}km (max for {mode.value})"
        ]
        
        if available_time_hours is not None:
            reasons.append(
                f"Time: {travel_time:.2f}h ≤ {available_time_hours:.2f}h (available)"
            )
        else:
            reasons.append(f"Travel time: {travel_time:.2f}h")
        
        reasons.append(f"Cost: ${config.calculate_cost(distance_km):.2f}")
        
        # Add priority note
        if mode == TransportMode.WALKING:
            reasons.append("Preferred (walking is 1st priority)")
        elif mode == TransportMode.MOTORBIKE:
            reasons.append("Walking too far, motorbike is 2nd priority")
        elif mode == TransportMode.TAXI:
            reasons.append("Motorbike too far, taxi is 3rd priority")
        
        return " | ".join(reasons)
    
    @classmethod
    def get_transport_info(
        cls,
        distance_km: float,
        available_time_hours: Optional[float] = None
    ) -> dict:
        """
        Get complete transport information for a journey
        
        Args:
            distance_km: Distance in kilometers
            available_time_hours: Available time in hours
            
        Returns:
            Dictionary with transport details
        """
        config, reason = cls.select_transport(distance_km, available_time_hours)
        
        travel_time_hours = config.calculate_travel_time_hours(distance_km)
        cost = config.calculate_cost(distance_km)
        
        return {
            'mode': config.mode.value,
            'distance_km': round(distance_km, 2),
            'travel_time_hours': round(travel_time_hours, 2),
            'travel_time_minutes': round(travel_time_hours * 60, 1),
            'cost_usd': round(cost, 2),
            'speed_kmh': config.avg_speed_kmh,
            'reason': reason
        }
    
    @classmethod
    def get_all_configs(cls) -> dict:
        """Get all transport configurations"""
        return {
            mode.value: {
                'max_distance_km': config.max_distance_km,
                'avg_speed_kmh': config.avg_speed_kmh,
                'cost_per_km': config.cost_per_km
            }
            for mode, config in cls.TRANSPORT_CONFIGS.items()
        }
