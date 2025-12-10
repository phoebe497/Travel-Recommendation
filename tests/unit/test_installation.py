"""
Test script to verify installation and basic functionality
Run this after installation to ensure everything works
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import numpy
        import pandas
        import sklearn
        import pymongo
        import requests
        from scipy import sparse
        
        logger.info("✓ All required packages imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        logger.error("Run: pip install -r requirements.txt")
        return False


def test_project_structure():
    """Test if project structure is correct"""
    logger.info("Testing project structure...")
    
    import os
    
    required_files = [
        'src/__init__.py',
        'src/config.py',
        'src/database.py',
        'src/models.py',
        'src/smart_itinerary_planner.py',
        'src/itinerary_builder.py',
        'src/block_scheduler.py',
        'src/place_filter.py',
        'src/graph_builder.py',
        'src/transport_manager.py',
        'src/hybrid_recommender.py',
        'src/content_filter_bert.py',
        'src/collaborative_filter_svd.py',
        'main.py',
        'utils.py',
        'requirements.txt'
    ]
    
    all_exist = True
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"✗ Missing file: {file}")
            all_exist = False
    
    if all_exist:
        logger.info("✓ All required files present")
        return True
    return False


def test_models():
    """Test data models"""
    logger.info("Testing data models...")
    
    try:
        import sys
        from pathlib import Path
        # Add project root to path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from src.models import Place, UserPreference
        
        # Test Place creation
        place = Place(
            place_id="test_123",
            name="Test Place",
            city="Bangkok",
            types=["restaurant", "food"],
            rating=4.5,
            latitude=13.7563,
            longitude=100.5018
        )
        
        # Test UserPreference creation
        user_pref = UserPreference(
            user_id="test_user",
            destination_city="Bangkok",
            trip_duration_days=3,
            budget_range="medium",
            interests=["food", "temples"]
        )
        
        # Test alpha calculation
        alpha = user_pref.calculate_alpha()
        assert 0 <= alpha <= 1, "Alpha should be between 0 and 1"
        
        logger.info("✓ Data models working correctly")
        return True
    except Exception as e:
        logger.error(f"✗ Model test failed: {e}")
        return False


def test_content_filter():
    """Test content-based filtering (BERT)"""
    logger.info("Testing content-based filtering (BERT)...")
    
    try:
        from src.content_filter_bert import ContentBasedFilterBERT
        from src.models import Place, UserPreference
        
        filter = ContentBasedFilterBERT(cache_dir="data/test_cache")
        
        # Create test places
        places = [
            Place("p1", "Restaurant A", "Bangkok", ["restaurant"], 4.5, 13.7, 100.5),
            Place("p2", "Temple B", "Bangkok", ["temple", "tourist_attraction"], 4.8, 13.7, 100.5),
            Place("p3", "Hotel C", "Bangkok", ["hotel", "lodging"], 4.2, 13.7, 100.5)
        ]
        
        user_pref = UserPreference(
            user_id="test",
            destination_city="Bangkok",
            interests=["temples", "food"]
        )
        
        # Precompute embeddings for test
        filter.precompute_embeddings(places, save_cache=False)
        
        # Calculate scores
        scores = filter.calculate_content_scores(user_pref, places, [])
        
        assert len(scores) > 0, "Should return scores"
        assert all(0 <= v <= 1 for v in scores.values()), "Scores should be 0-1"
        
        logger.info("✓ Content-based filtering (BERT) working")
        return True
    except Exception as e:
        logger.error(f"✗ Content filter test failed: {e}")
        return False


def test_collaborative_filter():
    """Test collaborative filtering (SVD)"""
    logger.info("Testing collaborative filtering (SVD)...")
    
    try:
        from src.collaborative_filter_svd import CollaborativeFilterSVD
        
        filter = CollaborativeFilterSVD(n_factors=5, model_dir="data/test_models")
        
        # Create test interactions
        interactions = [
            {"user_id": "u1", "place_id": "p1", "rating": 5},
            {"user_id": "u1", "place_id": "p2", "rating": 4},
            {"user_id": "u2", "place_id": "p1", "rating": 4},
            {"user_id": "u2", "place_id": "p3", "rating": 5},
            {"user_id": "u3", "place_id": "p2", "rating": 3},
        ]
        
        # Train filter
        filter.fit(interactions, save_model=False)
        
        # Test prediction
        score = filter.predict("u1", "p3")
        assert 0 <= score <= 5, "Score should be 0-5"
        
        logger.info("✓ Collaborative filtering (SVD) working")
        return True
    except Exception as e:
        logger.error(f"✗ Collaborative filter test failed: {e}")
        return False


def test_config():
    """Test configuration"""
    logger.info("Testing configuration...")
    
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from src.config import config, TimeBlockConfig, BlockType
        
        # Check essential configs exist
        assert hasattr(config, 'MONGODB_URI')
        assert hasattr(config, 'DEFAULT_ALPHA')
        assert hasattr(config, 'DEFAULT_BETA')
        
        # Check new TimeBlockConfig
        assert hasattr(TimeBlockConfig, 'BLOCKS')
        assert BlockType.BREAKFAST in TimeBlockConfig.BLOCKS
        assert BlockType.LUNCH in TimeBlockConfig.BLOCKS
        assert BlockType.MORNING in TimeBlockConfig.BLOCKS
        
        # Check transport manager exists
        from src.transport_manager import TransportManager
        tm = TransportManager()
        assert tm is not None
        
        logger.info("✓ Configuration valid")
        return True
    except Exception as e:
        logger.error(f"✗ Config test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("SMART TRAVEL SYSTEM - INSTALLATION TEST")
    logger.info("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Project Structure", test_project_structure),
        ("Configuration", test_config),
        ("Data Models", test_models),
        ("Content Filter", test_content_filter),
        ("Collaborative Filter", test_collaborative_filter),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n--- {name} ---")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"✗ {name} failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✓ ALL TESTS PASSED! System is ready to use.")
        logger.info("Run 'python main.py' to generate an example tour.")
        return True
    else:
        logger.error(f"\n✗ {total - passed} tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
