# 🚀 Hướng Dẫn Bàn Giao Cho Bên Web

## 📦 Đã Hoàn Thành

### 1. API Backend (FastAPI)
- ✅ 2 endpoints REST API:
  - `POST /api/v1/generate-itinerary` - Tạo lịch trình hoàn chỉnh
  - `POST /api/v1/recommendations` - Lấy danh sách gợi ý địa điểm
- ✅ Validation request với Pydantic
- ✅ Swagger UI tự động tại `/docs`
- ✅ CORS đã cấu hình cho frontend
- ✅ Exception handling toàn diện

### 2. Containerization
- ✅ Dockerfile cho API
- ✅ docker-compose.yml với 3 services:
  - `api`: Backend API (port 8000)
  - `mongo`: MongoDB database (port 27017)
  - `mongo-express`: Web UI quản lý database (port 8081)
- ✅ Volume mounting để persistent data

### 3. Documentation
- ✅ **API_DOCUMENTATION.md**: Chi tiết endpoints, request/response examples
- ✅ **INSTALLATION_GUIDE.md**: Hướng dẫn setup Docker + local + production
- ✅ **INTEGRATION_GUIDE.md**: Code examples cho Flask/React integration
- ✅ **README.md**: Tổng quan hệ thống, quick start

### 4. Testing & Scripts
- ✅ `test_api.py`: Script test tự động cả 2 endpoints
- ✅ `start.ps1`: PowerShell script khởi động nhanh

---

## 🎯 Thay Thế Gemini API Như Thế Nào?

### Hiện Tại (Gemini)
```javascript
// Frontend call
const response = await fetch('https://your-backend.com/api/gemini', {
  method: 'POST',
  body: JSON.stringify({
    prompt: "Create 3-day Ho Chi Minh itinerary for couple, budget 5M"
  })
});
```

### Sau Khi Thay (API Này)
```javascript
// Frontend call
const response = await fetch('http://localhost:8000/api/v1/generate-itinerary', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    destination: "Ho Chi Minh",
    start_date: "2024-03-15",
    num_days: 3,
    budget: 5000000,
    travel_party: "couple",
    interests: ["food", "culture"]
  })
});

const itinerary = await response.json();
// itinerary.days[0].activities[0].place.name
```

**Ưu điểm so với Gemini:**
- ✅ Response cấu trúc rõ ràng (JSON schema cố định)
- ✅ Không phụ thuộc external API (tự host)
- ✅ Không tốn tiền gọi API
- ✅ Data từ database thực (60 places, 678 tours HCM)
- ✅ Tính toán route thực tế (Dijkstra pathfinding)

---

## ⚡ Quick Start (3 Bước)

### 1. Khởi Động Backend
```powershell
# Windows PowerShell
cd Travel-Recommendation
.\start.ps1
```

Hoặc thủ công:
```bash
cd deployment
docker-compose up -d
```

**Services sẽ chạy tại:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- MongoDB: localhost:27017
- Mongo Express: http://localhost:8081

### 2. Test API
```bash
# Cài dependencies
pip install requests

# Chạy test
python test_api.py
```

### 3. Tích Hợp Vào Frontend

#### Option A: Gọi Trực Tiếp Từ Frontend (Development)
```javascript
// React Example
import { useState } from 'react';

function TravelPlanner() {
  const [itinerary, setItinerary] = useState(null);
  
  const generateItinerary = async () => {
    const response = await fetch('http://localhost:8000/api/v1/generate-itinerary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination: "Ho Chi Minh",
        start_date: "2024-03-15",
        num_days: 3,
        budget: 5000000,
        travel_party: "couple",
        interests: ["food", "shopping"]
      })
    });
    
    const data = await response.json();
    setItinerary(data);
  };
  
  return (
    <div>
      <button onClick={generateItinerary}>Generate Itinerary</button>
      {itinerary && (
        <div>
          <h2>{itinerary.destination} - {itinerary.total_days} days</h2>
          {itinerary.days.map(day => (
            <div key={day.day}>
              <h3>Day {day.day}</h3>
              {day.activities.map((act, i) => (
                <p key={i}>{act.time_block}: {act.place.name}</p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### Option B: Proxy Qua Backend Flask (Production)
```python
# Backend Flask - proxy_routes.py
from flask import Blueprint, request, jsonify
import requests

api_bp = Blueprint('api', __name__)

RECOMMENDATION_API = "http://localhost:8000"

@api_bp.route('/api/generate-itinerary', methods=['POST'])
def generate_itinerary():
    """Proxy to ML API"""
    data = request.get_json()
    
    try:
        response = requests.post(
            f"{RECOMMENDATION_API}/api/v1/generate-itinerary",
            json=data,
            timeout=60
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## 📋 Checklist Bàn Giao

### Phía Backend API (Đã Xong)
- [x] FastAPI endpoints hoạt động
- [x] Docker containers start successfully
- [x] MongoDB connection OK
- [x] CORS configured
- [x] Swagger docs accessible
- [x] Test script passes

### Phía Bên Web (Cần Làm)
- [ ] **Chạy test script để verify API hoạt động**
  ```bash
  python test_api.py
  ```

- [ ] **Đọc Integration Guide**
  - File: `docs/INTEGRATION_GUIDE.md`
  - Có code examples cho Flask + React

- [ ] **Update Frontend để gọi API mới**
  - Thay Gemini endpoint bằng `/api/v1/generate-itinerary`
  - Parse response theo schema trong API_DOCUMENTATION.md

- [ ] **Update Backend Flask (nếu có proxy layer)**
  - Thêm routes proxy tới ML API
  - Xem example trong INTEGRATION_GUIDE.md

- [ ] **Environment Variables**
  - Production: Update `CORS_ORIGINS` trong `.env`
  - Thêm domain frontend vào whitelist

- [ ] **Deploy Production**
  - Option 1: Docker Compose trên server
  - Option 2: PM2 cho Python process
  - Xem chi tiết trong INSTALLATION_GUIDE.md

---

## 🔧 Troubleshooting

### API không start được
```bash
# Check Docker
docker ps

# Xem logs
docker logs travel-recommendation-api

# Restart services
cd deployment
docker-compose down
docker-compose up -d
```

### CORS errors từ frontend
```python
# Trong .env
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]
```

### Response chậm (>40s)
- Lần đầu chạy tải BERT model (420MB) → chậm
- Lần sau có cache → nhanh ~5s
- Xem metrics trong PERFORMANCE_REPORT.md

---

## 📞 Liên Hệ & Support

### Documentation Files
1. **API_DOCUMENTATION.md**: Endpoint reference, request/response schemas
2. **INSTALLATION_GUIDE.md**: Setup hướng dẫn chi tiết
3. **INTEGRATION_GUIDE.md**: Code examples Flask/React
4. **PERFORMANCE_REPORT.md**: Benchmarks, metrics

### Test Commands
```bash
# Health check
curl http://localhost:8000/health

# Test generate itinerary
curl -X POST http://localhost:8000/api/v1/generate-itinerary \
  -H "Content-Type: application/json" \
  -d '{"destination":"Ho Chi Minh","num_days":3,"budget":5000000,"travel_party":"couple"}'

# Run automated tests
python test_api.py
```

---

## 🎉 Summary

**Bên Web cần làm gì:**
1. ✅ Chạy `start.ps1` hoặc `docker-compose up -d`
2. ✅ Test với `python test_api.py`
3. ✅ Đọc `docs/INTEGRATION_GUIDE.md`
4. ✅ Update frontend code để gọi API mới
5. ✅ Deploy Docker Compose lên production server

**Timeline ước tính:** 1-2 giờ cho integration + testing

**Contact:** Check INSTALLATION_GUIDE.md nếu gặp vấn đề
