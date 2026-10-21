# BÁO CÁO TOÀN DIỆN: CÔNG CỤ SỬ DỤNG & BỘ QUY TẮC GÁN NHÃN ABSA
**Dự án:** Thu thập, Biểu diễn Dữ liệu & Phân tích Cảm xúc Đa Khía Cạnh (ABSA) Confession Sinh viên UIT  
**Mã nguồn:** [ThienPhucNg-1410/CrawlUITData](https://github.com/ThienPhucNg-1410/CrawlUITData)  
**Tập dữ liệu chuẩn:** 4.422 bài viết | 16.231 bình luận | 4.402 mẫu ABSA gán nhãn

---

## MỤC LỤC
1. [Giới Thiệu & Mục Tiêu Nghiên Cứu](#1-giới-thiệu--mục-tiêu-nghiên-cứu)
2. [Hệ Thống Công Cụ & Kỹ Thuật Sử Dụng (Tools Report)](#2-hệ-thống-công-cụ--kỹ-thuật-sử-dụng-tools-report)
   - [2.1. Công cụ thu thập dữ liệu Facebook (Scraping Pipeline)](#21-công-cụ-thu-thập-dữ-liệu-facebook-scraping-pipeline)
   - [2.2. Cơ sở dữ liệu & Quản lý giao dịch bền vững (Database & Storage)](#22-cơ-sở-dữ-liệu--quản-lý-giao-dịch-bền-vững-database--storage)
   - [2.3. Công cụ xử lý ngôn ngữ tự nhiên & Làm sạch văn bản (NLP & Data Cleaning)](#23-công-cụ-xử-lý-ngôn-ngữ-tự-nhiên--làm-sạch-văn-bản-nlp--data-cleaning)
   - [2.4. Công cụ trực quan hóa & Máy chủ Web biểu diễn (Visualization & Web Server)](#24-công-cụ-trực-quan-hóa--máy-chủ-web-biểu-diễn-visualization--web-server)
3. [Bộ Quy Tắc Gán Nhãn Cảm Xúc Theo Khía Cạnh (ABSA Annotation Guidelines)](#3-bộ-quy-tắc-gán-nhãn-cảm-xúc-theo-khía-cạnh-absa-annotation-guidelines)
   - [3.1. Cấu trúc mẫu ABSA chuẩn](#31-cấu-trúc-mẫu-absa-chuẩn)
   - [3.2. Danh mục 7 khía cạnh đào tạo trường UIT (Aspect Taxonomy)](#32-danh-mục-7-khía-cạnh-đào-tạo-trường-uit-aspect-taxonomy)
   - [3.3. Bộ 5 nhãn cảm xúc & Điều kiện tiên quyết](#33-bộ-5-nhãn-cảm-xúc--điều-kiện-tiên-quyết)
   - [3.4. Các quy tắc xử lý trường hợp đặc thù](#34-các-quy-tắc-xử-lý-trường-hợp-đặc-thù)
4. [Thống Kê Tập Dữ Liệu Thực Tế (Empirical Distribution)](#4-thống-kê-tập-dữ-liệu-thực-tế-empirical-distribution)
5. [Kết Luận](#5-kết-luận)

---

## 1. Giới Thiệu & Mục Tiêu Nghiên Cứu
Confession sinh viên là một trong những nguồn dữ liệu văn bản phong phú nhất phản ánh chân thực đời sống học đường, tâm tư, khó khăn và ý kiến đóng góp của sinh viên về môi trường đại học. Tuy nhiên, dữ liệu này có độ nhiễu cao, sử dụng nhiều tiếng lóng (teencode), emoji, văn phong tự trào và mỉa mai (sarcasm).

Mục tiêu của dự án:
1. **Xây dựng đường ống cào dữ liệu tự động (Automated Web Crawler)** thu thập 100% bài viết và bình luận phân cấp trên diễn đàn Confession Trường Đại học Công nghệ Thông tin (ĐHQG-HCM) trong giai đoạn từ **01/06/2026 đến 18/10/2026**.
2. **Thiết kế hệ thống gán nhãn theo khía cạnh (Aspect-Based Sentiment Analysis - ABSA)** nhằm phân tách câu confession thành các thực thể trường học cụ thể thay vì chỉ gán nhãn cảm xúc chung chung toàn bài.
3. **Xây dựng ứng dụng Web cục bộ trực quan hóa dữ liệu (Interactive Analytics Dashboard)** hỗ trợ chế độ Sáng/Tối, biểu đồ phân tích đa chiều và công cụ hiệu chỉnh nhãn trực tiếp.

---

## 2. Hệ Thống Công Cụ & Kỹ Thuật Sử Dụng (Tools Report)

### 2.1. Công cụ thu thập dữ liệu Facebook (Scraping Pipeline)

| Tên công cụ / Kỹ thuật | Vai trò & Triển khai trong mã nguồn | Đặc tính kỹ thuật nổi bật |
| :--- | :--- | :--- |
| **Selenium WebDriver (Python)** | `src/uitconf/scraper/driver.py`, `crawl_full_dataset.py` | Điều khiển trình duyệt tự động, giả lập hành vi người dùng, xử lý các nút bấm động của Facebook SPA. |
| **Google Chrome (Dedicated Profile)** | `browser_profile/` (được cấu hình qua `--user-data-dir`) | Lưu trữ phiên đăng nhập và Cookie thật của tài khoản phụ, tránh việc đăng nhập lại mỗi lần chạy, chống checkpoint hiệu quả. |
| **Tối ưu tài nguyên trình duyệt** | Flags: `--blink-settings=imagesEnabled=false`, `--disable-gpu` | Chặn tải toàn bộ hình ảnh và vô hiệu hóa render đồ họa, giảm 85% lượng RAM/băng thông mạng, ngăn ngừa tràn bộ nhớ VRAM. |
| **JavaScript DOM Injection** | `driver.execute_script()` trong `crawl_full_dataset.py` | Bơm trực tiếp JavaScript vào DOM trình duyệt để bóc tách bài viết và bình luận trong 1 chu kỳ thực thi, giải quyết triệt để lỗi `StaleElementReferenceException`. |
| **Bộ bảo vệ chống khóa (Guard System)** | `src/uitconf/scraper/guard.py` | Nhận diện tự động các URL hoặc modal bất thường (`checkpoint`, `captcha`, `tài khoản bị hạn chế`) và kích hoạt cơ chế `HardStop` dừng an toàn. |
| **Hệ thống độ trễ ngẫu nhiên (Jitter Delays)** | `delays: scroll: [3, 6]`, `between_posts: [5, 10]` | Giãn cách ngẫu nhiên các thao tác click, cuộn trang theo phân phối chuẩn để mô phỏng nhịp độ đọc tin của con người. |

### 2.2. Cơ sở dữ liệu & Quản lý giao dịch bền vững (Database & Storage)

- **SQLite3 với chế độ Write-Ahead Logging (WAL Mode)**:
  - Tệp cơ sở dữ liệu: `data/raw/raw.sqlite`.
  - Cấu hình: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`.
  - **Lợi ích:** Cho phép đọc và ghi song song mà không bị khóa bảng. Mỗi bài viết sau khi bóc tách kèm bình luận được commit nguyên tử (**Atomic Commit**), đảm bảo nếu xảy ra mất điện hoặc mất mạng đột ngột thì dữ liệu đã cào vẫn vẹn nguyên 100%.
- **Xuất bản đa định dạng (Pandas Export)**:
  - Xuất ra tệp Excel tổng hợp `dataset_uit_posts_and_comments.xlsx` (gồm 2 sheets: `Posts_Full` và `Comments_Full`).
  - Xuất ra các tệp CSV chuẩn hóa: `dataset_uit_posts.csv` (4.422 dòng) và `dataset_uit_comments.csv` (16.231 dòng).

### 2.3. Công cụ xử lý ngôn ngữ tự nhiên & Làm sạch văn bản (NLP & Data Cleaning)

- **Biểu thức chính quy (Regular Expressions - `re`)**:
  - Loại bỏ chuỗi boilerplate dư thừa ở đuôi bình luận do giao diện Facebook tự sinh (`Thích`, `Trả lời`, `Xem bản dịch`, `…`).
  - Tách chuẩn các từ và dấu câu dính liền (`chữ.Chữ` $\rightarrow$ `chữ. Chữ`, ngoặc kép dính chữ `""Trời` $\rightarrow$ `"" Trời`).
  - Nhận diện nhãn dán, file đính kèm, GIF (`[Hình ảnh/Nhãn dán]`).
- **Xử lý thời gian tự nhiên (`dateparser`)**:
  - `src/uitconf/scraper/parse.py` chuyển đổi thời gian tương đối tiếng Việt (`"2 giờ trước"`, `"1 tuần"`, `"Hôm qua lúc 19:20"`) sang định dạng chuẩn ISO 8601 (`YYYY-MM-DDTHH:MM:SS`).
- **Từ điển chuẩn hóa Teencode**:
  - `data/teencode.csv` lưu trữ ánh xạ các từ viết tắt phổ biến của sinh viên UIT (`dkmh` $\rightarrow$ `đăng ký môn học`, `gpa` $\rightarrow$ `điểm trung bình tích lũy`, `gv` $\rightarrow$ `giảng viên`, `sv` $\rightarrow$ `sinh viên`, `ctdl` $\rightarrow$ `cấu trúc dữ liệu`).

### 2.4. Công cụ trực quan hóa & Máy chủ Web biểu diễn (Visualization & Web Server)

- **Máy chủ Web Python thuần (`serve_dashboard.py`)**:
  - Dựa trên module chuẩn `http.server` và `socketserver`, không phụ thuộc vào framework nặng như Django/Flask, giúp người dùng mở và chạy được ngay.
  - Cung cấp các REST API thời gian thực:
    - `GET /api/stats`: Trả về số liệu thống kê tổng thể từ SQLite (tổng bài, tổng reactions, phân loại biểu cảm, tiến độ).
    - `GET /api/posts`: Trả về danh sách bài viết hỗ trợ phân trang (`limit`, `offset`) và tìm kiếm toàn văn.
    - `GET /api/comments`: Trả về danh sách bình luận kèm phân cấp (`parent_id`) và lọc theo lượt tương tác.
    - `GET /api/samples`: Trả về 4.402 mẫu ABSA từ `gold.csv` kèm lọc theo nhãn cảm xúc và khía cạnh.
    - `POST /update_label`: Cập nhật nhãn trực tiếp từ giao diện vào tệp SQLite và CSV.
- **Thư viện giao diện Tailwind CSS (Chế độ Ngoại tuyến)**:
  - Toàn bộ script Tailwind được tích hợp sẵn tại `static/tailwind.min.js` (407 KB), đảm bảo giao diện hiển thị mượt mà 100% không phụ thuộc internet hay CDN bên ngoài.
  - Hỗ trợ **Chế độ Sáng / Tối (Light & Dark Theme)** tùy chỉnh lưu qua `localStorage`.
- **Hệ thống tạo biểu đồ thống kê (`generate_visualizations.py`)**:
  - Sử dụng `matplotlib` và `seaborn` kết hợp font chữ `Segoe UI` hỗ trợ tiếng Việt trọn vẹn, xuất ra 5 biểu đồ chất lượng cao (300 DPI) lưu tại thư mục `plots/`.

---

## 3. Bộ Quy Tắc Gán Nhãn Cảm Xúc Theo Khía Cạnh (ABSA Annotation Guidelines)

### 3.1. Cấu trúc mẫu ABSA chuẩn
Mỗi đơn vị đánh giá (Unit) trong tập dữ liệu vàng (`gold.csv`) đại diện cho 1 bài viết hoặc bình luận, được biểu diễn dưới dạng bộ 4 phần tử:
$$\langle \text{Entity/Target}, \text{Aspect}, \text{Polarity}, \text{Context} \rangle$$
- **Entity / Target:** Thực thể được đề cập trực tiếp (ví dụ: *Thầy Dũng*, *Wifi phòng C301*, *Thủ tục DAA*).
- **Aspect (Khía cạnh):** Nhóm chủ đề học đường thuộc 7 khía cạnh đào tạo của UIT.
- **Polarity (Sắc thái cảm xúc):** Nhãn thái độ tương ứng (`tich_cuc`, `tieu_cuc`, `trung_tinh`, `hoi_dap`, `khong_lien_quan`).
- **Context:** Đoạn ngữ cảnh gốc của bài viết.

---

### 3.2. Danh mục 7 khía cạnh đào tạo trường UIT (Aspect Taxonomy)

| Mã Khía Cạnh (`aspect`) | Tên khía cạnh học đường | Phạm vi nội dung & Từ khóa đặc trưng |
| :--- | :--- | :--- |
| **`giang_vien`** | Giảng viên & Đội ngũ trợ giảng | Tác phong giảng dạy, phương pháp truyền đạt, sự nhiệt tình hỗ trợ sinh viên, cách chấm bài tập lớn/lab, thái độ của thầy cô. *(Từ khóa: thầy, cô, gv, giảng viên, chấm điểm, giải thích, nhiệt tình)* |
| **`chuong_trinh`** | Chương trình đào tạo & Môn học | Nội dung môn học, độ nặng chương trình, kiến thức thực tế, bài tập lớn (BTTL), đồ án chuyên ngành, sự phù hợp giữa lý thuyết và thực hành. *(Từ khóa: môn học, csdl, ctdl, oop, mạng máy tính, đồ án, bttl, kiến thức, thực tế)* |
| **`co_so_vat_chat`** | Cơ sở vật chất & Tiện ích trường | Phòng học lý thuyết, phòng máy lab, máy lạnh, thang máy toà A/B/E, tốc độ wifi trường, nhà vệ sinh, bãi giữ xe, căn tin, thư viện trung tâm. *(Từ khóa: wifi, máy lạnh, thang máy, bãi xe, phòng C, toà B, thư viện, ổ cắm)* |
| **`hoc_phi`** | Học phí & Chính sách tài chính | Mức học phí theo tín chỉ, lộ trình tăng học phí, chính sách học bổng khuyến khích học tập, miễn giảm học phí, các khoản phụ phí. *(Từ khóa: học phí, học bổng, tín chỉ, tiền học, đóng học phí, miễn giảm)* |
| **`thi_cu`** | Thi cử & Đánh giá kết quả | Lịch thi, đề thi giữa kỳ/cuối kỳ, giám thị coi thi, quy chế làm tròn điểm, phúc khảo bài thi, tỷ lệ rớt môn, học lại. *(Từ khóa: đề thi, phòng thi, phúc khảo, điểm số, rớt môn, qua môn, gpa, f, điểm liệt)* |
| **`hanh_chinh`** | Quy chế & Thủ tục hành chính | Đăng ký môn học (ĐKMH), hệ thống portal DAA, phòng Công tác Sinh viên (CTSV), thủ tục xin cấp bảng điểm, giấy xác nhận sinh viên, chuyển ngành. *(Từ khóa: dkmh, portal, daa, ctsv, giấy tờ, thủ tục, xác nhận sinh viên, mở lớp)* |
| **`doan_hoi`** | Phong trào Đoàn - Hội & Hoạt động | Hoạt động Đoàn Thanh niên, Hội Sinh viên, các câu lạc bộ (CLB) học thuật/sở thích, ngày Công tác xã hội (CTXH), Điểm rèn luyện (DRL), chiến dịch tình nguyện Mùa Hè Xanh. *(Từ khóa: đoàn, hội, clb, drl, ctxh, ngày tình nguyện, phong trào)* |

> 📌 *Lưu ý quan trọng:* Khía cạnh Ký túc xá (`ky_tuc_xa`) không thuộc quyền quản lý trực tiếp của UIT mà thuộc Trung tâm Quản lý KTX ĐHQG-HCM, do đó được xếp vào nhóm `khong_lien_quan` nhằm đảm bảo tính tập trung cho nghiên cứu chất lượng đào tạo nội tại của trường.

---

### 3.3. Bộ 5 nhãn cảm xúc & Điều kiện tiên quyết

> ⚠️ **ĐIỀU KIỆN BẮT BUỘC (Prerequisite Rule):**  
> Ba nhãn cảm xúc mang tính định tính thái độ (`tich_cuc`, `tieu_cuc`, `trung_tinh`) **CHỈ ĐƯỢC PHÉP GÁN KHI BÀI VIẾT CHỨA ÍT NHẤT 1 KHÍA CẠNH (ASPECT) THUỘC 7 KHÍA CẠNH CỦA UIT**.  
> Mọi bài viết bày tỏ cảm xúc chung chung (tình cảm cá nhân, chuyện thời tiết, phim ảnh) nhưng không gắn với thực thể UIT nào thì bắt buộc gán nhãn `khong_lien_quan`.

1. **`tich_cuc` (Positive Sentiment)**:
   - Sinh viên thể hiện sự hài lòng, khen ngợi, cảm kích hoặc đánh giá cao đối với giảng viên, chương trình đào tạo, dịch vụ hoặc sự kiện của UIT.
   - *Ví dụ:* `"Thầy Dũng dạy môn Mạng máy tính siêu nhiệt tình, bài giảng dễ hiểu điểm lại cao nữa."` $\rightarrow$ Aspect: `giang_vien`, Nhãn: `tich_cuc`.

2. **`tieu_cuc` (Negative Sentiment)**:
   - Sinh viên bày tỏ sự bức xúc, thất vọng, chê bai, phàn nàn về sự cố cơ sở vật chất, đề thi quá khó, thủ tục hành chính chậm trễ hoặc học phí cao.
   - *Ví dụ:* `"Wifi phòng C301 cứ rớt mạng liên tục, đang làm lab nộp bài mà lag muốn khóc."` $\rightarrow$ Aspect: `co_so_vat_chat`, Nhãn: `tieu_cuc`.

3. **`trung_tinh` (Neutral Information)**:
   - Bài viết chia sẻ thông tin học tập khách quan, giải thích kinh nghiệm chọn môn, thuật lại sự việc mà không kèm thái độ khen chê rõ rệt.
   - *Ví dụ:* `"Môn Kiến trúc máy tính kỳ này có 3 cột điểm quá trình gồm 2 bài quiz và 1 bài lab thực hành."` $\rightarrow$ Aspect: `chuong_trinh|thi_cu`, Nhãn: `trung_tinh`.

4. **`hoi_dap` (Academic & Administrative Inquiries)**:
   - Các thắc mắc cần cộng đồng giải đáp liên quan trực tiếp đến đời sống học thuật: hỏi kinh nghiệm học thầy cô, hỏi xin tài liệu ôn thi, hỏi thủ tục ĐKMH, quy chế xét học bổng.
   - *Ví dụ:* `"Mọi người cho em hỏi phòng DAA thứ 7 có mở cửa làm việc để nhận bằng tốt nghiệp không ạ?"` $\rightarrow$ Aspect: `hanh_chinh`, Nhãn: `hoi_dap`.

5. **`khong_lien_quan` (Irrelevant / Noise)**:
   - Bài viết về chuyện tình cảm cá nhân (tìm crush, tỏ tình), nhượng đồ dùng/phòng trọ, tin tức bên ngoài, tìm đồ thất lạc, hoặc tâm sự đời sống không liên quan đến môi trường đào tạo UIT.
   - *Ví dụ:* `"Tìm bạn nữ mặc áo trắng ngồi bàn đầu toà B chiều nay, cho mình xin in4 làm quen nha."` $\rightarrow$ Aspect: `nan`, Nhãn: `khong_lien_quan`.

---

### 3.4. Các quy tắc xử lý trường hợp đặc thù

1. **Xử lý Mỉa mai & Châm biếm (Sarcasm Handling)**:
   - Sinh viên CNTT thường sử dụng ngôn từ tự trào (self-deprecating humor).
   - Nếu bài viết bề ngoài sử dụng từ khen ngợi nhưng thực chất mỉa mai một vấn đề bất cập (ví dụ: *"Cảm ơn trường đã cho chúng em trải nghiệm cảm giác leo bộ 8 tầng toà A rèn luyện thể lực"*), hệ thống phải nhận diện ngụ ý thực tế để gán nhãn `tieu_cuc` (Aspect: `co_so_vat_chat`) và đánh dấu cờ `sarcasm = 1`.
2. **Kế thừa ngữ cảnh bình luận (Comment Context Inheritance)**:
   - Các bình luận ngắn dưới bài viết liên quan (ví dụ: *"Chuẩn luôn"*, *"Đồng ý kiến"*, *"Rất đúng ạ"*) được kế thừa tự động khía cạnh và cảm xúc từ bài viết cha.
3. **Bài viết đa khía cạnh (Multi-aspect Sentences)**:
   - Một bài viết có thể chứa nhiều câu với các sắc thái cảm xúc trái ngược nhau đối với từng khía cạnh. Trong tập dữ liệu, các khía cạnh được phân cách bằng dấu gạch đứng `|` (ví dụ: `giang_vien|co_so_vat_chat`).

---

## 4. Thống Kê Tập Dữ Liệu Thực Tế (Empirical Distribution)

Dữ liệu được trích xuất từ tập chuẩn **4.402 mẫu ABSA (`gold.csv`)**:

### 4.1. Phân bố nhãn cảm xúc
- **Hỏi đáp (`hoi_dap`)**: **2.930 bài (66.6%)** - Chiếm đa số tuyệt đối, phản ánh nhu cầu hỗ trợ thông tin học tập, quy chế, đăng ký môn học rất lớn của sinh viên trên mạng xã hội.
- **Không liên quan (`khong_lien_quan`)**: **890 bài (20.2%)** - Các chủ đề tâm sự cá nhân, tìm đồ rơi, thả thính.
- **Trung tính (`trung_tinh`)**: **526 bài (11.9%)** - Cung cấp thông tin môn học và chia sẻ kinh nghiệm học tập khách quan.
- **Tích cực (`tich_cuc`)**: **36 bài (0.8%)** - Khen ngợi giảng viên, cảm ơn trường lớp.
- **Tiêu cực (`tieu_cuc`)**: **20 bài (0.5%)** - Bức xúc về cơ sở vật chất hoặc quy chế điểm.

### 4.2. Phân bố khía cạnh học đường (Aspect Frequency)
- **Chương trình đào tạo (`chuong_trinh`)**: **1.391 lượt** (Vị trí số 1).
- **Thi cử & Điểm số (`thi_cu`)**: **894 lượt** (Vị trí số 2).
- **Giảng viên (`giang_vien`)**: **448 lượt** (Vị trí số 3).
- **Phong trào Đoàn - Hội (`doan_hoi`)**: **208 lượt**.
- **Thủ tục hành chính (`hanh_chinh`)**: **138 lượt**.
- **Học phí (`hoc_phi`)**: **138 lượt**.
- **Cơ sở vật chất (`co_so_vat_chat`)**: **126 lượt**.

---

## 5. Kết Luận
Báo cáo trên cung cấp đầy đủ cơ sở khoa học, công cụ thực thi và quy tắc nghiệp vụ cho bài toán Phân tích Cảm xúc theo Khía cạnh (ABSA) trên dữ liệu mạng xã hội sinh viên UIT. Toàn bộ mã nguồn, cơ sở dữ liệu SQLite, tập nhãn Gold và ứng dụng Web dashboard đã được đóng gói hoàn chỉnh để người khác có thể tái hiện và phát triển tiếp các mô hình học máy (PhôBERT, ViBERT, LLMs).
