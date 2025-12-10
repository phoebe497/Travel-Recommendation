# 🐳 Docker Deployment

This folder contains Docker deployment files for the Travel Recommendation API.

## 📦 Files

- **`Dockerfile`**: Container image definition for the API service
- **`docker-compose.yml`**: Multi-service orchestration (API + MongoDB + Mongo Express)
- **`requirements-api.txt`**: Python dependencies for the API

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 🌐 Services

| Service | Port | Description |
|---------|------|-------------|
| **api** | 8000 | FastAPI server |
| **mongo** | 27017 | MongoDB database |
| **mongo-express** | 8081 | MongoDB web UI |

## 📝 Environment Variables

Copy `.env.example` to `.env` in the root directory and configure:

```env
MONGODB_URI=mongodb://mongo:27017/vietnam_travel
BERT_MODEL_NAME=paraphrase-multilingual-mpnet-base-v2
BERT_CACHE_DIR=./model_cache
CORS_ORIGINS=["http://localhost:3000"]
```

## 🔧 Troubleshooting

### Port conflicts
Edit `docker-compose.yml` to change ports:
```yaml
services:
  api:
    ports:
      - "8080:8000"  # Change 8080 to any available port
```

### View logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs mongo

# Follow logs in real-time
docker-compose logs -f api
```

### Restart services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Clean rebuild
```bash
docker-compose down -v  # Remove volumes
docker-compose build --no-cache  # Rebuild images
docker-compose up -d
```

## 📚 Full Documentation

See root directory:
- `../QUICK_START.md` - 5-minute setup guide
- `../docs/INSTALLATION_GUIDE.md` - Complete deployment guide
- `../docs/API_DOCUMENTATION.md` - API reference
