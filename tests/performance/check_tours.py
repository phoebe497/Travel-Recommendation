"""
Check Tours Collection Schema
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database import MongoDBHandler
import json

db = MongoDBHandler()
tours_collection = db.get_collection('tours')

# Count total tours
total = tours_collection.count_documents({})
print(f"Total tours in database: {total}")

# Get sample tour
if total > 0:
    sample = tours_collection.find_one()
    print("\n" + "="*70)
    print("Sample Tour Schema:")
    print("="*70)
    print(json.dumps(sample, indent=2, default=str))
    
    # Show all tour cities
    cities = tours_collection.distinct("destination_city")
    print("\n" + "="*70)
    print(f"Cities with tours: {cities}")
    print("="*70)
else:
    print("No tours found in database")
