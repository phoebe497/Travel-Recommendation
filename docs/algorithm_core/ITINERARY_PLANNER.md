# Báo Cáo Quy Trình Hệ Thống Smart Itinerary Planner

## 1. Tổng Quan Hệ Thống

Hệ thống **Smart Itinerary Planner** là một giải pháp tạo lịch trình du lịch tự động, cá nhân hóa cao, sử dụng các kỹ thuật học máy tiên tiến (Machine Learning) và tối ưu hóa toán học. Hệ thống không chỉ gợi ý các địa điểm phù hợp với sở thích người dùng mà còn sắp xếp chúng thành một lộ trình di chuyển hợp lý, tối ưu về thời gian và chi phí.

Mục tiêu chính:
- **Cá nhân hóa:** Hiểu sâu sở thích người dùng qua ngữ nghĩa (Semantic) và hành vi cộng đồng (Collaborative).
- **Tối ưu hóa:** Giảm thiểu thời gian di chuyển, đảm bảo tính khả thi về thời gian mở cửa và khoảng cách.
- **Trải nghiệm thực tế:** Lịch trình bao gồm đầy đủ các bữa ăn, nghỉ ngơi và hoạt động tham quan hợp lý.

---

## 2. Quy Trình Xử Lý (Pipeline)

Quy trình hoạt động của hệ thống được chia thành 3 giai đoạn chính:

### Giai đoạn 1: Khởi tạo & Xây dựng Đồ thị
Khi nhận yêu cầu từ người dùng (thành phố, số ngày, sở thích, các địa điểm đã chọn trước), hệ thống thực hiện:
1.  **Tải dữ liệu:** Lấy danh sách tất cả địa điểm (nhà hàng, khách sạn, điểm tham quan) của thành phố đó từ cơ sở dữ liệu.
2.  **Xây dựng đồ thị di chuyển:** Tạo một mạng lưới kết nối tất cả các địa điểm. Hệ thống tính toán trước khoảng cách và đường đi ngắn nhất giữa mọi cặp địa điểm bằng thuật toán tối ưu, giúp việc tra cứu sau này diễn ra tức thì.

### Giai đoạn 2: Tính Điểm Gợi Ý (Hybrid Recommendation)
Hệ thống chấm điểm cho từng địa điểm dựa trên mức độ phù hợp với người dùng. Điểm số này là sự kết hợp của hai thành phần:
1.  **Mức độ phù hợp nội dung (Content-Based):** So sánh sự tương đồng về ngữ nghĩa giữa sở thích người dùng và đặc điểm của địa điểm (ví dụ: "temple" tương đồng với "church", "culture").
2.  **Mức độ phù hợp cộng đồng (Collaborative):** Dự đoán người dùng sẽ thích địa điểm nào dựa trên lịch sử đánh giá của những người dùng tương tự.

### Giai đoạn 3: Lập Lịch Trình (Itinerary Generation)
Dựa trên danh sách địa điểm đã được chấm điểm, hệ thống tiến hành sắp xếp vào các ngày du lịch:
1.  **Phân chia khung giờ:** Mỗi ngày được chia thành 7 khung giờ cố định (breakfast, morning, lunch, afternoon, dinner, evening, hotel).
2.  **Lấp đầy khung giờ:** Với mỗi khung giờ, hệ thống chọn các địa điểm tốt nhất phù hợp với loại hình (ví dụ: khung giờ ăn chỉ chọn nhà hàng) và chưa được ghé thăm trong ngày.
3.  **Tối ưu di chuyển:** Khi chọn địa điểm tiếp theo, hệ thống cân nhắc cả điểm số gợi ý và khoảng cách từ địa điểm hiện tại để đảm bảo người dùng không phải di chuyển quá xa.

---

## 3. Chi Tiết Thuật Toán

### 3.1. Content-Based Filtering (Sử dụng BERT)
Thay vì chỉ so khớp từ khóa đơn giản (như hệ thống cũ), hệ thống mới sử dụng mô hình ngôn ngữ lớn **Multilingual BERT**.
- **Cơ chế:** Mô hình chuyển đổi thông tin văn bản của địa điểm (tên, loại hình, mô tả) thành các vector số học đa chiều (768 chiều).
- **Ưu điểm:**
    - **Hiểu ngữ nghĩa:** Máy hiểu rằng "bảo tàng" có nét tương đồng với "di tích lịch sử" hơn là "trung tâm mua sắm".
    - **Đa ngôn ngữ:** Hiểu được sự tương đương giữa tiếng Việt ("Chùa") và tiếng Anh ("Temple") mà không cần từ điển dịch thuật.
    - **Tốc độ:** Sử dụng cơ chế bộ nhớ đệm (Caching) giúp tốc độ xử lý nhanh gấp hàng trăm lần so với tính toán trực tiếp.

### 3.2. Collaborative Filtering (Sử dụng SVD)
Để cá nhân hóa sâu hơn, hệ thống sử dụng thuật toán phân rã ma trận **SVD (Singular Value Decomposition)**.
- **Cơ chế:** Phân tích ma trận đánh giá của hàng ngàn người dùng trước đó để tìm ra các "yếu tố ẩn" (latent factors). Ví dụ: hệ thống có thể tự học được rằng "Người dùng A thích thiên nhiên" và "Địa điểm B thuộc nhóm thiên nhiên" chỉ dựa trên các mẫu đánh giá.
- **Ưu điểm:** Đưa ra các gợi ý mang tính cá nhân hóa cao, phát hiện được những sở thích ngầm mà người dùng có thể chưa khai báo trực tiếp.
- **Xử lý người dùng mới:** Với người dùng chưa có lịch sử, hệ thống tự động điều chỉnh trọng số để ưu tiên thuật toán Content-Based (BERT) hơn.

### 3.3. Tối ưu hóa lộ trình (Sử dụng Dijkstra)
Để giải quyết bài toán di chuyển, hệ thống sử dụng thuật toán **Dijkstra**.
- **Cơ chế:** Tính toán đường đi ngắn nhất giữa tất cả các cặp địa điểm trong thành phố.
- **Ứng dụng:** Khi đang ở địa điểm A, hệ thống biết chính xác khoảng cách và thời gian để đến địa điểm B, C, D... Từ đó, nó có thể tính toán chi phí di chuyển và thời gian cần thiết một cách chính xác nhất.

### 3.4. Sắp xếp lịch trình (Greedy Block Scheduling)
Hệ thống sử dụng chiến thuật **Tham lam (Greedy)** kết hợp với các ràng buộc thực tế để sắp xếp lịch trình.
- **Cơ chế:** Tại mỗi bước (mỗi khung giờ), hệ thống sẽ chọn địa điểm "tốt nhất" tại thời điểm đó. "Tốt nhất" được định nghĩa là sự cân bằng giữa:
    - Điểm gợi ý cao (người dùng thích).
    - Khoảng cách gần (không mất công di chuyển).
    - Phù hợp với khung giờ (ví dụ: không đi công viên vào buổi tối muộn, không ăn trưa lúc 3 giờ chiều).
- **Ràng buộc:**
    - Không lặp lại địa điểm trong cùng một ngày.
    - Khách sạn chỉ xuất hiện vào khung giờ nghỉ ngơi cuối ngày.
    - Các hoạt động tham quan chỉ diễn ra vào Sáng, Chiều, Tối.

---

## 4. Cải Tiến Nổi Bật So Với Hệ Thống Cũ

| Đặc điểm | Hệ thống Cũ | Hệ thống Mới (Smart Itinerary Planner) |
| :--- | :--- | :--- |
| **Hiểu ngôn ngữ** | Chỉ so khớp từ khóa chính xác | Hiểu ngữ nghĩa, đa ngôn ngữ (Việt/Anh) |
| **Cá nhân hóa** | Không có hoặc rất cơ bản | Học từ lịch sử đánh giá của cộng đồng |
| **Tính toán di chuyển** | Khoảng cách đường chim bay đơn giản | Đường đi ngắn nhất tối ưu hóa |
| **Cấu trúc lịch trình** | Đơn giản, thiếu bữa sáng | 7 khung giờ chi tiết (bao gồm Ăn sáng) |
| **Độ chính xác chi phí** | Chỉ ước lượng mức giá (1-4) | Tính toán chi phí thực tế (USD) cho vé & đi lại |
| **Hiệu năng** | Chậm hơn do tính toán lặp lại | Siêu tốc nhờ tối ưu hóa bộ nhớ đệm & thuật toán |

---

## 5. Kết Luận

Hệ thống Smart Itinerary Planner mới đại diện cho một bước tiến lớn về công nghệ gợi ý du lịch. Bằng cách kết hợp khả năng "hiểu" ngôn ngữ của BERT, khả năng "học" sở thích của SVD và khả năng "tính toán" tối ưu của Dijkstra, hệ thống tạo ra những lịch trình không chỉ chính xác về mặt dữ liệu mà còn hợp lý và thuận tiện cho trải nghiệm thực tế của người dùng.
