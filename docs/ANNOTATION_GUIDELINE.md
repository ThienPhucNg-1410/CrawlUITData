# BỘ QUY TẮC GÁN NHÃN & THU THẬP DỮ LIỆU (ANNOTATION & SCRAPING RULES v4.1)
*Dự án: Phân tích cảm xúc đa khía cạnh (ABSA) Confession Sinh viên UIT*

---

## 📌 QUY TẮC 1: CẤU TRÚC ĐỊNH DANH PHÂN CẤP (ID SCHEME)
Mọi điểm dữ liệu trong CSDL và tập nhãn bắt buộc tuân theo quy ước:
1. **Bài viết gốc (`post`):** Giữ nguyên ID gốc của Facebook làm ID chính.
   - *Định dạng:* `[post_id]` (Ví dụ: `1137195462176515`)
2. **Bình luận (`comment`):** Định danh theo cơ chế cha-con, gắn kèm số thứ tự:
   - *Định dạng:* `[post_id]_[sub_id]` (Ví dụ: `1137195462176515_1`, `1137195462176515_2`...)
   - *Ý nghĩa:* Dễ dàng truy xuất, gom nhóm (group by) và kế thừa thông tin ngữ cảnh từ bài gốc.

---

## 📌 QUY TẮC 2: NGUYÊN TẮC "POST GỐC QUYẾT ĐỊNH" (PARENT POST PRE-FILTER)
**Luôn nhìn vào bài viết gốc trước khi xét đến bình luận:**
1. **Nếu Post gốc KHÔNG liên quan** (mang nhãn `khong_lien_quan`):
   - ➔ **Tuyệt đối KHÔNG cào bình luận** của bài đó (tiết kiệm tài nguyên và bảo vệ an toàn nick).
   - ➔ Mọi bình luận bên dưới bài đó mặc định được xếp vào **`khong_lien_quan`** (loại bỏ hoàn toàn rác nhiễu).
2. **Nếu Post gốc LIÊN QUAN** (thuộc 4 nhãn `trung_tinh`, `tich_cuc`, `tieu_cuc`, `hoi_dap`):
   - ➔ Ưu tiên thu thập bình luận để phân tích cảm xúc và giải đáp.
   - ➔ Các bình luận ngắn ("chuẩn", "thầy dạy hay", "đồng ý") **tự động kế thừa khía cạnh (aspect)** từ bài viết gốc.

---

## 📌 QUY TẮC 3: ĐIỀU KIỆN TIÊN QUYẾT CHO 3 NHÃN CẢM XÚC (`trung_tinh`, `tich_cuc`, `tieu_cuc`)
> ⚠️ **ĐIỀU KIỆN BẮT BUỘC:**  
> Bộ 3 nhãn cảm xúc `trung_tinh`, `tich_cuc`, `tieu_cuc` **CHỈ ĐƯỢC PHÉP ÁP DỤNG KHI BÀI VIẾT/BÌNH LUẬN CÓ CHỨA ÍT NHẤT 1 KHÍA CẠNH (ASPECT) THỰC THỂ CỦA UIT** (giảng viên, chương trình đào tạo, cơ sở vật chất, học phí, thi cử, hành chính, đoàn - hội).  
> **Mọi bài viết không có aspect liên quan đến UIT thì TUYỆT ĐỐI KHÔNG GÁN NHÃN CẢM XÚC, mà phải đưa về `khong_lien_quan`!**

### Chi tiết 3 nhãn cảm xúc:
1. `tieu_cuc`:
   - Bày tỏ thái độ bất mãn, chê bai, bức xúc, thất vọng về môn học, giảng viên, tác phong làm việc, wifi, máy lạnh, quy chế thi cử...
   - *Điều kiện:* **Bắt buộc có Aspect**.
2. `tich_cuc`:
   - Bày tỏ thái độ khen ngợi, hài lòng, biết ơn về giảng viên, trường, môn học, cơ sở vật chất UIT.
   - *Điều kiện:* **Bắt buộc có Aspect**.
3. `trung_tinh`:
   - Đưa ra nhận xét, đánh giá, chia sẻ kinh nghiệm, cung cấp thông tin khách quan về trường/thầy cô/môn học/cơ sở vật chất mà không khen chê rõ rệt.
   - *Điều kiện:* **Bắt buộc có Aspect**.

---

## 📌 QUY TẮC 4: ĐỊNH NGHĨA 2 NHÓM NHÃN NGOÀI CẢM XÚC

### 1. `hoi_dap` (Thắc mắc / Hỏi đáp học tập & quy chế)
- Các câu hỏi, thắc mắc cần giải đáp liên quan trực tiếp đến đời sống học thuật và đào tạo tại UIT:
  - Hỏi quy chế điểm danh, làm tròn điểm, phúc khảo, chuẩn đầu ra (TOEIC, CNTT).
  - Hỏi cách học môn học, xin tài liệu, xin đề thi, hỏi lịch đăng ký môn học (ĐKMH).
  - Hỏi thủ tục hành chính tại PĐT (DAA), CTSV, chuyển ngành, nộp chứng chỉ.

### 2. `khong_lien_quan` (Tạp âm / Ngoài lề / Không liên quan đến UIT)
- Mọi bài viết hoặc bình luận **KHÔNG** thuộc các khía cạnh học thuật/cơ sở UIT:
  - Chuyện tình cảm cá nhân, hẹn hò, tìm bạn, tán gẫu, meme vui đùa.
  - Rao vặt, nhượng/pass đồ dùng, tìm đồ thất lạc, rơi ví/thẻ xe.
  - Các bài về ký túc xá (KTX) không thuộc phạm vi đào tạo/cơ sở trường UIT.
  - Mọi bài có cảm xúc bâng quơ nhưng **không gắn với thực thể UIT** nào.

---

## 📌 QUY TẮC 5: DANH MỤC CÁC KHÍA CẠNH (ASPECTS) - ĐÃ LOẠI BỎ KÝ TÚC XÁ
Danh mục chính thức gồm 7 khía cạnh cốt lõi của UIT:
1. `giang_vien`: Tác phong, phương pháp giảng dạy, tính điểm của thầy/cô.
2. `chuong_trinh`: Nội dung môn học, độ khó, tính thực tế, bài tập lớn/Lab.
3. `co_so_vat_chat`: Phòng học, máy lạnh, thang máy, wifi, căn tin, thư viện trường.
4. `hoc_phi`: Mức học phí, chính sách tăng học phí, học bổng, miễn giảm.
5. `thi_cu`: Đề thi, coi thi, làm tròn điểm, phúc khảo, gian lận thi cử.
6. `hanh_chinh`: Thủ tục ĐKMH, phòng DAA, cấp bảng điểm, xác nhận sinh viên.
7. `doan_hoi`: Câu lạc bộ, Đoàn - Hội, hoạt động ngoại khóa, ngày CTXH, DRL.

*(Lưu ý: Khía cạnh `ky_tuc_xa` đã được loại bỏ hoàn toàn khỏi bộ đánh giá).*

---

## 📌 QUY TẮC 6: XỬ LÝ SARCASM (MỈA MAI / CHÂM BIẾM)
- Khi bài viết sử dụng ngôn từ tích cực bề nổi nhưng mang hàm ý chỉ trích (hoặc ngược lại):
  - Cờ `sarcasm = 1`.
  - **Nhãn gán theo Ý THẬT NGỤ Ý** (thường là `tieu_cuc`).
