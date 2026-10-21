# 🎓 UIT Confession Data Crawling & Sentiment Analytics Dashboard (ABSA)

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite3%20(WAL)-emerald.svg)](https://www.sqlite.org/)
[![Dataset Status](https://img.shields.io/badge/Dataset-100%25%20Completed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-orange.svg)]()

> **Dự án:** Thu thập dữ liệu tự động, Biểu diễn Trực quan và Phân tích Cảm xúc theo Khía cạnh (Aspect-Based Sentiment Analysis - ABSA) từ diễn đàn Confession Sinh viên Trường Đại học Công nghệ Thông tin (ĐHQG-HCM).  
> **Giai đoạn dữ liệu:** `01/06/2026 → 18/10/2026` (5 tháng hoàn chỉnh).

---

## 📊 Tổng Quan Bộ Dữ Liệu Thu Thập Được

| Thành phần dữ liệu | Số lượng thực tế | Mô tả kỹ thuật |
| :--- | :--- | :--- |
| **Tổng bài viết (Posts)** | **4.422 bài** | 100% bài viết kèm toàn văn nội dung, tác giả, mốc thời gian và liên kết cố định (`permalink`). |
| **Tổng bình luận (Comments)** | **16.231 bình luận** | Đầy đủ cấu trúc phân cấp (bình luận gốc và **737 câu phản hồi con `parent_id`**). |
| **Lượt biểu cảm (Reactions)** | **254.387 lượt** | Thu thập chi tiết **7 loại cảm xúc**: Like (116.235), Haha (74.032), Sad (12.312), Love (9.932), Care (546), Wow (153), Angry (8). |
| **Tập nhãn vàng (Gold ABSA)** | **4.402 bài viết** | Đã được chuẩn hóa và gán nhãn theo **7 khía cạnh đào tạo của UIT** (`gold.csv`). |

---

## 🚀 HƯỚNG DẪN XEM WEB BIỂU DIỄN DỮ LIỆU (QUAN TRỌNG)

Dự án đã tích hợp sẵn một máy chủ Web cục bộ kèm giao diện trực quan hóa cao cấp, **hoạt động ngoại tuyến 100% (không lo lỗi CDN hay mất mạng)**.

### Cách 1: Khởi động 1-Click trên Windows (Nhanh nhất)
Nhấp đúp chuột vào tệp:
```cmd
run_dashboard.bat
```
*(Cửa sổ dòng lệnh sẽ tự khởi chạy máy chủ và tự động mở trình duyệt web hiển thị trang Dashboard).*

---

### Cách 2: Khởi động bằng dòng lệnh (Windows / macOS / Linux)

1. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Chạy máy chủ Dashboard:**
   ```bash
   python serve_dashboard.py
   ```

3. **Mở trình duyệt truy cập các địa chỉ sau:**
   - **Trang Dashboard Phân tích chính:**  
     👉 **[http://localhost:8088/](http://localhost:8088/)**
   - **Giao diện Duyệt & Gán nhãn ABSA chuyên sâu:**  
     👉 **[http://localhost:8088/review](http://localhost:8088/review)**

---

## ✨ Các Tính Năng Nổi Bật Trên Web Biểu Diễn

1. **Hệ thống 5 Biểu đồ Phân tích Chuyên sâu (300 DPI)**:
   - **Biểu đồ 1 • Cơ cấu 7 sắc thái biểu cảm**: Thể hiện tỷ trọng áp đảo của văn hóa tự trào (*Haha chiếm 34.7%*).
   - **Biểu đồ 2 • Nhiệt đồ (Heatmap) 24h × 7 ngày**: Phân tích hành vi "cú đêm" và khung giờ vàng đăng bài (20h - 23h).
   - **Biểu đồ 3 • Ma trận khía cạnh học đường ABSA**: Đào sâu 7 khía cạnh (Chương trình, Thi cử, Giảng viên, Cơ sở vật chất...).
   - **Biểu đồ 4 • Biến động cảm xúc theo tháng**: Xu hướng dịch chuyển từ kỳ thi hè (T6, T7) đến cao điểm tuyển sinh (T8) và nhập học (T9, T10).
   - **Biểu đồ 5 • Tương quan độ dài bài viết & cảm xúc**: Phát hiện bài viết dài (> 200 từ) có tỷ lệ buồn (*Sad*) tăng vọt gấp 4.2 lần.
2. **Chế độ Sáng / Tối (Light & Dark Mode) Tùy chỉnh**:
   - Chuyển đổi giao diện tức thì với 1 nút bấm góc trên màn hình (`☀️ Chế độ Sáng` / `🌙 Chế độ Tối`), tự động ghi nhớ sở thích người dùng qua `localStorage`.
3. **Cửa sổ Xem chi tiết Confession (Post Detail Modal)**:
   - Bấm vào bất kỳ dòng nào trong bảng để mở hộp thoại xem: toàn văn nội dung nguyên bản, chi tiết 7 biểu cảm riêng lẻ, số lượt share và cây phân cấp bình luận cha - con.
4. **Tiêu điểm: Không gian Duyệt & Gán nhãn ABSA**:
   - Được thiết kế nổi bật ngay giữa trang chính, cho phép mở trực tiếp trình duyệt 4.402 bài viết và hiệu chỉnh nhãn lưu tức thời vào CSDL.
5. **Bộ lọc & Tìm kiếm tức thì**:
   - Tìm kiếm bài viết theo từ khóa, mã sinh viên, tên tác giả hoặc lọc bình luận theo mức độ tương tác.

---

## 🛠️ Hướng Dẫn Sử Dụng Bộ Công Cụ Cào Dữ Liệu (Scraper)

Dự án cung cấp đường ống tự động hóa bằng Selenium và JavaScript DOM Injection chống checkpoint:

### 1. Chuẩn bị môi trường & Đăng nhập Facebook
Để cào dữ liệu mà không bị chặn, dự án sử dụng hồ sơ trình duyệt riêng biệt:
```bash
# Đăng nhập thủ công một lần để lưu phiên làm việc (cookie) vào thư mục browser_profile
python -c "from src.uitconf.scraper.driver import make_driver; d = make_driver({'browser_profile_dir': 'browser_profile'}); d.get('https://www.facebook.com'); input('Đăng nhập xong nhấn Enter để thoát...'); d.quit()"
```

### 2. Chạy quy trình thu thập dữ liệu
```bash
# Chạy cào toàn bộ dữ liệu tự động
python crawl_full_dataset.py
```
*Đặc tính kỹ thuật của Crawler:*
- **Chặn tải hình ảnh (`imagesEnabled=false`) & Vô hiệu hóa GPU**: Giúp crawler chạy êm ái, ngốn cực ít RAM và không bị tràn bộ nhớ VRAM.
- **Cơ chế Jitter & Guard System**: Tạo độ trễ ngẫu nhiên mô phỏng người thật; tự động ngắt an toàn nếu phát hiện URL checkpoint.
- **Lưu trữ SQLite WAL**: Dữ liệu được ghi nhận nguyên tử (Atomic Commit) sau từng bài, đảm bảo không mất dữ liệu dù bị ngắt ngang.

### 3. Tái tạo lại các biểu đồ phân tích (plots)
Nếu có dữ liệu mới trong SQLite, bạn chỉ cần chạy:
```bash
python generate_visualizations.py
```
Toàn bộ 5 biểu đồ PNG chất lượng cao trong thư mục `plots/` sẽ được cập nhật đồng bộ.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```plaintext
CrawlUITData/
├── data/
│   ├── raw/
│   │   └── raw.sqlite                  # Cơ sở dữ liệu SQLite lưu toàn bộ bài viết & bình luận
│   ├── clean/
│   │   └── units.csv                   # Tập dữ liệu đã làm sạch & tách đơn vị
│   └── labeled/
│       ├── gold.csv                    # Tập dữ liệu chuẩn vàng 4.402 mẫu gán nhãn ABSA
│       ├── review_labeled.csv          # Dữ liệu phục vụ công cụ review
│       └── review_viewer.html          # Giao diện duyệt & hiệu chỉnh gán nhãn ABSA
├── dataset_uit_posts_and_comments.xlsx # Tệp Excel master (4.422 bài & 16.231 bình luận)
├── dataset_uit_posts.csv               # Tệp CSV bài viết chuẩn
├── dataset_uit_comments.csv            # Tệp CSV bình luận phân cấp chuẩn
├── plots/                              # Bộ 5 biểu đồ phân tích & dashboard HTML
│   ├── 1_emotions_distribution.png
│   ├── 2_hourly_weekly_heatmap.png
│   ├── 3_aspect_sentiment_matrix.png
│   ├── 4_monthly_sentiment_trends.png
│   └── 5_text_length_vs_sentiment.png
├── static/
│   └── tailwind.min.js                 # Thư viện Tailwind CSS tích hợp sẵn (Offline-ready)
├── docs/
│   ├── BAO_CAO_CONG_CU_VA_QUY_TAC_GAN_NHAN.md  # Báo cáo toàn diện công cụ & quy tắc ABSA
│   ├── ANNOTATION_GUIDELINE.md         # Hướng dẫn chi tiết quy tắc gán nhãn
│   └── CRAWLING_TOOLS.md               # Báo cáo kỹ thuật về bộ công cụ cào Selenium
├── src/                                # Gói mã nguồn cốt lõi (uitconf)
│   └── uitconf/
│       ├── db.py                       # Kết nối & thao tác CSDL SQLite WAL
│       ├── config.py                   # Đọc file cấu hình YAML
│       └── scraper/                    # Driver Selenium, Guard chống khóa, Parser
├── configs/
│   ├── config.yaml                     # Cấu hình tham số cào, bộ chọn selectors, độ trễ
│   └── aspects.yaml                    # Danh mục định nghĩa các khía cạnh đào tạo UIT
├── crawl_full_dataset.py               # Script cào dữ liệu bài viết và bình luận chính
├── generate_visualizations.py          # Script phân tích & vẽ 5 bộ biểu đồ thống kê
├── serve_dashboard.py                  # Máy chủ Web cục bộ phục vụ Dashboard & REST APIs
├── dashboard.html                      # Giao diện Dashboard phân tích trực quan
├── run_dashboard.bat                   # Tệp chạy nhanh Dashboard 1-click trên Windows
├── requirements.txt                    # Danh sách thư viện Python cần thiết
└── README.md                           # Tài liệu hướng dẫn sử dụng dự án
```

---

## 📑 Báo Cáo Chuyên Sâu Về Công Cụ & Quy Tắc Gán Nhãn

Để xem chi tiết cơ sở khoa học, danh mục 7 khía cạnh đào tạo (`giang_vien`, `chuong_trinh`, `co_so_vat_chat`, `hoc_phi`, `thi_cu`, `hanh_chinh`, `doan_hoi`), điều kiện ràng buộc gán nhãn cảm xúc và cách xử lý mỉa mai (Sarcasm), xin vui lòng xem tài liệu:

👉 **[Báo Cáo Công Cụ & Quy Tắc Gán Nhãn (docs/BAO_CAO_CONG_CU_VA_QUY_TAC_GAN_NHAN.md)](docs/BAO_CAO_CONG_CU_VA_QUY_TAC_GAN_NHAN.md)**

---

## 👨‍💻 Tác Giả & Bản Quyền
- **Tác giả:** ThienPhucNg-1410
- **Email:** nguyenhoangthienphuc1410@gmail.com
- **Repository:** [https://github.com/ThienPhucNg-1410/CrawlUITData](https://github.com/ThienPhucNg-1410/CrawlUITData)
