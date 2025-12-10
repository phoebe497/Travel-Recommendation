# File Structure & Usage Guide

## 📁 Current System Architecture

### **Smart Itinerary Planner System** (Production)

#### Core Modules
- **`src/smart_itinerary_planner.py`** - Main entry point for itinerary generation
- **`src/itinerary_builder.py`** - Assemble multi-day itineraries
- **`src/block_scheduler.py`** - Schedule places within time blocks with optimization
- **`src/place_filter.py`** - Filter places by type, opening hours, preferences + classification helpers
- **`src/graph_builder.py`** - Graph construction & Dijkstra algorithm for routing
- **`src/transport_manager.py`** - Transport mode selection (walking/motorbike/taxi)

#### Recommendation System (BERT + SVD)
- **`src/hybrid_recommender.py`** - Hybrid scoring with dynamic alpha calculation
- **`src/content_filter_bert.py`** - BERT embeddings for content-based filtering
- **`src/collaborative_filter_svd.py`** - SVD matrix factorization for collaborative filtering

#### Supporting Files
- **`src/models.py`** - Data models (Place, UserPreference, Tour)
- **`src/database.py`** - MongoDB connection & queries
- **`src/config.py`** - Environment variables, TimeBlockConfig, PlaceCategory

#### Tests
- **`tests/integration/test_new_itinerary_planner.py`** - End-to-end test
- **`tests/integration/test_mongodb_schema.py`** - Data loading & filtering test
- **`tests/integration/test_real_data.py`** - Real data integration test
- **`tests/unit/test_bert_optimization.py`** - BERT performance tests
- **`tests/unit/test_installation.py`** - Installation verification

---

## 🔧 Configuration Files

### Active Configs

#### `src/config.py`
**Purpose**: Centralized configuration for entire system

**Key Components**:
```python
# MongoDB Settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "smart_travel"

# Algorithm Parameters
DEFAULT_ALPHA = 0.7  # Content vs Collaborative weight
DEFAULT_BETA = 0.5   # Score vs Travel time weight
TOP_K_PLACES = 50    # Max places to consider

# Time Block Configuration (merged from timeblock_config.py)
class BlockType(Enum):
    BREAKFAST = "breakfast"        # 07:00-08:00
    MORNING_ACTIVITY = "morning"   # 08:00-11:00
    LUNCH = "lunch"                # 11:00-13:00
    AFTERNOON_ACTIVITY = "afternoon"  # 13:00-18:30
    EVENING_ACTIVITY = "evening"   # 20:30-22:00
    DINNER = "dinner"              # 18:30-20:30
    HOTEL = "hotel"                # 22:00-07:00

class PlaceCategory(Enum):
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    HOTEL = "hotel"
    ACTIVITY = "activity"

# Place Type Mappings
PLACE_TYPE_MAPPING = {
    PlaceCategory.RESTAURANT: ['restaurant', 'thai_restaurant', ...],
    PlaceCategory.CAFE: ['cafe', 'bakery', 'food', ...],
    PlaceCategory.HOTEL: ['hotel', 'lodging', ...],
    PlaceCategory.ACTIVITY: ['tourist_attraction', 'bar', 'pub', ...]
}
```

**Recent Updates**:
- ✅ Merged `timeblock_config.py` into `config.py`
- ✅ Removed deprecated `TIME_BLOCKS` and `TRANSPORT_MODES`
- ✅ Added `'food'` to CAFE for breakfast places
- ✅ Added `'bar'`, `'pub'` to ACTIVITY for evening activities
- ✅ Centralized all configuration in single file

#### `src/transport_manager.py`
**Purpose**: Transport mode configurations

**Transport Modes**:
```python
WALKING:    max 1.5km,  5 km/h,  $0/km     (Priority 1)
MOTORBIKE:  max 30km,   35 km/h, $0.4/km   (Priority 2)
TAXI:       max 100km,  30 km/h, $0.75/km  (Priority 3)
```

---

## 🗑️ Deleted Files (Migration Complete)

### **Removed from src/**
- ❌ `tour_generator.py` - Replaced by `smart_itinerary_planner.py`
- ❌ `greedy_scheduler.py` - Replaced by `block_scheduler.py`
- ❌ `distance_calculator.py` - Replaced by `graph_builder.py` (Dijkstra)
- ⚠️ `timeblock_config.py` - Merged into `config.py` (backward compat wrapper kept)

### **Removed from docs/**
- ❌ `QUICKSTART.md` - Written for old TourGenerator system
- ❌ `IMPLEMENTATION_SUMMARY.md` - Written for old system
- ⚠️ `ALGORITHM_EXPLANATION.md` - Kept for update with new system details

### **Removed from tests/**
- ❌ `tests/legacy/` - Entire folder with old TourGenerator tests
- ❌ `tests/integration/test_integration.py` - Used old TourGenerator

---

## 📊 File Dependency Graph

### Current System Architecture
```
main.py / utils.py (API)
    ↓
smart_itinerary_planner.py
    ├── hybrid_recommender.py
    │   ├── content_filter_bert.py (BERT embeddings)
    │   ├── collaborative_filter_svd.py (SVD)
    │   └── place_filter.py (classification)
    ├── itinerary_builder.py
    │   ├── block_scheduler.py
    │   │   ├── graph_builder.py (Dijkstra)
    │   │   ├── transport_manager.py
    │   │   └── place_filter.py
    │   │       └── config.py (TimeBlockConfig)
    │   └── place_filter.py
    ├── database.py
    └── models.py
```

---

## 🎯 Summary

### **Current System Features**
- ✅ **BERT + SVD Hybrid Scoring**: Intelligent recommendations with dynamic alpha
- ✅ **Graph-based Routing**: Dijkstra algorithm, no external API calls
- ✅ **Time Block Scheduling**: Smart meal/activity/rest scheduling
- ✅ **Opening Hours Filtering**: Respects place availability
- ✅ **Transport Optimization**: Walking/motorbike/taxi selection
- ✅ **Multi-day Itineraries**: Complete trip planning

### **Migration Status**
- ✅ **Phase 1**: New system implemented
- ✅ **Phase 2**: main.py and utils.py updated
- ✅ **Phase 3**: Old files deleted
- ✅ **Phase 4**: Tests and docs cleaned up

---

## 📝 Configuration Best Practices

### To Add New Place Types
**Edit**: `src/config.py` → `TimeBlockConfig.PLACE_TYPE_MAPPING`

Example:
```python
PlaceCategory.CAFE: [
    'cafe', 'bakery', 'food',
    'tea_house'  # ← Add new type
]
```

### To Modify Time Blocks
**Edit**: `src/config.py` → `TimeBlockConfig.BLOCKS`

Example:
```python
TimeBlockConfig.BLOCKS = {
    BlockType.BREAKFAST: TimeBlock(
        block_type=BlockType.BREAKFAST,
        start_time=time(7, 30),  # ← Changed from 7:00
        end_time=time(8, 30),    # ← Changed from 8:00
        ...
    )
}
```

### To Adjust Transport
**Edit**: `src/transport_manager.py` → `TRANSPORT_CONFIGS`

Example:
```python
TransportMode.MOTORBIKE: TransportConfig(
    max_distance_km=40,  # ← Increase max distance
    avg_speed_kmh=40,    # ← Increase speed
    cost_per_km=0.5,     # ← Adjust cost
    ...
)
```

**Last Updated**: December 5, 2025  
**New System Status**: ✅ Fully Implemented & Tested  
**Old System Status**: ⚠️ Deprecated but kept for compatibility
