"""
Database module for MongoDB connection and operations
Handles all database interactions for the Smart Travel system
"""

from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
import logging

from .config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MongoDBHandler:
    """Handler for MongoDB operations"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.connect()
    
    def connect(self) -> None:
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(config.MONGODB_URI)
            self.db = self.client[config.MONGODB_DATABASE]
            # Test connection
            self.client.server_info()
            logger.info(f"Successfully connected to MongoDB: {config.MONGODB_DATABASE}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a specific collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            MongoDB collection object
        """
        return self.db[collection_name]
    
    # Places operations
    def get_places_by_city(self, city: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all places in a specific city
        
        Args:
            city: City name
            limit: Maximum number of results
            
        Returns:
            List of place documents
        """
        collection = self.get_collection("places")
        query = {"city": city}
        cursor = collection.find(query)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def get_place_by_id(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific place by ID
        
        Args:
            place_id: Google Place ID
            
        Returns:
            Place document or None
        """
        collection = self.get_collection("places")
        return collection.find_one({"id": place_id})
    
    def get_places_by_type(self, city: str, place_type: str) -> List[Dict[str, Any]]:
        """
        Get places by type (hotel, restaurant, etc.)
        
        Args:
            city: City name
            place_type: Type of place
            
        Returns:
            List of place documents
        """
        collection = self.get_collection("places")
        query = {
            "city": city,
            "types": {"$in": [place_type]}
        }
        return list(collection.find(query))
    
    # Tours operations
    def get_tour_by_id(self, tour_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a tour by ID
        
        Args:
            tour_id: Tour ID
            
        Returns:
            Tour document or None
        """
        collection = self.get_collection("tours")
        return collection.find_one({"tour_id": tour_id})
    
    def get_tours_by_destination(self, destination: str) -> List[Dict[str, Any]]:
        """
        Get all tours for a destination
        
        Args:
            destination: Destination city
            
        Returns:
            List of tour documents
        """
        collection = self.get_collection("tours")
        return list(collection.find({"destination": destination}))
    
    def create_tour(self, tour_data: Dict[str, Any]) -> str:
        """
        Create a new tour
        
        Args:
            tour_data: Tour document
            
        Returns:
            Inserted tour ID
        """
        collection = self.get_collection("tours")
        result = collection.insert_one(tour_data)
        return str(result.inserted_id)
    
    # User-Place interaction operations
    def get_user_place_interactions(self) -> List[Dict[str, Any]]:
        """
        Get all user-place interactions for collaborative filtering
        This builds the user-item matrix
        
        Returns:
            List of user-place interaction documents
        """
        collection = self.get_collection("tours")
        interactions = []
        
        for tour in collection.find():
            # Extract user preferences and selected places
            if "participants" in tour and "itinerary" in tour:
                for participant_id in tour["participants"]:
                    for day in tour["itinerary"]:
                        for place in day.get("places", []):
                            interactions.append({
                                "user_id": str(participant_id),
                                "place_id": place.get("place_id"),
                                "rating": place.get("rating", 0),
                                "tour_id": tour.get("tour_id")
                            })
        
        return interactions
    
    def get_user_selected_places(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get places that a user has selected/visited
        
        Args:
            user_id: User ID
            
        Returns:
            List of place documents
        """
        collection = self.get_collection("tours")
        place_ids = set()
        
        # Find tours where user participated
        user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else None
        if not user_oid:
            return []
        
        tours = collection.find({"participants": user_oid})
        
        for tour in tours:
            for day in tour.get("itinerary", []):
                for place in day.get("places", []):
                    place_ids.add(place.get("place_id"))
        
        # Get full place details
        places_collection = self.get_collection("places")
        places = list(places_collection.find({"id": {"$in": list(place_ids)}}))
        
        return places
    
    # City operations
    def get_city_by_name(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Get city information
        
        Args:
            city_name: City name
            
        Returns:
            City document or None
        """
        collection = self.get_collection("worldcities")
        return collection.find_one({"city": city_name})
    
    def city_has_places(self, city_name: str) -> bool:
        """
        Check if a city has any places in the database
        
        Args:
            city_name: City name
            
        Returns:
            True if city has places, False otherwise
        """
        collection = self.get_collection("places")
        count = collection.count_documents({"city": city_name}, limit=1)
        return count > 0
    
    # User preferences operations
    def get_user_preference(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from user_preferences collection
        
        Args:
            user_id: User ID
            
        Returns:
            User preference document or None
        """
        collection = self.get_collection("user_preferences")
        return collection.find_one({"user_id": user_id})
    
    def get_all_user_preferences_with_places(self) -> List[Dict[str, Any]]:
        """
        Get all user preferences where the destination city has places in DB
        This ensures we only process users for cities we can actually recommend
        
        Returns:
            List of user preference documents (filtered)
        """
        collection = self.get_collection("user_preferences")
        all_prefs = list(collection.find())
        
        # Filter: only keep users whose city has places
        valid_prefs = []
        places_collection = self.get_collection("places")
        
        for pref in all_prefs:
            city_name = pref.get("city_name", "")
            if city_name:
                # Check if city has any places
                count = places_collection.count_documents({"city": city_name}, limit=1)
                if count > 0:
                    valid_prefs.append(pref)
                else:
                    logger.warning(f"Skipping user {pref.get('user_id')}: city '{city_name}' has no places")
        
        logger.info(f"Found {len(valid_prefs)}/{len(all_prefs)} users with valid cities")
        return valid_prefs
    
    def get_tour_interactions_for_collaborative_filter(self) -> List[Dict[str, Any]]:
        """
        Extract user-place-rating interactions from tours collection
        for training collaborative filter (SVD)
        
        Format compatible with CollaborativeFilterSVD.train():
        [{"user_id": "...", "place_id": "...", "rating": 4.5}, ...]
        
        Returns:
            List of interaction dictionaries
        """
        collection = self.get_collection("tours")
        interactions = []
        
        tours = collection.find()
        
        for tour in tours:
            # Get user IDs from participants
            participants = tour.get("participants", [])
            if not participants:
                continue
            
            # Use first participant as the main user for this tour
            user_oid = participants[0]
            user_id = str(user_oid) if isinstance(user_oid, ObjectId) else str(user_oid)
            
            # Extract places from itinerary
            itinerary = tour.get("itinerary", [])
            for day in itinerary:
                places = day.get("places", [])
                for place_entry in places:
                    place_id = place_entry.get("place_id")
                    rating = place_entry.get("rating", 0.0)
                    
                    if place_id and rating > 0:
                        interactions.append({
                            "user_id": user_id,
                            "place_id": place_id,
                            "rating": float(rating)
                        })
        
        logger.info(f"Extracted {len(interactions)} tour interactions for collaborative filter")
        return interactions
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Singleton instance
db_handler = MongoDBHandler()


def get_database() -> Database:
    """
    Get the MongoDB database instance
    
    Returns:
        Database instance for queries
    """
    return db_handler.db
