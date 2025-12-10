"""
Database Data Import and Verification Script
Connects to MongoDB Atlas and verifies data for the recommendation system
"""

import logging
from pymongo import MongoClient
from typing import Dict, List, Any
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseImporter:
    """Handle database connection and data verification"""
    
    def __init__(self, mongo_uri: str, database_name: str = "smart_travel"):
        """
        Initialize database importer
        
        Args:
            mongo_uri: MongoDB connection URI
            database_name: Database name
        """
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.client = None
        self.db = None
    
    def connect(self) -> bool:
        """
        Connect to MongoDB
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongo_uri)
            
            # Test connection
            databases = self.client.list_database_names()
            logger.info(f"✓ Kết nối thành công tới MongoDB!")
            logger.info(f"✓ Databases có sẵn: {databases}")
            
            # Check if target database exists
            if self.database_name not in databases:
                logger.warning(f"⚠ Database '{self.database_name}' chưa tồn tại. Sẽ được tạo khi thêm data.")
            
            self.db = self.client[self.database_name]
            return True
            
        except Exception as e:
            logger.error(f"✗ Lỗi khi kết nối MongoDB: {e}")
            logger.error("Vui lòng kiểm tra connection string và network access trong MongoDB Atlas.")
            return False
    
    def verify_collections(self) -> Dict[str, Any]:
        """
        Verify required collections exist
        
        Returns:
            Dictionary with collection stats
        """
        if self.db is None:
            logger.error("Database chưa được kết nối!")
            return {}
        
        logger.info("\n" + "="*60)
        logger.info("KIỂM TRA COLLECTIONS")
        logger.info("="*60)
        
        collections = self.db.list_collection_names()
        logger.info(f"Collections có trong database '{self.database_name}':")
        logger.info(f"  {collections}")
        
        required_collections = ['places', 'tours', 'worldcities', 'user_preferences']
        stats = {}
        
        for coll_name in required_collections:
            collection = self.db[coll_name]
            count = collection.count_documents({})
            
            stats[coll_name] = {
                'exists': coll_name in collections,
                'count': count,
                'sample': collection.find_one({}) if count > 0 else None
            }
            
            status = "✓" if count > 0 else "✗"
            logger.info(f"\n{status} Collection '{coll_name}':")
            logger.info(f"   - Tồn tại: {stats[coll_name]['exists']}")
            logger.info(f"   - Số documents: {count:,}")
            
            if count > 0:
                sample = stats[coll_name]['sample']
                if sample:
                    logger.info(f"   - Các trường: {list(sample.keys())[:10]}...")
        
        return stats
    
    def verify_places_data(self) -> bool:
        """
        Verify places collection has required fields
        
        Returns:
            True if data is valid
        """
        logger.info("\n" + "="*60)
        logger.info("KIỂM TRA DỮ LIỆU PLACES")
        logger.info("="*60)
        
        collection = self.db['places']
        sample = collection.find_one({})
        
        if not sample:
            logger.error("✗ Collection 'places' không có dữ liệu!")
            return False
        
        required_fields = {
            'id': str,
            'city': str,
            'types': list,
            'rating': (int, float),
            'location': dict,
            'displayName': (dict, str),
        }
        
        all_valid = True
        
        for field, expected_type in required_fields.items():
            if field in sample:
                actual_type = type(sample[field])
                type_match = isinstance(sample[field], expected_type)
                
                status = "✓" if type_match else "✗"
                logger.info(f"{status} Trường '{field}': {actual_type.__name__}")
                
                if not type_match:
                    all_valid = False
                    logger.warning(f"   ⚠ Expected {expected_type}, got {actual_type}")
            else:
                logger.error(f"✗ Thiếu trường bắt buộc: '{field}'")
                all_valid = False
        
        # Check location fields
        if 'location' in sample:
            loc = sample['location']
            if 'latitude' in loc and 'longitude' in loc:
                logger.info(f"✓ Location: lat={loc['latitude']}, lng={loc['longitude']}")
            else:
                logger.error("✗ Location thiếu latitude/longitude")
                all_valid = False
        
        # Sample places by city
        logger.info("\n📊 Phân bố places theo city:")
        pipeline = [
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        for result in collection.aggregate(pipeline):
            city = result['_id']
            count = result['count']
            logger.info(f"   - {city}: {count:,} places")
        
        return all_valid
    
    def verify_tours_data(self) -> bool:
        """
        Verify tours collection for collaborative filtering
        
        Returns:
            True if data exists
        """
        logger.info("\n" + "="*60)
        logger.info("KIỂM TRA DỮ LIỆU TOURS")
        logger.info("="*60)
        
        collection = self.db['tours']
        count = collection.count_documents({})
        
        logger.info(f"Tổng số tours: {count:,}")
        
        if count > 0:
            sample = collection.find_one({})
            
            # Check for required fields
            has_participants = 'participants' in sample
            has_itinerary = 'itinerary' in sample
            
            logger.info(f"✓ Sample tour có participants: {has_participants}")
            logger.info(f"✓ Sample tour có itinerary: {has_itinerary}")
            
            if has_itinerary and sample['itinerary']:
                day = sample['itinerary'][0]
                if 'places' in day:
                    logger.info(f"✓ Day 1 có {len(day['places'])} places")
            
            return True
        else:
            logger.warning("⚠ Collection 'tours' chưa có dữ liệu")
            logger.warning("⚠ Collaborative filtering sẽ không hoạt động tốt")
            return False
    
    def verify_worldcities_data(self) -> bool:
        """
        Verify worldcities collection
        
        Returns:
            True if data is valid
        """
        logger.info("\n" + "="*60)
        logger.info("KIỂM TRA DỮ LIỆU WORLDCITIES")
        logger.info("="*60)
        
        collection = self.db['worldcities']
        count = collection.count_documents({})
        
        logger.info(f"Tổng số cities: {count:,}")
        
        if count > 0:
            sample = collection.find_one({})
            
            required_fields = ['city', 'country', 'lat', 'lng']
            all_present = all(field in sample for field in required_fields)
            
            if all_present:
                logger.info(f"✓ Sample city: {sample['city']}, {sample['country']}")
                logger.info(f"✓ Tọa độ: {sample['lat']}, {sample['lng']}")
                return True
            else:
                logger.error("✗ Thiếu trường bắt buộc trong worldcities")
                return False
        else:
            logger.warning("⚠ Collection 'worldcities' chưa có dữ liệu")
            return False
    
    def verify_user_preference_data(self) -> Dict[str, Any]:
        """
        Verify user_preferences collection
        
        Returns:
            Dictionary with user preferences data
        """
        logger.info("\n" + "="*60)
        logger.info("KIỂM TRA DỮ LIỆU USER_PREFERENCES")
        logger.info("="*60)
        
        collection = self.db['user_preferences']
        count = collection.count_documents({})
        
        logger.info(f"Tổng số user preferences: {count:,}")
        
        result = {
            'count': count,
            'users': [],
            'valid': False
        }
        
        if count > 0:
            # Get sample user preference
            sample = collection.find_one({})
            
            required_fields = [
                'user_id', 'city_id', 'city_name',
                'liked_restaurants', 'disliked_restaurants',
                'liked_hotels', 'disliked_hotels',
                'liked_activities', 'disliked_activities',
                'liked_transport', 'disliked_transport'
            ]
            
            all_present = all(field in sample for field in required_fields)
            
            if all_present:
                logger.info(f"✓ Sample user preference:")
                logger.info(f"   - User ID: {sample['user_id']}")
                logger.info(f"   - City: {sample['city_name']} (ID: {sample['city_id']})")
                logger.info(f"   - Liked restaurants: {len(sample['liked_restaurants'])}")
                logger.info(f"   - Liked hotels: {len(sample['liked_hotels'])}")
                logger.info(f"   - Liked activities: {len(sample['liked_activities'])}")
                logger.info(f"   - Liked transport: {sample['liked_transport']}")
                
                # Get all users with their preferences
                logger.info(f"\n📊 Danh sách users có preferences:")
                
                users = list(collection.find({}).limit(10))
                for i, user in enumerate(users, 1):
                    total_likes = (
                        len(user.get('liked_restaurants', [])) +
                        len(user.get('liked_hotels', [])) +
                        len(user.get('liked_activities', []))
                    )
                    
                    user_info = {
                        'user_id': user['user_id'],
                        'city_name': user['city_name'],
                        'city_id': user['city_id'],
                        'total_likes': total_likes,
                        'liked_restaurants': user.get('liked_restaurants', []),
                        'liked_hotels': user.get('liked_hotels', []),
                        'liked_activities': user.get('liked_activities', []),
                        'liked_transport': user.get('liked_transport', [])
                    }
                    
                    result['users'].append(user_info)
                    
                    logger.info(f"   {i}. User: {user['user_id'][:20]}...")
                    logger.info(f"      City: {user['city_name']}")
                    logger.info(f"      Total likes: {total_likes} places")
                
                result['valid'] = True
                return result
            else:
                logger.error("✗ Thiếu trường bắt buộc trong user_preference")
                missing = [f for f in required_fields if f not in sample]
                logger.error(f"   Thiếu: {missing}")
                return result
        else:
            logger.warning("⚠ Collection 'user_preferences' chưa có dữ liệu")
            logger.warning("⚠ Không thể test với user preferences thực tế")
            return result
    
    def get_user_preference_for_test(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get user preference data for testing
        
        Args:
            user_id: Optional specific user_id to retrieve
            
        Returns:
            User preference dictionary or None
        """
        collection = self.db['user_preferences']
        
        if user_id:
            user_pref = collection.find_one({'user_id': user_id})
        else:
            # Get first user with most liked places
            all_users = list(collection.find({}))
            
            if not all_users:
                return None
            
            # Calculate total interactions for each user
            users_with_scores = []
            for user in all_users:
                total = (
                    len(user.get('liked_restaurants', [])) +
                    len(user.get('liked_hotels', [])) +
                    len(user.get('liked_activities', []))
                )
                users_with_scores.append((user, total))
            
            # Sort by total interactions
            users_with_scores.sort(key=lambda x: x[1], reverse=True)
            user_pref = users_with_scores[0][0] if users_with_scores else None
        
        if user_pref:
            logger.info(f"\n✓ Đã tìm thấy user preference cho testing:")
            logger.info(f"   User ID: {user_pref['user_id']}")
            logger.info(f"   City: {user_pref['city_name']}")
            logger.info(f"   Liked restaurants: {len(user_pref.get('liked_restaurants', []))}")
            logger.info(f"   Liked hotels: {len(user_pref.get('liked_hotels', []))}")
            logger.info(f"   Liked activities: {len(user_pref.get('liked_activities', []))}")
            
            return user_pref
        else:
            logger.warning("⚠ Không tìm thấy user preference")
            return None
    
    def create_indexes(self):
        """Create indexes for better performance"""
        logger.info("\n" + "="*60)
        logger.info("TẠO INDEXES")
        logger.info("="*60)
        
        try:
            # Places indexes
            places = self.db['places']
            places.create_index([("city", 1)])
            places.create_index([("types", 1)])
            places.create_index([("rating", -1)])
            logger.info("✓ Created indexes for 'places' collection")
            
            # Tours indexes
            tours = self.db['tours']
            tours.create_index([("destination", 1)])
            tours.create_index([("tour_id", 1)])
            logger.info("✓ Created indexes for 'tours' collection")
            
            # Worldcities indexes
            cities = self.db['worldcities']
            cities.create_index([("city", 1)])
            cities.create_index([("country", 1)])
            logger.info("✓ Created indexes for 'worldcities' collection")
            
            # User preference indexes
            user_prefs = self.db['user_preferences']
            user_prefs.create_index([("user_id", 1)])
            user_prefs.create_index([("city_id", 1)])
            user_prefs.create_index([("city_name", 1)])
            logger.info("✓ Created indexes for 'user_preferences' collection")
            
        except Exception as e:
            logger.warning(f"⚠ Lỗi khi tạo indexes: {e}")
    
    def test_query_places(self, city: str = "Bangkok", limit: int = 5):
        """
        Test querying places
        
        Args:
            city: City to query
            limit: Number of results
        """
        logger.info("\n" + "="*60)
        logger.info(f"TEST QUERY: Places in {city}")
        logger.info("="*60)
        
        collection = self.db['places']
        places = list(collection.find({"city": city}).limit(limit))
        
        logger.info(f"Found {len(places)} places in {city}:")
        
        for i, place in enumerate(places, 1):
            name = place.get('displayName', {})
            if isinstance(name, dict):
                name = name.get('text', 'Unknown')
            
            rating = place.get('rating', 0)
            types = place.get('types', [])[:3]
            
            logger.info(f"{i}. {name}")
            logger.info(f"   Rating: {rating}/5.0")
            logger.info(f"   Types: {', '.join(types)}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report
        
        Returns:
            Summary dictionary
        """
        logger.info("\n" + "="*60)
        logger.info("BÁO CÁO TỔNG KẾT")
        logger.info("="*60)
        
        summary = {
            'database': self.database_name,
            'connected': self.db is not None,
            'collections': {}
        }
        
        if self.db is not None:
            for coll_name in ['places', 'tours', 'worldcities', 'user_preferences']:
                collection = self.db[coll_name]
                count = collection.count_documents({})
                summary['collections'][coll_name] = count
                
                status = "✓" if count > 0 else "✗"
                logger.info(f"{status} {coll_name}: {count:,} documents")
            
            # Check if ready for recommender
            places_ok = summary['collections'].get('places', 0) > 0
            cities_ok = summary['collections'].get('worldcities', 0) > 0
            
            summary['ready_for_recommender'] = places_ok and cities_ok
            
            logger.info("\n📊 Trạng thái hệ thống:")
            if summary['ready_for_recommender']:
                logger.info("✓ SẴN SÀNG sử dụng Recommendation System!")
                logger.info("  Bạn có thể chạy: python main.py")
            else:
                logger.warning("✗ CHƯA SẴN SÀNG - Cần import thêm dữ liệu")
                if not places_ok:
                    logger.warning("  - Thiếu dữ liệu places")
                if not cities_ok:
                    logger.warning("  - Thiếu dữ liệu worldcities")
        
        return summary
    
    def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("\n✓ Đã đóng kết nối MongoDB")


def main():
    """Main function"""
    # MongoDB connection string
    MONGO_URI = "mongodb+srv://hain65633_db_user:12345@cluster0.olqzq.mongodb.net/"
    DATABASE_NAME = "smart_travel"
    
    logger.info("="*60)
    logger.info("DATABASE IMPORT & VERIFICATION TOOL")
    logger.info("Smart Travel Recommendation System")
    logger.info("="*60)
    
    # Initialize importer
    importer = DatabaseImporter(MONGO_URI, DATABASE_NAME)
    
    # Connect
    if not importer.connect():
        logger.error("\n✗ Không thể kết nối database!")
        sys.exit(1)
    
    # Verify collections
    stats = importer.verify_collections()
    
    # Verify data
    places_valid = importer.verify_places_data()
    tours_exist = importer.verify_tours_data()
    cities_valid = importer.verify_worldcities_data()
    user_prefs = importer.verify_user_preference_data()
    
    # Create indexes
    importer.create_indexes()
    
    # Test query
    if stats.get('places', {}).get('count', 0) > 0:
        importer.test_query_places(city="Hanoi", limit=5)
    
    # Test getting user preference for recommendation
    if user_prefs.get('valid') and user_prefs.get('count', 0) > 0:
        logger.info("\n" + "="*60)
        logger.info("TEST: LẤY USER PREFERENCE CHO RECOMMENDATION")
        logger.info("="*60)
        
        test_user = importer.get_user_preference_for_test()
        
        if test_user:
            logger.info(f"\n💡 Gợi ý sử dụng:")
            logger.info(f"   Bạn có thể sử dụng user này để test recommendation:")
            logger.info(f"   - User ID: {test_user['user_id']}")
            logger.info(f"   - City: {test_user['city_name']}")
            logger.info(f"   - Selected places: {len(test_user.get('liked_restaurants', [])) + len(test_user.get('liked_hotels', [])) + len(test_user.get('liked_activities', []))} places")
    
    # Generate summary
    summary = importer.generate_summary_report()
    
    # Disconnect
    importer.disconnect()
    
    # Exit code
    if summary.get('ready_for_recommender'):
        logger.info("\n🎉 SUCCESS! Database is ready.")
        sys.exit(0)
    else:
        logger.warning("\n⚠ Database needs more data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
