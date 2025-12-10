"""
Utility functions for API integration
Helper functions for easy integration with web frontend
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from src.models import UserPreference
from src.smart_itinerary_planner import SmartItineraryPlanner
from src.itinerary_builder import TourItinerary


class TourAPI:
    """
    Simple API wrapper for tour generation
    Use this to integrate with your web backend
    """
    
    def __init__(self, use_hybrid_scoring: bool = True):
        """
        Initialize Tour API
        
        Args:
            use_hybrid_scoring: Whether to use BERT+SVD hybrid scoring
        """
        self.planner = SmartItineraryPlanner(use_hybrid_scoring=use_hybrid_scoring)
        if self.planner.use_hybrid_scoring:
            self.planner.recommender.train_models()
    
    def generate_tour_from_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate tour from HTTP request data
        
        Args:
            request_data: Dictionary with user preferences
            
        Expected request format:
        {
            "user_id": "user_123",
            "destination": "Bangkok",
            "duration_days": 3,
            "budget": "medium",
            "interests": ["temples", "food"],
            "selected_places": ["place_id_1", "place_id_2"],
            "start_date": "2025-12-01"  # Optional
        }
        
        Returns:
            Tour dictionary (JSON-serializable)
        """
        # Parse request data
        user_pref = UserPreference(
            user_id=request_data.get("user_id", "anonymous"),
            destination_city=request_data["destination"],
            trip_duration_days=request_data.get("duration_days", 3),
            budget_range=request_data.get("budget", "medium"),
            interests=request_data.get("interests", []),
            travel_party=request_data.get("travel_party", "solo"),
            accommodation_type=request_data.get("accommodation_type", "hotel"),
            selected_places=request_data.get("selected_places", []),
            dietary_restrictions=request_data.get("dietary_restrictions", []),
            accessibility_needs=request_data.get("accessibility_needs", [])
        )
        
        # Parse start date
        start_date = None
        if "start_date" in request_data:
            start_date = datetime.fromisoformat(request_data["start_date"]).date()
        
        # Generate tour
        tour = self.planner.generate_itinerary(user_pref, start_date)
        
        # Convert to dict
        return tour.to_dict()
    
    def save_tour_to_database(self, tour_data: Dict[str, Any]) -> str:
        """
        Save generated tour to database
        
        Args:
            tour_data: Tour dictionary
            
        Returns:
            Database ID
        """
        return self.planner.db.create_tour(tour_data)


# Example Flask integration
def create_flask_routes(app):
    """
    Example Flask route integration
    
    Usage:
        from flask import Flask
        from utils import create_flask_routes
        
        app = Flask(__name__)
        create_flask_routes(app)
        app.run()
    """
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        raise ImportError("Flask not installed. Run: pip install flask")
    
    api = TourAPI(use_hybrid_scoring=True)
    
    @app.route('/api/generate-tour', methods=['POST'])
    def generate_tour():
        """Generate tour endpoint"""
        try:
            request_data = request.get_json()
            tour = api.generate_tour_from_request(request_data)
            return jsonify({
                "success": True,
                "tour": tour
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
    
    @app.route('/api/save-tour', methods=['POST'])
    def save_tour():
        """Save tour endpoint"""
        try:
            tour_data = request.get_json()
            db_id = api.save_tour_to_database(tour_data)
            return jsonify({
                "success": True,
                "id": db_id
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "service": "Smart Travel Recommendation API"
        })


# Example FastAPI integration
def create_fastapi_routes():
    """
    Example FastAPI route integration
    
    Usage:
        from fastapi import FastAPI
        from utils import create_fastapi_routes
        
        app = create_fastapi_routes()
        # Run with: uvicorn utils:app --reload
    """
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
    except ImportError:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")
    
    app = FastAPI(title="Smart Travel Recommendation API")
    api = TourAPI(use_hybrid_scoring=True)
    
    class TourRequest(BaseModel):
        user_id: str
        destination: str
        duration_days: int = 3
        budget: str = "medium"
        interests: List[str] = []
        selected_places: List[str] = []
        start_date: str = None
    
    @app.post("/api/generate-tour")
    async def generate_tour(request: TourRequest):
        """Generate personalized tour"""
        try:
            tour = api.generate_tour_from_request(request.dict())
            return {"success": True, "tour": tour}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @app.get("/api/health")
    async def health_check():
        """Health check"""
        return {
            "status": "healthy",
            "service": "Smart Travel Recommendation API"
        }
    
    return app


# Standalone function for direct use
def generate_tour_simple(
    destination: str,
    duration_days: int = 3,
    budget: str = "medium",
    interests: List[str] = None,
    selected_places: List[str] = None
) -> str:
    """
    Simplified tour generation that returns JSON string
    
    Args:
        destination: Destination city
        duration_days: Number of days
        budget: Budget range ('low', 'medium', 'high')
        interests: List of interests
        selected_places: List of pre-selected place IDs
        
    Returns:
        JSON string of the tour
    """
    api = TourAPI(use_hybrid_scoring=True)
    
    request_data = {
        "user_id": "api_user",
        "destination": destination,
        "duration_days": duration_days,
        "budget": budget,
        "interests": interests or [],
        "selected_places": selected_places or []
    }
    
    tour = api.generate_tour_from_request(request_data)
    return json.dumps(tour, indent=2)


if __name__ == "__main__":
    # Example usage
    print("Generating example tour...")
    
    tour_json = generate_tour_simple(
        destination="Bangkok",
        duration_days=3,
        budget="medium",
        interests=["temples", "food", "shopping"]
    )
    
    print("\nGenerated Tour:")
    print(tour_json)
    
    # Save to file
    with open("example_tour.json", "w", encoding="utf-8") as f:
        f.write(tour_json)
    
    print("\nTour saved to example_tour.json")


def save_tour_with_timestamp(tour: TourItinerary, output_dir: str = "outputs") -> str:
    """
    Save tour to JSON file with timestamp and city name
    
    Args:
        tour: TourItinerary object
        output_dir: Base output directory (default: outputs)
    
    Returns:
        Path to saved file
    """
    from pathlib import Path
    
    # Create outputs directory
    base_path = Path(output_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create filename with timestamp and city name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city_name = tour.destination.replace(" ", "_").replace("/", "-")
    filename = f"{safe_city_name}_{timestamp}.json"
    filepath = base_path / filename
    
    # Save tour
    tour_dict = tour.to_dict()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(tour_dict, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def get_latest_tours(output_dir: str = "outputs/tours", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get latest saved tours sorted by timestamp
    
    Args:
        output_dir: Base output directory
        limit: Maximum number of tours to return
    
    Returns:
        List of tour dictionaries with metadata
    """
    tours = []
    base_path = Path(output_dir)
    
    if not base_path.exists():
        return []
    
    # Scan all date directories
    for date_dir in sorted(base_path.iterdir(), reverse=True):
        if not date_dir.is_dir():
            continue
        
        # Scan all tour files in this date
        for tour_file in sorted(date_dir.glob("*.json"), reverse=True):
            try:
                with open(tour_file, 'r', encoding='utf-8') as f:
                    tour_data = json.load(f)
                
                tours.append({
                    'filepath': str(tour_file),
                    'filename': tour_file.name,
                    'date': date_dir.name,
                    'tour_id': tour_data.get('tour_id', 'unknown'),
                    'destination': tour_data.get('destination', 'unknown'),
                    'created_at': tour_data.get('created_at'),
                    'data': tour_data
                })
                
                if len(tours) >= limit:
                    return tours
                    
            except Exception as e:
                print(f"Error reading {tour_file}: {e}")
                continue
    
    return tours

