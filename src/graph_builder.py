"""
Graph Builder with Dijkstra Algorithm
Build graph from places and calculate shortest paths using Dijkstra
"""

import heapq
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import math

from src.models import Place

logger = logging.getLogger(__name__)


@dataclass
class Edge:
    """Edge in the graph"""
    to_place_id: str
    distance_km: float
    

class PlaceGraph:
    """
    Graph representation of places with Haversine distances
    Supports Dijkstra shortest path algorithm
    """
    
    def __init__(self, places: List[Place]):
        """
        Initialize graph from list of places
        
        Args:
            places: List of Place objects
        """
        self.places_dict = {p.place_id: p for p in places}
        self.adjacency_list: Dict[str, List[Edge]] = {}
        
        logger.info(f"Building graph with {len(places)} places")
        self._build_graph()
        
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate Haversine distance between two coordinates
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        R = 6371  # Earth radius in kilometers
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _build_graph(self):
        """Build complete graph with edges between all place pairs"""
        place_ids = list(self.places_dict.keys())
        
        for i, place_id1 in enumerate(place_ids):
            place1 = self.places_dict[place_id1]
            self.adjacency_list[place_id1] = []
            
            for place_id2 in place_ids:
                if place_id1 == place_id2:
                    continue
                
                place2 = self.places_dict[place_id2]
                
                # Calculate Haversine distance
                distance = self._haversine_distance(
                    place1.latitude, place1.longitude,
                    place2.latitude, place2.longitude
                )
                
                # Add edge
                self.adjacency_list[place_id1].append(
                    Edge(to_place_id=place_id2, distance_km=distance)
                )
        
        logger.info(f"Graph built with {len(self.adjacency_list)} nodes")
    
    def dijkstra(self, start_id: str, end_id: str) -> Tuple[float, List[str]]:
        """
        Find shortest path between two places using Dijkstra algorithm
        
        Args:
            start_id: Starting place ID
            end_id: Destination place ID
            
        Returns:
            Tuple of (total_distance_km, path_as_place_ids)
        """
        if start_id not in self.places_dict or end_id not in self.places_dict:
            logger.warning(f"Place not found: {start_id} or {end_id}")
            return float('inf'), []
        
        # Special case: same place
        if start_id == end_id:
            return 0.0, [start_id]
        
        # Initialize distances and predecessors
        distances = {place_id: float('inf') for place_id in self.places_dict}
        distances[start_id] = 0
        predecessors = {place_id: None for place_id in self.places_dict}
        
        # Priority queue: (distance, place_id)
        pq = [(0, start_id)]
        visited = set()
        
        while pq:
            current_dist, current_id = heapq.heappop(pq)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Found destination
            if current_id == end_id:
                break
            
            # Check all neighbors
            for edge in self.adjacency_list.get(current_id, []):
                neighbor_id = edge.to_place_id
                
                if neighbor_id in visited:
                    continue
                
                new_dist = current_dist + edge.distance_km
                
                if new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    predecessors[neighbor_id] = current_id
                    heapq.heappush(pq, (new_dist, neighbor_id))
        
        # Reconstruct path
        path = []
        current = end_id
        
        while current is not None:
            path.append(current)
            current = predecessors[current]
        
        path.reverse()
        
        # Check if path exists
        if path[0] != start_id:
            logger.warning(f"No path found from {start_id} to {end_id}")
            return float('inf'), []
        
        return distances[end_id], path
    
    def get_shortest_distance(self, start_id: str, end_id: str) -> float:
        """
        Get shortest distance between two places
        
        Args:
            start_id: Starting place ID
            end_id: Destination place ID
            
        Returns:
            Shortest distance in kilometers
        """
        distance, _ = self.dijkstra(start_id, end_id)
        return distance
    
    def get_shortest_path(self, start_id: str, end_id: str) -> List[Place]:
        """
        Get shortest path between two places as list of Place objects
        
        Args:
            start_id: Starting place ID
            end_id: Destination place ID
            
        Returns:
            List of Place objects in path order
        """
        _, path_ids = self.dijkstra(start_id, end_id)
        return [self.places_dict[pid] for pid in path_ids if pid in self.places_dict]
    
    def optimize_route(self, place_ids: List[str], start_id: Optional[str] = None) -> List[str]:
        """
        Optimize route through multiple places using nearest neighbor heuristic
        This is a greedy approximation to TSP
        
        Args:
            place_ids: List of place IDs to visit
            start_id: Optional starting place (if None, uses first place)
            
        Returns:
            Optimized order of place IDs
        """
        if not place_ids:
            return []
        
        if len(place_ids) == 1:
            return place_ids
        
        # Start from specified place or first place
        current = start_id if start_id and start_id in place_ids else place_ids[0]
        unvisited = set(place_ids) - {current}
        route = [current]
        
        # Greedy nearest neighbor
        while unvisited:
            nearest = min(unvisited, 
                         key=lambda p: self.get_shortest_distance(current, p))
            route.append(nearest)
            current = nearest
            unvisited.remove(nearest)
        
        return route
    
    def calculate_route_distance(self, place_ids: List[str]) -> float:
        """
        Calculate total distance for a route
        
        Args:
            place_ids: List of place IDs in route order
            
        Returns:
            Total distance in kilometers
        """
        if len(place_ids) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(len(place_ids) - 1):
            distance = self.get_shortest_distance(place_ids[i], place_ids[i + 1])
            total_distance += distance
        
        return total_distance
