# System Architecture Diagram

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INPUT                                  │
│  • Destination: Bangkok                                              │
│  • Duration: 3 days                                                  │
│  • Budget: medium                                                    │
│  • Interests: [temples, food, parks]                                 │
│  • Selected Places: [place_id_1, place_id_2]                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE (MongoDB)                              │
│  ┌──────────────┬─────────────────┬──────────────────┐              │
│  │   places     │     tours       │   worldcities    │              │
│  │  (10,000+)   │   (historical)  │    (metadata)    │              │
│  └──────────────┴─────────────────┴──────────────────┘              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CANDIDATE FILTERING                               │
│  • Get all places in destination city                                │
│  • Filter by budget range                                            │
│  • Filter by minimum rating (3.0+)                                   │
│  • Filter by user interests                                          │
│                                                                       │
│  Result: ~500 candidate places                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌───────────────────────────┐  ┌──────────────────────────┐
│  CONTENT-BASED FILTERING  │  │ COLLABORATIVE FILTERING  │
│                           │  │                          │
│ 1. Build place embedding: │  │ 1. Build U-I matrix     │
│    [types, rating,        │  │    from historical data │
│     price, popularity]    │  │                          │
│                           │  │ 2. Matrix Factorization │
│ 2. Build user vector from│  │    (ALS algorithm)       │
│    selected places        │  │    • 20 latent factors  │
│                           │  │    • 15 iterations      │
│ 3. Cosine similarity:     │  │                          │
│    sim(user, place)       │  │ 3. Predict ratings for  │
│                           │  │    unseen places        │
│ Output: content_scores    │  │                          │
│   {place_id: 0.0-1.0}     │  │ Output: collab_scores   │
│                           │  │   {place_id: 0.0-1.0}   │
└───────────────┬───────────┘  └────────────┬─────────────┘
                │                           │
                └───────────┬───────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HYBRID SCORING                                  │
│                                                                       │
│  Calculate α based on user selections:                               │
│  • 0 selections → α = 0.3 (rely on collaborative)                    │
│  • 1-3 selections → α = 0.5                                          │
│  • 4-7 selections → α = 0.7                                          │
│  • 8+ selections → α = 0.9 (rely on content)                         │
│                                                                       │
│  hybrid_score = α × content_score + (1-α) × collab_score             │
│                 + rating_bonus                                       │
│                                                                       │
│  Select Top K places (K=30)                                          │
│  Result: [(place, score), ...]                                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   DISTANCE CALCULATION                               │
│                                                                       │
│  For each pair of places (i, j):                                     │
│  1. Calculate distance:                                              │
│     • Haversine formula (Euclidean)                                  │
│     • Or RapidAPI (accurate, slower)                                 │
│                                                                       │
│  2. Determine transport mode:                                        │
│     • 0-1.5km → walking                                              │
│     • 1.5-5km → bike/grab_bike                                       │
│     • 5-20km → bus/metro                                             │
│     • 20+km → taxi/grab_car                                          │
│                                                                       │
│  3. Calculate travel time:                                           │
│     travel_time = distance / speed                                   │
│                                                                       │
│  Result: distance_matrix[(i,j)] = {distance, transport, time, cost}  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GREEDY SCHEDULING                                 │
│                                                                       │
│  For each day:                                                       │
│    For each time_block in [morning, lunch, afternoon, ...]:         │
│      1. Filter places suitable for block:                            │
│         • Morning/Afternoon → activity places                        │
│         • Lunch/Dinner → restaurants                                 │
│         • Night → hotels                                             │
│                                                                       │
│      2. Calculate greedy score for each candidate:                   │
│         is_selected = place_id in user.selected_places               │
│         beta = 0 if is_selected else config.DEFAULT_BETA             │
│                                                                       │
│         greedy_score = (place.rating/5.0) × hybrid_score             │
│                        - beta × travel_time                          │
│                                                                       │
│      3. Select place with highest greedy_score                       │
│                                                                       │
│      4. Update:                                                      │
│         • Current location = selected place                          │
│         • Current time += duration + travel_time                     │
│         • Add travel info to previous place                          │
│                                                                       │
│  Result: scheduled_places = [ScheduledPlace, ...]                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 MULTI-DAY DISTRIBUTION                               │
│                                                                       │
│  Distribute scheduled places across days:                            │
│  • Day 1: places[0:10]                                               │
│  • Day 2: places[10:20]                                              │
│  • Day 3: places[20:30]                                              │
│                                                                       │
│  For each day, create DayItinerary:                                  │
│  • Calculate total_distance                                          │
│  • Estimate costs (meals + transport + activities)                   │
│  • Format start times                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FINAL TOUR OUTPUT                                │
│                                                                       │
│  TourRecommendation:                                                 │
│  {                                                                    │
│    tour_id: "bangkok_tour_abc123",                                   │
│    destination: "Bangkok",                                           │
│    duration_days: 3,                                                 │
│    itinerary: [                                                      │
│      {                                                                │
│        day_number: 1,                                                │
│        date: "2025-12-01",                                           │
│        places: [                                                     │
│          {                                                            │
│            name: "Grand Palace",                                     │
│            start_time: "09:00",                                      │
│            duration_hours: 2.5,                                      │
│            time_block: "morning",                                    │
│            rating: 4.8,                                              │
│            score: 0.892,                                             │
│            transport_to_next: "taxi",                                │
│            distance_to_next_km: 3.5                                  │
│          },                                                           │
│          ...                                                          │
│        ],                                                             │
│        total_distance_km: 15.3,                                      │
│        estimated_cost: 85.0                                          │
│      },                                                               │
│      ...                                                              │
│    ],                                                                 │
│    total_cost_usd: 850.0                                             │
│  }                                                                    │
│                                                                       │
│  Export to JSON → Send to Frontend                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## Algorithm Details

### Content-Based Score Calculation

```python
# Step 1: Create place embedding
place_vector = [
    type_encoding[0..n],      # Multi-hot: [0,1,0,1,0,...]
    rating / 5.0,              # Normalized: 0.0-1.0
    price_level / 4.0,         # Normalized: 0.0-1.0
    log(popularity) / 10.0     # Log-scaled: 0.0-1.0
]

# Step 2: Create user vector from selections
user_vector = weighted_average([
    place_vector for place in selected_places
])

# Step 3: Calculate similarity
content_score = cosine_similarity(user_vector, place_vector)
                + (rating / 5.0) × 0.2  # Rating boost
```

### Collaborative Score Calculation

```python
# Step 1: Build User-Item matrix
UI_matrix[user_i, place_j] = rating if exists else 0

# Step 2: Matrix Factorization (ALS)
for iteration in range(15):
    # Fix item_factors, solve for user_factors
    user_factors = solve_least_squares(UI_matrix, item_factors)
    
    # Fix user_factors, solve for item_factors
    item_factors = solve_least_squares(UI_matrix.T, user_factors)

# Step 3: Predict rating
predicted_rating = dot(user_factors[user_i], item_factors[place_j])
collab_score = predicted_rating / 5.0  # Normalize to 0-1
```

### Greedy Score Calculation

```python
for place in candidate_places:
    # Get travel time from current location
    travel_time = distance_to(current_location, place) / transport_speed
    
    # Set beta based on user selection
    beta = 0 if place in user_selected else config.DEFAULT_BETA
    
    # Calculate greedy score
    greedy_score = (place.rating / 5.0) × hybrid_score[place]
                   - beta × travel_time
    
    # Select place with max score
    best_place = argmax(greedy_score)
```

## Time Complexity

- **Content-based filtering**: O(n × d) where n=places, d=embedding_dim
- **Collaborative filtering**: O(k × m × n) where k=iterations, m=users, n=places
- **Distance calculation**: O(n²) for n places
- **Greedy scheduling**: O(b × n) where b=time_blocks, n=places
- **Overall**: O(n²) dominated by distance calculation

## Space Complexity

- **Place embeddings**: O(n × d)
- **User-Item matrix**: O(m × n) sparse
- **Factor matrices**: O((m+n) × k) where k=latent_factors
- **Distance matrix**: O(n²)
- **Overall**: O(n²) dominated by distance matrix

## Performance Optimizations

1. **Caching**: Distance calculations cached
2. **Sparse Matrix**: Use scipy.sparse for U-I matrix
3. **Vectorization**: NumPy operations instead of loops
4. **Early Stopping**: ALS convergence check
5. **Top-K Selection**: Only process top candidates

---

Created by Smart Travel Team
