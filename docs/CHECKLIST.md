# 🎯 PRE-DEPLOYMENT CHECKLIST

Sử dụng checklist này để verify hệ thống ready cho production.

---

## 📦 FILES & STRUCTURE

### Core API Files
- [x] `api/main.py` - FastAPI app với middleware, CORS, exception handling
- [x] `api/routes/itinerary.py` - POST /generate-itinerary endpoint
- [x] `api/routes/recommendation.py` - POST /recommendations endpoint
- [x] `api/schemas/request.py` - Pydantic request models với validators
- [x] `api/schemas/response.py` - Pydantic response models

### Configuration Files
- [x] `configs/settings.py` - Pydantic settings class
- [x] `.env.example` - Environment template với tất cả variables
- [ ] `.env` - **Tạo từ .env.example và update MONGODB_URI**

### Deployment Files
- [x] `deployment/Dockerfile` - Container image cho API
- [x] `deployment/docker-compose.yml` - Multi-service orchestration
- [x] `deployment/requirements-api.txt` - Python dependencies

### Documentation
- [x] `README.md` - Tổng quan hệ thống, quick start
- [x] `docs/API_DOCUMENTATION.md` - Endpoint reference
- [x] `docs/INSTALLATION_GUIDE.md` - Setup & deployment guide
- [x] `docs/INTEGRATION_GUIDE.md` - Web integration examples
- [x] `HANDOVER.md` - Hướng dẫn bàn giao
- [x] `QUICK_START.md` - 5-minute setup guide

### Testing & Scripts
- [x] `test_api.py` - Automated API testing script
- [x] `start.ps1` - PowerShell quick-start script

---

## 🔧 CONFIGURATION VALIDATION

### .env File (CRITICAL)
```bash
# Verify these variables exist:
- [ ] APP_NAME
- [ ] DEBUG
- [ ] MONGODB_URI (⚠️ MUST UPDATE THIS!)
- [ ] MONGODB_DB_NAME
- [ ] BERT_MODEL_NAME
- [ ] BERT_CACHE_DIR
- [ ] CORS_ORIGINS
- [ ] MAX_REQUEST_SIZE_MB
```

### MongoDB Connection
- [ ] MongoDB URI format correct: `mongodb://host:port/database`
- [ ] Database có collections: `places`, `tours`
- [ ] Places collection có >= 60 documents
- [ ] Tours collection có >= 678 documents

---

## 🐳 DOCKER VALIDATION

### Docker Desktop
- [ ] Docker Desktop installed
- [ ] Docker daemon running (`docker ps` works)
- [ ] Docker Compose available (`docker-compose --version`)

### Docker Compose Services
```bash
cd deployment
docker-compose config  # Validate YAML syntax
```

- [ ] `docker-compose.yml` syntax valid
- [ ] Port 8000 không bị conflict
- [ ] Port 27017 không bị conflict (MongoDB)
- [ ] Port 8081 không bị conflict (Mongo Express)

---

## 🚀 DEPLOYMENT TEST

### 1. Start Services
```bash
cd deployment
docker-compose up -d
```

**Expected output:**
```
Creating network "deployment_default" with the default driver
Creating travel-recommendation-mongo ... done
Creating travel-recommendation-api   ... done
Creating travel-recommendation-mongo-express ... done
```

### 2. Check Container Status
```bash
docker ps
```

**Expected:**
- 3 containers running
- `travel-recommendation-api` - Healthy
- `travel-recommendation-mongo` - Up
- `travel-recommendation-mongo-express` - Up

### 3. Check Logs
```bash
docker logs travel-recommendation-api
```

**Expected:**
- No error messages
- "Application startup complete"
- "Uvicorn running on http://0.0.0.0:8000"

---

## 🧪 FUNCTIONAL TESTING

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{
  "status": "ok",
  "timestamp": "2024-03-15T10:30:00"
}
```

- [ ] Status code: 200
- [ ] Response có `status: "ok"`
- [ ] Response time < 1s

### 2. Swagger UI
Open: http://localhost:8000/docs

- [ ] Swagger UI loads
- [ ] 2 endpoints visible:
  - POST /api/v1/generate-itinerary
  - POST /api/v1/recommendations
- [ ] "Try it out" button works

### 3. Generate Itinerary Test
```bash
curl -X POST http://localhost:8000/api/v1/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Ho Chi Minh",
    "start_date": "2024-03-20",
    "num_days": 3,
    "budget": 5000000,
    "travel_party": "couple",
    "interests": ["food", "culture"]
  }'
```

**Expected:**
- [ ] Status code: 200
- [ ] Response có `tour_id`
- [ ] Response có `days` array với 3 elements
- [ ] Response time: 5-45s (first run slow, then fast)

### 4. Recommendations Test
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Ho Chi Minh",
    "interests": ["shopping", "nightlife"],
    "top_k": 10
  }'
```

**Expected:**
- [ ] Status code: 200
- [ ] Response có `recommendations` array
- [ ] Array length = 10
- [ ] Each item có `name`, `score`, `rating`

### 5. Automated Test Suite
```bash
python test_api.py
```

**Expected:**
- [ ] Health check: ✅ PASSED
- [ ] Generate itinerary: ✅ PASSED
- [ ] Get recommendations: ✅ PASSED
- [ ] 3/3 tests passed

---

## 🌐 INTEGRATION READINESS

### API Response Format
- [x] JSON schema well-defined in response.py
- [x] Nested objects properly structured (days → activities → place)
- [x] All fields documented in API_DOCUMENTATION.md

### CORS Configuration
- [ ] `CORS_ORIGINS` includes frontend URL
- [ ] Frontend có thể gọi API (no CORS errors)

### Error Handling
- [x] Validation errors return 422 với details
- [x] Server errors return 500 với message
- [x] 404 cho routes không tồn tại

### Performance
- [ ] Cold run: 40-50s (acceptable - BERT download)
- [ ] Warm run: 5-10s (acceptable - with cache)
- [ ] BERT cache directory created: `./model_cache/`

---

## 📚 DOCUMENTATION REVIEW

### For Web Team
- [ ] Đọc `QUICK_START.md` - Hiểu cách start API
- [ ] Đọc `HANDOVER.md` - Hiểu cách tích hợp
- [ ] Đọc `docs/API_DOCUMENTATION.md` - Hiểu request/response schema
- [ ] Đọc `docs/INTEGRATION_GUIDE.md` - Có code examples để copy

### For DevOps
- [ ] Đọc `docs/INSTALLATION_GUIDE.md` section "Production Deployment"
- [ ] Biết cách deploy với PM2 hoặc systemd (nếu không dùng Docker)

---

## 🎉 FINAL CHECKLIST

### Pre-Deployment
- [ ] All files created & committed to repo
- [ ] `.env` configured với MongoDB URI đúng
- [ ] Docker Compose starts successfully
- [ ] All 3 automated tests pass
- [ ] Swagger UI accessible at /docs

### Ready for Web Team
- [ ] Documentation complete (README + 4 docs files)
- [ ] Test script works (`python test_api.py`)
- [ ] Example cURL commands work
- [ ] Integration examples provided (Flask + React)

### Production Readiness
- [ ] Docker images built successfully
- [ ] Health check endpoint responsive
- [ ] MongoDB data populated (60 places, 678 tours)
- [ ] BERT model cached after first run
- [ ] Logs không có errors

---

## ✅ SIGN OFF

**Completed by:** ________________  
**Date:** ________________  
**Notes:**

```
Summary:
- API files: ✅ Complete
- Docker setup: ✅ Working
- Documentation: ✅ Comprehensive
- Testing: ✅ Automated
- Web integration: ✅ Examples provided

Status: READY FOR HANDOVER
```

---

## 🐛 If Any Item Fails

1. **Docker won't start**: Xem `QUICK_START.md` → "Docker daemon not running"
2. **API returns errors**: Check `docker logs travel-recommendation-api`
3. **Tests fail**: Xem `docs/INSTALLATION_GUIDE.md` → Troubleshooting
4. **CORS errors**: Update `CORS_ORIGINS` trong `.env`
5. **Slow performance**: Normal! First run downloads BERT model

**Need help?** Check all documentation files first!
