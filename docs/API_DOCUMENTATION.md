# 📚 API Documentation

## Overview
Smart Travel Recommendation API provides AI-powered travel itinerary generation using advanced machine learning algorithms (BERT + SVD + Dijkstra).

**Base URL:** `http://your-server.com/api/v1`

**API Documentation:** `http://your-server.com/docs` (Swagger UI)

---

## Authentication (Optional)

If `ENABLE_API_KEY_AUTH=true`, include API key in header:
```
X-API-Key: your_secret_key
```

---

## Endpoints

### 1. Generate Complete Itinerary

**Endpoint:** `POST /api/v1/generate-itinerary`

**Description:** Generate a complete personalized travel itinerary with scheduled places, transport, and costs.

**Request Body:**
```json
{
  "city": "Ho Chi Minh City",
  "num_days": 3,
  "start_date": "2025-12-20",
  "interests": ["culture", "food", "nature"],
  "budget": "medium",
  "travel_party": "solo",
  "accommodation_type": "hotel",
  "selected_place_ids": [],
  "hotel_place_id": null
}
```

**Request Fields:**
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `city` | string | ✅ | Destination city name | "Singapore" |
| `num_days` | integer | ✅ | Number of days (1-14) | 3 |
| `start_date` | string | ✅ | Start date (YYYY-MM-DD) | "2025-12-20" |
| `interests` | array[string] | ❌ | User interests | ["landmarks", "food"] |
| `budget` | string | ❌ | Budget: low, medium, high | "medium" |
| `travel_party` | string | ❌ | Party: solo, couple, family, friends | "couple" |
| `accommodation_type` | string | ❌ | Type: hotel, hostel, resort | "hotel" |
| `selected_place_ids` | array[string] | ❌ | Pre-selected place IDs | [] |
| `hotel_place_id` | string | ❌ | Specific hotel ID | null |

**Response (200 OK):**
```json
{
  "destination": "Ho Chi Minh City",
  "start_date": "2025-12-20",
  "duration_days": 3,
  "daily_itineraries": [
    {
      "day": 1,
      "date": "2025-12-20",
      "places": [
        {
          "place_id": "ChIJ...",
          "name": "Ben Thanh Market",
          "rating": 4.3,
          "price_level": 2,
          "types": ["market", "tourist_attraction"],
          "arrival_time": "09:00",
          "departure_time": "11:30",
          "visit_duration_hours": 2.5,
          "estimated_cost_usd": 20.0,
          "transport_to_next": {
            "mode": "walking",
            "distance_km": 1.2,
            "duration_minutes": 14.4,
            "cost_usd": 0.0
          }
        }
      ],
      "total_places": 8,
      "total_cost_usd": 85.50,
      "total_distance_km": 12.3,
      "total_duration_hours": 10.5
    }
  ],
  "total_places": 24,
  "total_cost_usd": 256.80,
  "total_distance_km": 38.7,
  "processing_time_ms": 7890,
  "generated_at": "2025-12-11T10:30:00"
}
```

**Error Responses:**
- `400`: Invalid request parameters
- `404`: City not found or no places available
- `500`: Server error

---

### 2. Get Place Recommendations (No Scheduling)

**Endpoint:** `POST /api/v1/recommendations`

**Description:** Get Top-K place recommendations without scheduling. Useful for showing options to users.

**Request Body:**
```json
{
  "city": "Bangkok",
  "interests": ["temples", "food", "markets"],
  "num_recommendations": 20,
  "selected_place_ids": null
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `city` | string | ✅ | Destination city |
| `interests` | array[string] | ❌ | User interests |
| `num_recommendations` | integer | ❌ | Number to return (5-50, default 20) |
| `selected_place_ids` | array[string] | ❌ | Pre-selected places |

**Response (200 OK):**
```json
{
  "city": "Bangkok",
  "total_candidates": 150,
  "recommendations": [
    {
      "place_id": "ChIJ...",
      "name": "Wat Pho",
      "rating": 4.7,
      "price_level": 1,
      "types": ["temple", "tourist_attraction", "place_of_worship"],
      "score": 0.9234,
      "avg_price_usd": 5.50
    }
  ],
  "processing_time_ms": 1200
}
```

---

## Response Time

| Scenario | Expected Time |
|----------|---------------|
| First request (cold start) | 40-50 seconds |
| Subsequent requests (cached) | 5-10 seconds |
| Recommendations only | 1-3 seconds |

**Why cold start is slow:** BERT model loading + embedding computation. After caching, ~700x faster.

---

## Rate Limiting

(Optional - not implemented by default)

To add rate limiting, use middleware or reverse proxy (nginx/traefik).

---

## CORS

By default, CORS allows all origins (`*`). For production, set specific domains in `.env`:
```
CORS_ORIGINS=https://your-frontend.com,https://app.your-domain.com
```

---

## Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": 1702297800.123
}
```

---

## Testing with cURL

### Generate Itinerary
```bash
curl -X POST "http://localhost:8000/api/v1/generate-itinerary" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Singapore",
    "num_days": 3,
    "start_date": "2025-12-20",
    "interests": ["landmarks", "food"],
    "budget": "medium"
  }'
```

### Get Recommendations
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Bangkok",
    "interests": ["temples"],
    "num_recommendations": 10
  }'
```

---

## Interactive Documentation

Visit `http://your-server:8000/docs` for interactive Swagger UI where you can:
- See all endpoints
- Try API calls directly
- View request/response schemas
- Download OpenAPI spec

---

## Error Handling

All errors return JSON with this format:
```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {...}
}
```

**Common Error Codes:**
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: City not found / No places
- `500 Internal Server Error`: Server issue
- `503 Service Unavailable`: Database connection failed
