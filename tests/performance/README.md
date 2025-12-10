# Performance Testing Module

Module đánh giá hiệu suất hệ thống Smart Itinerary Planner (Recommendation + Scheduling).

## 📁 Cấu trúc

```
tests/performance/
├── __init__.py                      # Package init
├── benchmark_speed.py               # Đo tốc độ từng bước của pipeline
├── evaluate_recommendation.py       # Đánh giá độ chính xác recommendation
├── run_performance_tests.py         # Script chạy tất cả tests
└── reports/                         # Folder chứa kết quả
    ├── speed_benchmark_*.json
    ├── evaluation_*.json
    └── performance_summary_*.json
```

## 🚀 Cách sử dụng

### 1. Chạy tất cả tests

```bash
cd tests/performance
python run_performance_tests.py
```

### 2. Chạy từng test riêng lẻ

**Speed Benchmark:**
```bash
python benchmark_speed.py
```

**Recommendation Evaluation:**
```bash
python evaluate_recommendation.py
```

## 📊 Các metrics được đo

### A. Speed Benchmark

Đo thời gian từng bước của pipeline:

1. **Load Places** - Tải dữ liệu từ MongoDB
2. **BERT Embeddings** - Precompute semantic embeddings
3. **Hybrid Scoring** - Tính điểm BERT + SVD
4. **Graph Building** - Xây dựng đồ thị & Dijkstra preprocessing
5. **Scheduling** - Sắp xếp lịch trình (Greedy Block Scheduling)
6. **Route Optimization** - Tối ưu transport mode

**Output:**
- Thời gian từng bước (seconds)
- Tỷ lệ phần trăm của mỗi bước
- Tổng thời gian recommendation (không tính I/O)
- Throughput (places/second)
- Scalability test với 50, 100, 200 places

### B. Recommendation Quality Evaluation

Đánh giá độ chính xác bằng binary classification metrics:

**Ground Truth:** Places mà users đã từng chọn trong tour history

**Predictions:** Top-K recommendations từ hệ thống

**Metrics:**
- **TP** (True Positives): Recommend đúng (user thích)
- **FP** (False Positives): Recommend sai (user không thích)
- **FN** (False Negatives): Bỏ sót (user thích nhưng không recommend)
- **TN** (True Negatives): Đúng không recommend
- **POD** (Probability of Detection) = Recall = TP/(TP+FN)
- **Precision** = TP/(TP+FP)
- **F1-Score** = 2 * (Precision * Recall) / (Precision + Recall)
- **FAR** (False Alarm Rate) = FP/(FP+TN)

## 📋 Yêu cầu

- MongoDB đang chạy với data đã import
- Collections cần thiết:
  - `places` - Danh sách địa điểm
  - `tours` - Tour history (để làm ground truth)
- Virtual environment đã được activate

## 📈 Kết quả mẫu

### Speed Benchmark
```
1_load_places                : 0.234s (5.2%)
2_bert_embeddings            : 1.456s (32.1%)
3_hybrid_scoring             : 0.892s (19.7%)
4_graph_building             : 1.123s (24.8%)
5_scheduling                 : 0.567s (12.5%)
6_route_optimization         : 0.256s (5.7%)
--------------------------------------------
TOTAL RECOMMENDATION TIME    : 4.528s
```

### Recommendation Evaluation
```
TP: 8.2    FP: 11.8    FN: 6.3    TN: 173.7

POD (Recall)    : 0.565 (56.5%)
Precision       : 0.410 (41.0%)
F1-Score        : 0.476
FAR             : 0.064 (6.4%)
```

## 🎯 Giải thích Metrics

- **POD cao** = Hệ thống recommend được nhiều places user thích
- **Precision cao** = Hệ thống ít recommend nhầm places user không thích
- **F1 cao** = Cân bằng tốt giữa POD và Precision
- **FAR thấp** = Tỷ lệ false alarm thấp (tốt)

## 🔧 Tùy chỉnh

Trong `run_performance_tests.py`, có thể thay đổi:

```python
# Thay đổi thành phố test
run_all_performance_tests(city="Ha Noi")

# Trong benchmark_speed.py
benchmark.benchmark_full_pipeline(
    city="Ho Chi Minh City",
    num_days=5,           # Số ngày
    max_places=500        # Số places
)

# Trong evaluate_recommendation.py
evaluator.evaluate_with_tour_history(
    city="Ho Chi Minh City",
    k_recommendations=30  # Top-K
)
```
