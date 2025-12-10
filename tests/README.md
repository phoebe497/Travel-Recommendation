# Test Suite Documentation

Thư mục tests được tổ chức theo chức năng để dễ quản lý và bảo trì.

## 📁 Cấu trúc thư mục

```
tests/
├── README.md              # File này
├── unit/                  # Unit tests - test từng component riêng lẻ
│   ├── test_installation.py      # Test cài đặt dependencies
│   └── test_bert_optimization.py # Test BERT performance & cache
├── integration/           # Integration tests - test toàn bộ pipeline
│   ├── test_mongodb_schema.py        # Test MongoDB data loading
│   ├── test_new_itinerary_planner.py # Test new itinerary system
│   └── test_real_data.py             # Test với MongoDB real data
└── performance/           # Performance tests - đánh giá hiệu suất
    ├── benchmark_speed.py            # Đo tốc độ từng bước
    ├── evaluate_recommendation.py    # Đánh giá độ chính xác (POD/FAR/F1)
    ├── run_performance_tests.py      # Chạy tất cả performance tests
    ├── quick_test.py                 # Quick test đơn giản
    ├── README.md                     # Hướng dẫn sử dụng
    ├── PERFORMANCE_REPORT.md         # Báo cáo kết quả chi tiết
    └── reports/                      # Thư mục chứa kết quả JSON
```

## 🧪 Các loại tests

### Unit Tests (`tests/unit/`)
Tests cho từng component riêng lẻ, không phụ thuộc vào database hay external services.

**test_installation.py**
- Kiểm tra tất cả dependencies được cài đặt đúng
- Verify BERT model có thể load
- Test basic content & collaborative filtering

```bash
# Chạy test
python tests/unit/test_installation.py
```

**test_bert_optimization.py**
- Test BERT embedding performance
- Verify cache optimization (70,000x speedup)
- Check semantic similarity scores

```bash
# Chạy test  
python tests/unit/test_bert_optimization.py
```

### Integration Tests (`tests/integration/`)
Tests toàn bộ pipeline từ MongoDB → Recommendations → Itinerary Generation.

**test_mongodb_schema.py**
- Test MongoDB schema parsing (regularOpeningHours, displayName)
- Verify place filtering by type and opening hours
- Check time block compatibility

```bash
# Chạy test (cần MongoDB connection)
python tests/integration/test_mongodb_schema.py
```

**test_new_itinerary_planner.py**
- Test full SmartItineraryPlanner pipeline
- SmartItineraryPlanner → HybridRecommender (BERT + SVD) → BlockScheduler
- Generate complete multi-day itinerary
- Verify graph-based routing with Dijkstra

```bash
# Chạy test (cần MongoDB connection)
python tests/integration/test_new_itinerary_planner.py
```

**test_real_data.py**
- Load 4,972 places from MongoDB
- Test BERT embeddings với production data
- Verify hybrid scoring (BERT + SVD)
- Check cache performance

```bash
# Chạy test (cần MongoDB connection)
python tests/integration/test_real_data.py
```

### Performance Tests (`tests/performance/`)
Đánh giá hiệu suất hệ thống (Speed + Accuracy) cho Recommendation + Scheduling pipeline.

**benchmark_speed.py**
- Đo thời gian từng bước: Load → BERT → Scoring → Graph → Scheduling → Optimization
- Scalability test với 50, 100, 200 places
- Identify bottlenecks (BERT embeddings chiếm 84% lần đầu, 54% khi có cache)

**evaluate_recommendation.py**
- Đánh giá độ chính xác bằng binary classification metrics
- TP, FP, FN, TN → POD (Recall), Precision, F1-Score, FAR
- Ground truth từ tour history trong MongoDB

**run_performance_tests.py**
- Chạy tất cả performance tests (speed + accuracy)
- Generate comprehensive JSON reports

```bash
# Chạy performance tests
cd tests/performance
python run_performance_tests.py

# Hoặc quick test
python quick_test.py
```

**Kết quả mẫu:**
- Total time: 9-11s (với cache) | 48s (lần đầu)
- Throughput: 5.5 places/s (cached)
- BERT embeddings: 84% time (first run) → 54% (cached) - **7-8x speedup**
- Xem chi tiết: `tests/performance/PERFORMANCE_REPORT.md`

## 🚀 Chạy tests

### Chạy tất cả unit tests
```bash
python tests/unit/test_installation.py
python tests/unit/test_bert_optimization.py
```

### Chạy integration tests (cần MongoDB)
```bash
# Ensure .env có MONGODB_URI
python tests/integration/test_mongodb_schema.py
python tests/integration/test_new_itinerary_planner.py
python tests/integration/test_real_data.py
```

### Chạy specific test
```bash
python -m pytest tests/unit/test_installation.py -v
```

## ✅ Expected Results

### test_installation.py
```
✅ Dependencies installed
✅ BERT model loadable
✅ Content filter working
✅ Collaborative filter working
```

### test_bert_optimization.py
```
✅ BERT cache: 100 embeddings
✅ Performance: <1ms with cache (700x speedup)
✅ Semantic similarity: Hotels → Hotels (working)
```

### test_real_data.py
```
✅ MongoDB: 4,972 places loaded
✅ BERT embeddings: 100+ cached
✅ Hybrid scoring: Working
✅ Semantic match: Perfect
```

### test_integration.py
```
✅ Tour generated: 3 days, 21 places, $664.88
✅ MongoDB connection: Working
✅ BERT embeddings: Cached
✅ Hybrid recommender: Functioning
✅ Greedy scheduler: Operational
✅ Full pipeline: Ready for production
```

## 📊 Test Coverage

| Component | Unit Test | Integration Test | Status |
|-----------|-----------|------------------|--------|
| BERT Content Filter | ✅ | ✅ | Production Ready |
| SVD Collaborative Filter | ✅ | ⚠️ Not trained | Needs user data |
| Hybrid Recommender | ✅ | ✅ | Production Ready |
| Greedy Scheduler | - | ✅ | Production Ready |
| MongoDB Integration | - | ✅ | Production Ready |
| Tour Generator | - | ✅ | Production Ready |

## 🔧 Troubleshooting

### MongoDB Connection Errors
```bash
# Check .env file
cat .env | grep MONGODB_URI

# Test connection
python -c "from src.database import MongoDBHandler; db = MongoDBHandler(); print('Connected!')"
```

### BERT Model Loading Issues
```bash
# Clear cache and redownload
rm -rf data/embeddings_cache/
python tests/unit/test_bert_optimization.py
```

### Missing Dependencies
```bash
# Reinstall
pip install -r requirements.txt
```

## 📝 Adding New Tests

### Unit Test Template
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.your_module import YourClass

def test_your_feature():
    """Test description"""
    obj = YourClass()
    result = obj.your_method()
    assert result is not None
    print("✅ Test passed")

if __name__ == "__main__":
    test_your_feature()
```

### Integration Test Template
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.database import MongoDBHandler
from src.smart_itinerary_planner import SmartItineraryPlanner
from src.models import UserPreference

def test_full_pipeline():
    """Test full pipeline"""
    db = MongoDBHandler()
    planner = SmartItineraryPlanner(db_handler=db, use_hybrid_scoring=True)
    
    # Create user preference
    user_pref = UserPreference(
        user_id="test_user",
        destination_city="Hanoi",
        trip_duration_days=3,
        interests=["culture", "food"]
    )
    
    # Generate itinerary
    tour = planner.generate_itinerary(user_pref)
    assert tour.get_total_places() > 0
    
    print("✅ Integration test passed")

if __name__ == "__main__":
    test_full_pipeline()
```

## 🎯 System Status

✅ **NEW SYSTEM (SmartItineraryPlanner)**
- BERT + SVD hybrid scoring
- Graph-based routing (Dijkstra)
- Time block scheduling
- Opening hours filtering
- All tests passing

❌ **OLD SYSTEM (TourGenerator)** - Deleted
- Replaced by SmartItineraryPlanner
- Old files removed from codebase

## 📞 Support

Nếu gặp vấn đề với tests:
1. Check MongoDB connection
2. Verify dependencies: `pip list`
3. Run: `python tests/unit/test_installation.py`

3. Clear cache: `rm -rf data/embeddings_cache/`
4. Rerun test with verbose: `python test.py -v`
