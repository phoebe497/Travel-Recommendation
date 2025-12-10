# Alpha Calculation - Chi Tiết Cách Tính

## 📋 Mục Lục
- [Alpha Là Gì?](#alpha-là-gì)
- [Phương Pháp Tính](#phương-pháp-tính)
- [Total Available Places & Clipping](#total-available-places--clipping)
- [Ví Dụ Thực Tế](#ví-dụ-thực-tế)
- [So Sánh Old vs New](#so-sánh-old-vs-new)

---

## Alpha Là Gì?

**Alpha (α)** là weight giữa **content-based filtering** và **collaborative filtering** trong hybrid recommendation system.

### Công Thức Hybrid Score:
```
hybrid_score = α × content_score + (1-α) × collaborative_score + rating_bonus
```

### Ý Nghĩa:
- **α cao (0.7-0.9)**: Tin **content-based** → Ưu tiên sở thích cá nhân user
- **α thấp (0.3-0.5)**: Tin **collaborative** → Ưu tiên places phổ biến

### Ví Dụ:
```python
# User A: α = 0.3 (cold start)
hybrid_score = 0.3 × content + 0.7 × collaborative
# → 70% dựa vào đánh giá chung, 30% sở thích cá nhân
# → Recommend places hot, phổ biến

# User B: α = 0.9 (nhiều selections)
hybrid_score = 0.9 × content + 0.1 × collaborative  
# → 90% dựa vào sở thích cá nhân, 10% đánh giá chung
# → Recommend places phù hợp với user, dù ít người biết
```

---

## Phương Pháp Tính

### Formula Overview:
```
selection_rate = selected_places / total_available_places
places_per_day = selected_places / trip_duration_days

if selection_rate < 0.5:
    alpha = 0.3 + 0.3 × (selection_rate / 0.5)    # Range: [0.3, 0.6]
else:
    alpha = 0.6 + 0.3 × ((selection_rate - 0.5) / 0.5)    # Range: [0.6, 0.9]

if places_per_day >= 5:
    alpha += 0.05    # Bonus for high engagement

alpha = min(0.9, alpha)    # Cap at 0.9
```

---

### Khoảng 1: Selection Rate < 50%

**Đặc điểm:** User chọn ít → chưa rõ sở thích → dựa collaborative nhiều hơn

**Formula:**
```
α = 0.3 + 0.3 × (rate / 0.5)
```

**Alpha Range:** `[0.3, 0.6]`

**Examples:**

| Selected | Total | Rate | Formula | Alpha | Behavior |
|----------|-------|------|---------|-------|----------|
| 0 | 30 | 0% | Cold start | **0.30** | 70% collaborative |
| 3 | 30 | 10% | 0.3 + 0.3×(0.1/0.5) | **0.36** | 64% collaborative |
| 6 | 30 | 20% | 0.3 + 0.3×(0.2/0.5) | **0.42** | 58% collaborative |
| 10 | 30 | 33% | 0.3 + 0.3×(0.33/0.5) | **0.50** | 50-50 balanced |
| 14 | 30 | 47% | 0.3 + 0.3×(0.47/0.5) | **0.58** | 42% collaborative |
| 15 | 30 | 50% | Threshold | **0.60** | Switch to Khoảng 2 |

---

### Khoảng 2: Selection Rate ≥ 50%

**Đặc điểm:** User chọn nhiều → rõ sở thích → dựa content nhiều hơn

**Formula:**
```
α = 0.6 + 0.3 × ((rate - 0.5) / 0.5)
```

**Alpha Range:** `[0.6, 0.9]`

**Examples:**

| Selected | Total | Rate | Formula | Alpha | Behavior |
|----------|-------|------|---------|-------|----------|
| 15 | 30 | 50% | 0.6 + 0.3×(0/0.5) | **0.60** | Threshold |
| 20 | 30 | 67% | 0.6 + 0.3×(0.17/0.5) | **0.70** | 70% content |
| 25 | 30 | 83% | 0.6 + 0.3×(0.33/0.5) | **0.80** | 80% content |
| 30 | 30 | 100% | 0.6 + 0.3×(0.5/0.5) | **0.90** | 90% content (max) |

---

### Bonus: Places Per Day ≥ 5

**Logic:** User chọn nhiều places/ngày → rất chủ động → tăng alpha

**Bonus:** `+0.05`

**Example:**
```python
# User chọn 15/30 places, 3 days
selection_rate = 15/30 = 0.5
places_per_day = 15/3 = 5.0

# Base alpha:
alpha = 0.6 + 0.3 × (0/0.5) = 0.60

# Bonus (PPD = 5 >= 5):
alpha = 0.60 + 0.05 = 0.65 ✓
```

---

## Total Available Places & Clipping

### ❓ Total Available Places Là Gì?

**KHÔNG PHẢI:** Tổng places trong DB (có thể 5000+)  
**MÀ LÀ:** "Interaction pool" mà user thực tế có thể nhìn thấy và tương tác

### 🎯 Tại Sao Cần Clipping?

User **KHÔNG NHÌN THẤY** hết 5000 places trong DB:
- UI chỉ hiển thị top 100-200 places (sorted by rating, popularity)
- User chỉ browse và chọn từ pool này
- Selection rate phải tính dựa trên "visible pool", không phải toàn bộ DB

### 📏 Clipping Range: [30, 200]

```python
total_available = len(candidate_places)    # DB size: 5-5000
total_available_clipped = max(30, min(200, total_available))
```

---

### MIN = 30: Tránh Over-Personalization

**Vấn đề:**  
Thành phố nhỏ (8 places), user chọn 5:
```
selection_rate = 5/8 = 62.5%
alpha = 0.6 + 0.3 × (0.125/0.5) = 0.68    ❌ Quá cao!
```

**Giải pháp:**  
Clip to 30:
```
selection_rate = 5/30 = 16.7%
alpha = 0.3 + 0.3 × (0.167/0.5) = 0.40    ✓ Hợp lý
```

**Lý do:**  
Ngay cả thành phố nhỏ, user vẫn cần **explore** với collaborative filtering để discover places mới, không chỉ dựa vào 5 places đã chọn.

---

### MAX = 200: Tránh Under-Personalization

**Vấn đề:**  
Thành phố lớn (5000 places), user chọn 14:
```
selection_rate = 14/5000 = 0.28%
alpha = 0.3 + 0.3 × (0.0028/0.5) = 0.30    ❌ Quá thấp!
```

**Giải pháp:**  
Clip to 200:
```
selection_rate = 14/200 = 7%
alpha = 0.3 + 0.3 × (0.07/0.5) = 0.34    ✓ Có personalize
```

**Lý do:**  
- User **KHÔNG nhìn thấy** hết 5000 places
- UI chỉ show top 200 places (by rating)
- User interaction pool ≈ 100-200 places
- `14/200 = 7%` phản ánh engagement thực tế

---

### 📚 Research Support

**Netflix:**  
Users browse ~50-100 titles trong catalog hàng nghìn phim

**Amazon:**  
Users tương tác với ~100-200 sản phẩm per category, dù có hàng triệu items

**Psychology:**  
Choice overload khi > 200 options → user bỏ qua, không tương tác

---

## Ví Dụ Thực Tế

### Scenario 1: Tokyo 🗼

**Context:**  
- DB có **5000 places** → clipped to **200**
- User chọn **14 places**, **3 ngày**

**Calculation:**
```python
selection_rate = 14/200 = 0.07 (7%)
places_per_day = 14/3 = 4.67

# Khoảng 1 (< 50%):
alpha = 0.3 + 0.3 × (0.07/0.5) = 0.34

# No bonus (PPD < 5)
Final: α = 0.34
```

**Ý nghĩa:**  
User **mới explore** Tokyo (chỉ chọn 7% places visible)  
→ Alpha thấp (0.34)  
→ Dựa **66% collaborative**, 34% content  
→ Recommend places **hot**, phổ biến mà nhiều người thích  
→ Tránh recommend places niche mà user chưa sẵn sàng

---

### Scenario 2: Hanoi 🏛️

**Context:**  
- DB có **50 places** → no clipping (trong range [30, 200])
- User chọn **14 places**, **3 ngày**

**Calculation:**
```python
selection_rate = 14/50 = 0.28 (28%)
places_per_day = 14/3 = 4.67

# Khoảng 1 (< 50%):
alpha = 0.3 + 0.3 × (0.28/0.5) = 0.47

# No bonus (PPD < 5)
Final: α = 0.47
```

**Ý nghĩa:**  
User đã chọn **28% places** visible  
→ Alpha cao hơn Tokyo (0.47 vs 0.34)  
→ Dựa **53% collaborative**, 47% content  
→ **Balanced** giữa phổ biến và sở thích cá nhân  
→ User biết rõ sở thích hơn Tokyo user

---

### Scenario 3: Small City 🏘️

**Context:**  
- DB có **8 places** → clipped to **30**
- User chọn **5 places**, **2 ngày**

**Calculation:**
```python
selection_rate = 5/30 = 0.17 (17%)
places_per_day = 5/2 = 2.5

# Khoảng 1 (< 50%):
alpha = 0.3 + 0.3 × (0.17/0.5) = 0.40

# No bonus (PPD < 5)
Final: α = 0.40
```

**Ý nghĩa:**  
Tránh **over-personalize**  
→ Nếu dùng 5/8 = 62% → α = 0.68 (quá cao!)  
→ Clip to 30 → α = 0.40 (hợp lý)  
→ Vẫn có 60% collaborative để explore

---

### Scenario 4: High Engagement User ⚡

**Context:**  
- DB có **100 places** → no clipping
- User chọn **20 places**, **2 ngày** (intense trip!)

**Calculation:**
```python
selection_rate = 20/100 = 0.20 (20%)
places_per_day = 20/2 = 10.0

# Khoảng 1 (< 50%):
alpha_base = 0.3 + 0.3 × (0.20/0.5) = 0.42

# Bonus (PPD = 10 >= 5):
alpha = min(0.9, 0.42 + 0.05) = 0.47

Final: α = 0.47
```

**Ý nghĩa:**  
User **rất chủ động** (10 places/ngày!)  
→ Bonus +0.05  
→ Alpha = 0.47 (cao hơn baseline 0.42)  
→ Personalize nhiều hơn cho power user

---

## So Sánh Old vs New

### Old Method: Threshold-Based

```python
def old_alpha(num_selected):
    if num_selected == 0: return 0.3
    elif num_selected <= 3: return 0.5
    elif num_selected <= 7: return 0.7
    else: return 0.9
```

**Vấn đề:**
- ❌ **Jumps**: 3 places → α=0.5, 4 places → α=0.5, 8 places → α=0.9 (nhảy vọt)
- ❌ **Không xét city size**: 14/50 (Hanoi) = 14/5000 (Tokyo) = α=0.9
- ❌ **Không xét engagement**: 14 places/1 ngày = 14 places/7 ngày = α=0.9

---

### New Method: Selection Rate + PPD

```python
def new_alpha(selected, total_available, days):
    rate = selected / max(30, min(200, total_available))
    ppd = selected / days
    
    if rate < 0.5:
        alpha = 0.3 + 0.3 * (rate / 0.5)
    else:
        alpha = 0.6 + 0.3 * ((rate - 0.5) / 0.5)
    
    if ppd >= 5:
        alpha += 0.05
    
    return min(0.9, alpha)
```

**Ưu điểm:**
- ✅ **Smooth transition**: Linear scaling thay vì jumps
- ✅ **Xét city size**: 14/50 (28%) ≠ 14/200 (7%) → alpha khác nhau
- ✅ **Xét engagement**: 15/3 days (PPD=5) → bonus +0.05
- ✅ **Clipping**: Tránh extremes (over/under-personalization)

---

### Comparison Table: Cùng 14 Selected Places

| City | DB Places | Clipped | Rate | **Old α** | **New α** | Difference |
|------|-----------|---------|------|-----------|-----------|------------|
| **Tokyo** | 5000 | 200 | 7% | 0.9 | **0.34** | -62% ⬇️ |
| **Hanoi** | 50 | 50 | 28% | 0.9 | **0.47** | -48% ⬇️ |
| **Bangkok** | 120 | 120 | 12% | 0.9 | **0.37** | -59% ⬇️ |

**Key Insight:**  
Cùng **14 selected** nhưng alpha khác nhau vì **city size** khác nhau:
- Tokyo (7% rate) → α=0.34 → User mới explore, cần collaborative
- Hanoi (28% rate) → α=0.47 → User biết rõ hơn, personalize nhiều hơn

---

## Flow Hoàn Chỉnh

### 1. TourGenerator Load Data
```python
all_places = db.get_places(city="Tokyo")  # 5000 places
selected_places = db.get_selected_places(user_id)  # 14 places
```

### 2. Get Top Recommendations
```python
top_recommended = recommender.get_top_recommendations(
    candidate_places=all_places,  # 5000
    selected_places=selected_places,  # 14
    k=30  # Chỉ là OUTPUT size
)
```

### 3. Bên Trong get_top_recommendations
```python
# A. Clip total available
total_available = len(candidate_places)  # 5000
total_available = max(30, min(200, total_available))  # → 200

# B. Tính alpha
alpha = user_pref.calculate_alpha(total_available_places=200)
# selection_rate = 14/200 = 0.07
# alpha = 0.34

# C. Score tất cả 5000 places
for place in all_places:  # 5000 places
    content_score = ...
    collab_score = ...
    hybrid_score = 0.34 * content_score + 0.66 * collab_score

# D. Return top 30
return sorted(scores)[:30]
```

---

## Tổng Kết

### Công Thức Cuối Cùng

```python
def calculate_alpha(selected, total_db_places, days):
    """
    Calculate alpha for hybrid recommendation
    
    Args:
        selected: Số places user đã chọn
        total_db_places: Tổng places trong DB của city
        days: Số ngày của trip
    
    Returns:
        Alpha ∈ [0.3, 0.9]
    """
    # 1. Clip total available
    total = max(30, min(200, total_db_places))
    
    # 2. Calculate rates
    selection_rate = selected / total
    places_per_day = selected / days
    
    # 3. Calculate base alpha
    if selection_rate < 0.5:
        alpha = 0.3 + 0.3 * (selection_rate / 0.5)
    else:
        alpha = 0.6 + 0.3 * ((selection_rate - 0.5) / 0.5)
    
    # 4. Bonus for high engagement
    if places_per_day >= 5:
        alpha = min(0.9, alpha + 0.05)
    
    return round(alpha, 2)
```

### Key Principles

1. **Selection Rate > Absolute Count**  
   14/200 (Tokyo) ≠ 14/50 (Hanoi) → alpha khác nhau

2. **Clipping [30, 200]**  
   Phản ánh "interaction pool" thực tế, không phải toàn bộ DB

3. **Linear Scaling**  
   Smooth transition thay vì threshold jumps

4. **Engagement Bonus**  
   PPD ≥ 5 → +0.05 bonus cho power users

5. **Bounded [0.3, 0.9]**  
   Luôn giữ ít nhất 10% collaborative để explore
