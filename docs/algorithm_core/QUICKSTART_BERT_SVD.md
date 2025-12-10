# Quick Start Guide: BERT + SVD Implementation

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# This will install:
# - sentence-transformers==2.7.0 (BERT model)
# - torch>=2.1.2 (PyTorch CPU)
# - scipy (for SVD)
```

## 📝 First-Time Setup

### Step 1: Precompute BERT Embeddings

```python
from src.content_filter_bert import ContentBasedFilterBERT
from src.database import MongoDBHandler
from src.models import Place

# Initialize filter
bert_filter = ContentBasedFilterBERT(cache_dir="data/embeddings_cache")

# Load all places from database
db = MongoDBHandler()
places_collection = db.get_collection("places")
places_data = list(places_collection.find({}))

# Convert to Place objects
places = [Place(...) for p in places_data]

# Precompute embeddings (one-time, ~10 minutes for 5000 places)
print("Precomputing BERT embeddings...")
bert_filter.precompute_embeddings(places, save_cache=True)
print(f"✅ Cached {len(places)} embeddings to disk")
```

### Step 2: Train Collaborative Filter

```python
from src.collaborative_filter_svd import CollaborativeFilterSVD

# Initialize SVD filter
svd_filter = CollaborativeFilterSVD(n_factors=50)

# Load user-place interactions from database
interactions_collection = db.get_collection("interactions")
interactions = list(interactions_collection.find({}))
# Format: [{"user_id": "u1", "place_id": "p1", "rating": 5}, ...]

# Train and save model (one-time, ~1-2 minutes)
print("Training SVD model...")
svd_filter.fit(interactions, save_model=True)
print("✅ Model saved to disk")
```

## 🎯 Using the Recommender

### Basic Usage

```python
from src.hybrid_recommender import HybridRecommender
from src.models import UserPreference

# Initialize (loads cached embeddings + trained model)
recommender = HybridRecommender(
    cache_dir="data/embeddings_cache",
    model_dir="data/models"
)

# Create user preference
user_pref = UserPreference(
    user_id="user123",
    selected_places=["temple_1", "temple_2", "museum_1"],
    destination_city="Hanoi",
    trip_duration_days=3
)

# Get recommendations (instant with cache!)
scores = recommender.calculate_hybrid_scores(
    user_pref,
    candidate_places,  # Places to score
    selected_places    # User's selections
)

# scores = {"place_id": hybrid_score, ...}
```

### Advanced: Filtering

```python
# Filter by interests and budget
recommendations = recommender.get_filtered_recommendations(
    user_pref,
    candidate_places,
    selected_places,
    interests=["culture", "history", "food"],  # Optional
    max_budget_per_day=1000000,  # Optional (VND)
    min_rating=4.0  # Optional
)

# Sort by score
top_10 = sorted(
    recommendations.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]
```

## 📊 Performance Monitoring

### Check Cache Statistics

```python
filter = ContentBasedFilterBERT()
stats = filter.get_cache_stats()

print(f"Cached embeddings: {stats['cached_embeddings']}")
print(f"Cache file exists: {stats['cache_file_exists']}")
print(f"Model loaded: {stats['model_loaded']}")
```

### Test Inference Speed

```python
import time

# Test single place encoding
place = places[0]

# With cache
start = time.time()
embedding = filter._create_place_embedding(place, use_cache=True)
elapsed = (time.time() - start) * 1000

print(f"Inference time: {elapsed:.3f} ms")
# Expected: <0.01 ms
```

## 🔄 Updating Models

### When to Re-precompute Embeddings:
- New places added to database
- Place information updated (name, types, etc.)

```python
# Get new/updated places
new_places = get_places_since_last_update()

# Add to cache (doesn't reload model)
filter.precompute_embeddings(new_places, save_cache=True)
```

### When to Retrain SVD:
- New user interactions (ratings, visits)
- Periodically (weekly/monthly)

```python
# Get recent interactions
interactions = get_all_interactions()

# Retrain and overwrite model
svd_filter.fit(interactions, save_model=True)
```

## 🐛 Troubleshooting

### Model Download Issues

```python
# If download fails, try manually:
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
# Will download to: ~/.cache/huggingface/
```

### Cache Not Loading

```python
# Clear and rebuild cache
filter = ContentBasedFilterBERT()
filter.clear_cache()  # Deletes cache file
filter.precompute_embeddings(places, save_cache=True)
```

### Low Scores for Similar Places

```python
# Check if place is in cache
place_id = "temple_1"
if place_id in filter.embedding_cache:
    print("✅ Place in cache")
else:
    print("❌ Place not cached - add to cache")
    filter.precompute_embeddings([place], save_cache=True)
```

## 📈 Expected Performance

**BERT Embeddings:**
- **First run:** ~700 ms/place (model download + encoding)
- **Cached:** <0.01 ms/place (700x faster)
- **Model size:** 1.11 GB (one-time download)
- **Memory:** ~500 MB RAM when loaded

**SVD Model:**
- **Training:** ~1-2 minutes for 10K interactions
- **Inference:** <1 ms per prediction
- **Model size:** ~1-10 MB (depends on users/places)

**Hybrid Recommender:**
- **Full pipeline:** ~50-100 ms for 1000 candidates (with cache)
- **Bottleneck:** Alpha calculation and sorting

## ✅ Validation Checklist

- [ ] sentence-transformers installed (v2.7.0)
- [ ] BERT embeddings cached (check `data/embeddings_cache/`)
- [ ] SVD model trained (check `data/models/`)
- [ ] Test inference speed (<1 ms)
- [ ] Semantic similarity working (cross-lingual)
- [ ] Recommendations make sense

## 📚 Next Steps

1. **Test with real users:** A/B test BERT vs TF-IDF
2. **Monitor performance:** Track cache hit rate, inference time
3. **Fine-tune alpha:** Adjust based on user engagement
4. **Optimize further:** Consider model quantization or DistilBERT

---

**Quick Reference:** See `docs/BERT_SVD_OPTIMIZATION.md` for detailed documentation.
