# ⚡ QUICK START GUIDE - 5 PHÚT ĐỂ CHẠY API

## Bước 1: Cài Docker Desktop (Nếu Chưa Có)

### Windows
1. Download: https://www.docker.com/products/docker-desktop
2. Cài đặt và restart máy
3. Mở Docker Desktop → đợi logo Docker hiện màu xanh

### Verify Docker
```powershell
docker --version
docker ps
```

---

## Bước 2: Start API (1 Lệnh)

### Option A: PowerShell Script (Recommended)
```powershell
cd d:\AIRC\Travel-Recommendation
.\start.ps1
```

### Option B: Manual Docker Compose
```bash
cd deployment
docker-compose up -d
```

**Đợi 2-5 phút** (lần đầu tải images)

---

## Bước 3: Test API

### 3.1 Health Check (Browser)
Mở trình duyệt: http://localhost:8000/health

Kết quả mong đợi:
```json
{
  "status": "ok",
  "timestamp": "2024-03-15T10:30:00"
}
```

### 3.2 Swagger UI
Mở: http://localhost:8000/docs

**Try it out:**
1. Click "POST /api/v1/generate-itinerary"
2. Click "Try it out"
3. Dùng payload này:
```json
{
  "destination": "Ho Chi Minh",
  "start_date": "2024-03-20",
  "num_days": 3,
  "budget": 5000000,
  "travel_party": "couple",
  "interests": ["food", "culture"]
}
```
4. Click "Execute"
5. Đợi 5-45s (lần đầu chậm, lần sau nhanh)

### 3.3 Automated Test Script
```bash
pip install requests
python test_api.py
```

---

## Bước 4: Tích Hợp Vào Web

### Frontend React Code
```javascript
const response = await fetch('http://localhost:8000/api/v1/generate-itinerary', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    destination: "Ho Chi Minh",
    start_date: "2024-03-20",
    num_days: 3,
    budget: 5000000,
    travel_party: "couple",
    interests: ["food", "shopping"]
  })
});

const itinerary = await response.json();
console.log(itinerary.days);
```

---

## 🛠️ Commands Thường Dùng

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker logs travel-recommendation-api
docker logs travel-recommendation-api --follow  # Real-time
```

### Restart API Only
```bash
docker-compose restart api
```

### Check Status
```bash
docker ps
```

---

## 🌐 Endpoints

| Service | URL |
|---------|-----|
| **API** | http://localhost:8000 |
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **MongoDB** | localhost:27017 |
| **Mongo Express** | http://localhost:8081 |

---

## 🐛 Common Issues

### "Docker daemon not running"
```bash
# Windows: Mở Docker Desktop app
# Đợi logo xanh
```

### Port 8000 đã bị dùng
```bash
# Tìm process đang dùng
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Hoặc đổi port trong docker-compose.yml
ports:
  - "8080:8000"  # External:Internal
```

### MongoDB connection failed
```bash
# Check .env file
MONGODB_URI=mongodb://mongo:27017/vietnam_travel

# Restart MongoDB
docker-compose restart mongo
```

### API chậm (>40s)
- **Lần đầu**: Tải BERT model 420MB → chậm
- **Lần sau**: Cache → nhanh ~5s
- **Normal behavior!**

---

## 📚 Chi Tiết Hơn?

| Document | Content |
|----------|---------|
| **HANDOVER.md** | Hướng dẫn bàn giao cho Web team |
| **docs/API_DOCUMENTATION.md** | Endpoints, schemas, examples |
| **docs/INSTALLATION_GUIDE.md** | Production deployment |
| **docs/INTEGRATION_GUIDE.md** | Flask/React code examples |

---

## ✅ Checklist

- [ ] Docker Desktop installed & running
- [ ] `docker-compose up -d` success
- [ ] http://localhost:8000/health returns OK
- [ ] http://localhost:8000/docs loads Swagger UI
- [ ] `python test_api.py` passes all tests
- [ ] Frontend có thể gọi API endpoint

**Done?** → Đọc `HANDOVER.md` để tích hợp vào web! 🚀
