# Hiệu chỉnh selector (tuần 2)
1. Chạy Chrome có giao diện, mở 1 bài mẫu, DevTools → xác nhận trong `configs/config.yaml > selectors`:
   `article`, `permalink`, `text_nodes`, `see_more_xpath`, `more_comments_xpath`, `reply_xpath`.
2. Ưu tiên thuộc tính ngữ nghĩa (`role`, `aria-*`, văn bản hiển thị); tránh class tự sinh. Thêm selector dự phòng (dùng dấu phẩy CSS / `or` XPath).
3. Điền 2–3 URL bài đã biết vào `health_check`; nếu lệch, phiên dừng.
4. Thời gian: `time_raw` luôn được lưu; kiểm tra `created_at` parse đúng trên 20 bài (đặc biệt dạng tương đối "3 tuần").
5. Số reaction/bình luận (`reactions`, `n_comments`) chưa được trích mặc định: thêm vào `_parse_article` sau khi xác định selector, dùng `parse_count`.
6. Tiêu chí: chạy 50 bài, so khớp tay 20 bài ≥ 95%, không trùng, dừng/tiếp tục đúng checkpoint.
7. Kiểm tra bình luận: xác nhận `JS_COMMENTS` không lọt tên người dùng (đối chiếu 10 bài).
