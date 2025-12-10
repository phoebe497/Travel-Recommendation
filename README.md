# Smart Travel Recommendation System 🌍

A production-ready REST API for personalized travel itinerary generation using **BERT Embeddings**, **Collaborative Filtering**, and **Intelligent Scheduling**.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.108.0-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green.svg)](https://www.mongodb.com/)

## 🚀 Quick Start (3 Minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd Travel-Recommendation

# Start services with Docker
cd deployment
docker-compose up -d

# API available at: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

## 🎯 Overview

This system generates personalized multi-day tour itineraries by:

1. **Hybrid Recommendation** - BERT semantic embeddings + SVD collaborative filtering
2. **Intelligent Scheduling** - Greedy algorithm optimizes place visits within time blocks
3. **Route Optimization** - Dijkstra pathfinding minimizes travel time
4. **Time-Block Planning** - Morning, lunch, afternoon, dinner scheduling
5. **REST API** - Production-ready FastAPI with Docker deployment

## 🏗️ System Architecture

```
User Request (REST API)
       ↓
┌──────────────────────────────────────┐
│    FastAPI Endpoint Handler          │
│  • Request validation (Pydantic)     │
│  • Authentication & rate limiting    │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│   BERT Content-Based Filtering       │
│  • Multilingual semantic embeddings  │
│  • Cosine similarity scoring         │
│  • Cache: 700x speedup (warm run)    │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│   SVD Collaborative Filtering        │
│  • Matrix factorization (678 tours)  │
│  • User-item predicted ratings       │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│       Hybrid Scoring (α-blend)       │
│  score = α×BERT + (1-α)×SVD          │
│  Dynamic α based on user selections  │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│     Greedy Scheduling Algorithm      │
│  • Time-block assignment (6 blocks)  │
│  • Rating × HybridScore - β×Distance │
│  • Handles must-visit constraints    │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│    Dijkstra Route Optimization       │
│  • Shortest path between places      │
│  • Travel time/cost calculation      │
└──────────────────┬───────────────────┘
                   ↓
┌──────────────────────────────────────┐
│   JSON Response (Itinerary)          │
│  • Day-by-day schedule               │
│  • Place details + transport info    │
│  • Cost estimates per day            │
└──────────────────────────────────────┘
```

## 📡 API Endpoints

### 1. Generate Complete Itinerary
```http
POST /api/v1/generate-itinerary
Content-Type: application/json

{
  "destination": "Ho Chi Minh",
  "start_date": "2024-03-15",
  "num_days": 3,
  "budget": 5000000,
  "travel_party": "couple",
  "interests": ["nature", "history"],
  "selected_place_ids": ["place_001", "place_002"]
}
```

**Response** (5-48s):
```json
{
  "tour_id": "tour_123",
  "destination": "Ho Chi Minh",
  "total_days": 3,
  "estimated_cost": 4800000,
  "days": [
    {
      "day": 1,
      "date": "2024-03-15",
      "activities": [
        {
          "time_block": "morning",
          "place": {
            "id": "place_001",
            "name": "Ben Thanh Market",
            "rating": 4.5,
            "price_level": 2
          },
          "transport": {
            "mode": "taxi",
            "duration_minutes": 15,
            "cost": 50000
          }
        }
      ]
    }
  ]
}
```

### 2. Get Recommendations Only
```http
POST /api/v1/recommendations
Content-Type: application/json

{
  "destination": "Ho Chi Minh",
  "interests": ["food", "shopping"],
  "top_k": 10
}
```

See **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** for complete reference.

## 📊 Algorithm Details

### BERT Content-Based Filtering
- **Model**: `paraphrase-multilingual-mpnet-base-v2` (768-dim embeddings)
- **Input**: Place name + description + types (Vietnamese/English)
- **Similarity**: Cosine similarity in semantic space
- **Cache**: First run ~45s, subsequent runs ~5s (700x speedup)

### SVD Collaborative Filtering
- **Data**: 678 historical tours from HCM dataset
- **Method**: Singular Value Decomposition for matrix factorization
- **Output**: Predicted ratings for unvisited places

### Hybrid Scoring
```python
hybrid_score = α × bert_score + (1-α) × svd_score
```
**Dynamic α** (adjusts based on user input):
- `α = 0.3`: No selections (trust collaborative data)
- `α = 0.5`: 1-3 selections
- `α = 0.7`: 4-7 selections
- `α = 0.9`: 8+ selections (trust user preferences)

### Greedy Scheduling
```python
greedy_score = place_rating × hybrid_score - β × travel_time
```
- **β = 0**: Must-visit places (no distance penalty)
- **β = 0.1**: Recommended places (minimize travel time)
- **Time Blocks**: Morning (8-11) → Lunch → Afternoon (12-19) → Dinner → Night

### Route Optimization
- **Algorithm**: Dijkstra's shortest path
- **Graph**: All places connected with travel time/cost edges
- **Output**: Optimal transport mode (walk/bus/taxi) between consecutive places

---

## 🚀 Installation & Deployment

### Option 1: Docker (Recommended)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Travel-Recommendation

# 2. Configure environment
cp .env.example .env
# Edit .env with your MongoDB URI

# 3. Start all services
cd deployment
docker-compose up -d

# 4. Check health
curl http://localhost:8000/health
```

**Services**:
- API: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- MongoDB: `localhost:27017`
- Mongo Express: `http://localhost:8081`

### Option 2: Local Development

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r deployment/requirements-api.txt

# 3. Configure environment
cp .env.example .env
# Update MONGODB_URI in .env

# 4. Run API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

See **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** for production deployment (PM2, systemd).

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** | Complete endpoint reference with examples |
| **[INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** | Docker + local + production deployment |
| **[INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** | Web integration patterns (Flask/React) |
| **[PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)** | Speed & accuracy benchmarks |
| **[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** | Technical implementation details |

---

## 🧪 Testing

```bash
# Test generate itinerary endpoint
curl -X POST http://localhost:8000/api/v1/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Ho Chi Minh",
    "start_date": "2024-03-15",
    "num_days": 3,
    "budget": 5000000,
    "travel_party": "couple",
    "interests": ["food", "culture"]
  }'

# Test recommendations endpoint
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Ho Chi Minh",
    "interests": ["shopping", "nightlife"],
    "top_k": 10
  }'
```

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| **Cold Run** (first request) | 43-48 seconds |
| **Warm Run** (cached BERT) | 5-10 seconds |
| **Cache Speedup** | 700-800x |
| **POD** (Percentage of Days) | 32.1% |
| **Precision** | 23.8% |
| **F1-Score** | 0.269 |
| **Places in DB** | 60 (HCM dataset) |
| **Historical Tours** | 678 |

---

## 🔗 Web Integration Example

### Replace Gemini API with This System

**Before** (Gemini):
```python
import google.generativeai as genai

response = genai.generate_content(
    "Create 3-day Ho Chi Minh itinerary"
)
```

**After** (This API):
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/generate-itinerary",
    json={
        "destination": "Ho Chi Minh",
        "num_days": 3,
        "budget": 5000000,
        "travel_party": "couple"
    }
)
itinerary = response.json()
```

See **[docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** for complete Flask/React examples.

---

## 🗂️ Project Structure

```
Travel-Recommendation/
├── api/                          # FastAPI application
│   ├── main.py                   # App entry point
│   ├── routes/                   # API endpoints
│   │   ├── itinerary.py         # POST /generate-itinerary
│   │   └── recommendation.py     # POST /recommendations
│   └── schemas/                  # Pydantic models
│       ├── request.py            # Request validation
│       └── response.py           # Response formatting
├── configs/                      # Configuration
│   └── settings.py               # Pydantic settings (env vars)
├── src/                          # Core algorithms
│   ├── hybrid_recommender.py    # BERT + SVD hybrid
│   ├── smart_itinerary_planner.py  # Scheduling engine
│   └── routing_utils.py          # Dijkstra pathfinding
├── deployment/                   # Deployment files
│   ├── Dockerfile                # API container image
│   ├── docker-compose.yml        # Multi-service setup
│   └── requirements-api.txt      # API dependencies
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── INSTALLATION_GUIDE.md
│   └── INTEGRATION_GUIDE.md
├── benchmarks/                   # Performance testing
│   ├── benchmark_speed.py
│   └── benchmark_accuracy.py
└── .env.example                  # Environment template
```

---

## ⚙️ Configuration

Key environment variables (`.env`):

```bash
# Application
APP_NAME=Smart Travel Recommendation API
DEBUG=false
API_VERSION=v1

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=vietnam_travel

# BERT Model
BERT_MODEL_NAME=paraphrase-multilingual-mpnet-base-v2
BERT_CACHE_DIR=./model_cache

# API Security
CORS_ORIGINS=["http://localhost:3000"]
MAX_REQUEST_SIZE_MB=10

# Rate Limiting (optional)
RATE_LIMIT_PER_MINUTE=60
```

---

## 🛠️ Development

### Run Tests
```bash
# Speed benchmark (6-step pipeline timing)
python benchmarks/benchmark_speed.py

# Accuracy benchmark (POD, Precision, Recall, F1)
python benchmarks/benchmark_accuracy.py
```

### Code Structure
- `src/bert_recommender.py`: Semantic similarity with multilingual BERT
- `src/collaborative_recommender.py`: SVD matrix factorization  
- `src/hybrid_recommender.py`: Alpha-blended scoring
- `src/scheduling_algorithm.py`: Greedy time-block scheduler
- `src/routing_utils.py`: Dijkstra shortest path
- `src/smart_itinerary_planner.py`: Main orchestrator (6-step pipeline)

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check MongoDB connection
docker ps | grep mongo

# View API logs
docker logs travel-recommendation-api

# Test health endpoint
curl http://localhost:8000/health
```

### BERT model download slow
- First run downloads 420MB model
- Subsequent runs use cache (`./model_cache/`)
- Cold run: ~45s, Warm run: ~5s

### Port already in use
```bash
# Change port in docker-compose.yml
services:
  api:
    ports:
      - "8080:8000"  # Host:Container
```

See **[docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)** for more issues.

---

## 📝 License

MIT License - See LICENSE file

---

## 👥 Contributors

Developed as part of Travel Recommendation System research project.

---

## 📞 Support

- **API Issues**: Check [docs/INSTALLATION_GUIDE.md](docs/INSTALLATION_GUIDE.md)
- **Integration Help**: Check [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)
- **Performance Questions**: Check [docs/PERFORMANCE_REPORT.md](docs/PERFORMANCE_REPORT.md)

---

**Ready to integrate?** Start with `docker-compose up -d` and visit `http://localhost:8000/docs` 🚀
  "tour_id": "bangkok_tour_abc123",
  "destination": "Bangkok",
  "duration_days": 3,
  "itinerary": [
    {
      "day_number": 1,
      "date": "2025-12-01",
      "places": [
        {
          "place_id": "ChIJ...",
          "name": "Grand Palace",
          "start_time": "09:00",
          "duration_hours": 2.5,
          "time_block": "morning",
          "rating": 4.8,
          "transport_to_next": "taxi",
          "distance_to_next_km": 3.5,
          "travel_time_hours": 0.12
        }
      ],
      "total_distance_km": 15.3,
      "estimated_cost": 85.00
    }
  ],
  "total_cost_usd": 850.00
}
```

## 🎓 Algorithm Improvements

Potential enhancements:

1. **Deep Learning**: Use neural networks for embedding learning
2. **Reinforcement Learning**: Optimize scheduling with RL agents
3. **Real-time Traffic**: Integrate real-time traffic data
4. **Weather Awareness**: Adjust recommendations based on weather
5. **Social Preferences**: Consider group dynamics for multi-traveler tours

## 📄 License

MIT License - See LICENSE file for details

## 👥 Contributors

Smart Travel Team

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This system requires MongoDB to be running and populated with place data. Use the provided database schema to structure your data correctly.