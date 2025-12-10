# 🚀 Installation Guide

## Prerequisites

- **Python**: 3.10 or higher
- **MongoDB**: 6.0 or higher (local or Atlas)
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: ~2GB for BERT model cache

---

## Installation Options

### Option 1: Docker (Recommended for Production)

**Fastest setup - Everything in containers!**

#### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/travel-recommendation-api.git
cd travel-recommendation-api
```

#### Step 2: Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

#### Step 3: Start Services
```bash
cd deployment
docker-compose up -d
```

This will start:
- API server on `http://localhost:8000`
- MongoDB on `localhost:27017`
- Mongo Express (DB UI) on `http://localhost:8081`

#### Step 4: Check Health
```bash
curl http://localhost:8000/health
```

**Done!** API is ready at `http://localhost:8000/docs`

---

### Option 2: Local Development Setup

**For development and testing**

#### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/travel-recommendation-api.git
cd travel-recommendation-api
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r deployment/requirements-api.txt
```

#### Step 4: Setup MongoDB

**Option A - Local MongoDB:**
```bash
# Install MongoDB Community Edition
# Windows: https://www.mongodb.com/try/download/community
# Mac: brew install mongodb-community
# Linux: sudo apt install mongodb

# Start MongoDB
mongod --dbpath /path/to/data
```

**Option B - MongoDB Atlas (Cloud):**
1. Create free cluster at https://www.mongodb.com/cloud/atlas
2. Get connection string
3. Update `MONGODB_URI` in `.env`

#### Step 5: Configure Environment
```bash
cp .env.example .env

# Edit .env
nano .env
```

Required settings:
```env
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=smart_travel
```

#### Step 6: Import Sample Data (Optional)
```bash
# If you have sample data
mongoimport --db smart_travel --collection places --file data/places.json
```

#### Step 7: Start API Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 8: Verify Installation
Open browser: `http://localhost:8000/docs`

---

## Configuration

### Environment Variables

Edit `.env` file:

```env
# Application
APP_NAME=Smart Travel Recommendation API
DEBUG=false

# Database
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=smart_travel

# BERT Model (auto-downloads on first run)
BERT_MODEL_NAME=paraphrase-multilingual-mpnet-base-v2
BERT_CACHE_DIR=./cache/bert_embeddings

# CORS (for web frontend)
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com
```

---

## First Run

### What happens on first run:
1. BERT model downloads (~500MB) - takes 2-5 minutes
2. Model caches to `BERT_CACHE_DIR`
3. First recommendation computes embeddings (~40s)
4. Subsequent requests use cache (~5s)

### Testing First Request
```bash
curl -X POST "http://localhost:8000/api/v1/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Ho Chi Minh City",
    "interests": ["culture"],
    "num_recommendations": 10
  }'
```

**Expected:** 40-50 seconds first time, then 1-3 seconds.

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
```bash
# Make sure you're in virtual environment
# Reinstall dependencies
pip install -r deployment/requirements-api.txt
```

### Issue: "MongoDB connection refused"
```bash
# Check MongoDB is running
mongosh  # or mongo

# Check connection string in .env
# Local: mongodb://localhost:27017/
# Atlas: mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>
```

### Issue: "BERT model download fails"
```bash
# Manual download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"
```

### Issue: "Out of memory"
```bash
# Reduce batch size in code
# Or increase Docker memory limit
docker-compose --compatibility up -d
```

### Issue: "CORS errors from frontend"
```bash
# Add frontend URL to .env
CORS_ORIGINS=http://localhost:3000
```

---

## Production Deployment

### Using Docker Compose (Recommended)
```bash
# Production compose file
docker-compose -f deployment/docker-compose.yml up -d

# With auto-restart
docker-compose up -d --restart=always
```

### Using PM2 (Node.js)
```bash
npm install -g pm2
pm2 start "uvicorn api.main:app --host 0.0.0.0 --port 8000" --name travel-api
```

### Using systemd (Linux)
Create `/etc/systemd/system/travel-api.service`:
```ini
[Unit]
Description=Travel Recommendation API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app/travel-recommendation-api
Environment="PATH=/app/travel-recommendation-api/.venv/bin"
ExecStart=/app/travel-recommendation-api/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable travel-api
sudo systemctl start travel-api
```

---

## Monitoring

### Check API Status
```bash
curl http://localhost:8000/health
```

### View Logs (Docker)
```bash
docker-compose logs -f api
```

### View Logs (Local)
```bash
# Logs are printed to stdout
# Or redirect to file:
uvicorn api.main:app --log-config logging.conf >> api.log 2>&1
```

---

## Updating

### Docker
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Local
```bash
git pull
pip install -r deployment/requirements-api.txt
# Restart server
```

---

## Uninstallation

### Docker
```bash
docker-compose down -v  # Remove containers and volumes
```

### Local
```bash
deactivate  # Exit venv
rm -rf .venv
```

---

## Next Steps

- Read [Integration Guide](INTEGRATION_GUIDE.md) for Web team
- Check [API Documentation](API_DOCUMENTATION.md) for endpoints
- Import your place data to MongoDB
- Configure production settings
