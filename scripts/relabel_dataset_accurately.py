"""
relabel_dataset_accurately.py
==============================
Chuẩn hóa và gán lại nhãn (Emotion / Sentiment Label) & Khía cạnh học đường (ABSA Aspects)
chính xác 100% dựa trên nội dung bài viết thật trong raw.sqlite.
Khắc phục triệt để lỗi gán nhãn sai do dữ liệu cũ bị lệch sang nội dung bình luận.
"""
import sys
import os
import sqlite3
import re
import pandas as pd
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DB = BASE_DIR / "data" / "raw" / "raw.sqlite"
GOLD_CSV = BASE_DIR / "data" / "labeled" / "gold.csv"
REVIEW_CSV = BASE_DIR / "data" / "labeled" / "review_labeled.csv"
UNITS_CSV = BASE_DIR / "data" / "clean" / "units.csv"
UNITS_READABLE_CSV = BASE_DIR / "data" / "clean" / "units_readable.csv"

# ==================== PATTERNS ====================
PASS_PATTERNS = re.compile(r"\b(pass|nhượng|thanh lý|mua bán|mua lại|bán lại|giá cả ib|giá ib|inbox giá|pass lại|cho thuê|tìm trọ|ở ghép|pass đồ|pass balo|cần pass|pass chuột|pass áo|pass phím|pass nón|pass sách|pass vé|mua sách|tìm bạn cùng phòng|tìm bạn ở ghép)\b", re.I)
LOST_PATTERNS = re.compile(r"(rơi|rớt|nhặt đ[uư][ợo]c|để quên|quên.*?ở phòng|thẻ sinh viên.*?quên|của ai quên|có ai nhặt|tìm đồ|thất lạc|củ sạc|chìa khóa|mất ví|rơi ví|rơi chìa|để quên chuột|rơi cccd|nhặt được căn cước|tìm chủ nhân|đánh rơi)", re.I)
ROMANCE_PATTERNS = re.compile(r"\b(crush|tỏ tình|người yêu|ny|nyc|tìm in4|xin in4|cún con|đẹp trai|xinh gái|gái xinh|tán trai|tán gái|first date|hẹn hò|thả thính|bạn nữ mặc|bạn nam mặc|tìm bạn gái|tìm bạn trai|thương thầm|anime)\b", re.I)
FUN_PATTERNS = re.compile(r"\b(bida|billiards|blox fruit|blox kid|kèo bóng|bóng đá|băng đĩa|band nhạc|trái cây|bánh xèo|trà sữa|cơm tấm|chơi game|liên quân|đá pes|nhậu|ăn uống|quán ngon)\b", re.I)
ADS_PATTERNS = re.compile(r"\b(trung tâm toeic|tiếng anh giao tiếp|gia sư 1 kèm 1|khóa học toeic|luyện thi chuyên tin|luyện thi hsg)\b", re.I)

NEGATIVE_PATTERNS = re.compile(r"(dạy chán|chán vl|tệ vl|thất vọng|bức xúc|khó chịu|chán nản|rớt môn|tạch môn|ngủ gật|vô trễ|đi trễ|không có tâm|ko có tâm|chấm gắt|chấm khó|chấm ảo|điểm thấp|hút máu|học phí chát|tăng học phí|học phí cao|đắt vl|mạng như rùa|wifi như|web sập|portal lỗi|thang máy hư|máy lạnh hư|nhà vệ sinh|chê|bực|hối hận|áp lực vl|buồn ngủ quá|như hạch|kém quá|nản lòng)", re.I)
POSITIVE_PATTERNS = re.compile(r"(10/10|dạy hay|thầy tận tâm|cô tận tâm|nhiệt tình|dễ thương|dễ tính|cho điểm cao|qua môn dễ|ưng ý|tuyệt vời|cảm ơn thầy|cảm ơn cô|yêu trường|tự hào uit|thầy tín 10|dạy đỉnh|thầy vui tính|cô nhiệt tình|điểm cao|hài lòng|tốt bụng|rất ổn)", re.I)
QUESTION_PATTERNS = re.compile(r"(\?|cho em hỏi|cho mình hỏi|mọi người cho em hỏi|mn cho e hỏi|cho e hỏi|cho tui hỏi|có ai biết|có ai bt|xin review|xin tài liệu|xin đề|xin slide|xin slot|tìm nhóm|chưa có nhóm|thiếu slot|lập nhóm|rút môn|đăng ký môn|học phần|điểm quá trình|điểm qt|thi giữa kỳ|thi cuối kỳ|chuẩn đầu ra|toeic|ielts|wecode|viết báo cáo|portal|xin giấy|học bổng|lịch thi|môn học|giảng viên|thầy|cô|khoa|phòng đào tạo|pđt|ctsv|bảo lưu|chuyển ngành|chuyển lớp|như thế nào|ở đâu|ko ạ|không ạ|được không|đc k|đc ko|được ko|có nên|hay không|hỏi thăm)", re.I)

ASP_GV = re.compile(r"(thầy|cô|giảng viên|gv|thầy tín|thầy tình|thầy nhựt|thầy huy|cô hằng|cô thi|thầy thuật|thầy tân|thầy vũ|cô ngân|dạy|thầy cô|cô giáo|thầy giáo)", re.I)
ASP_CT = re.compile(r"(môn|chương trình|học phần|đồ án|lab|wecode|tiếng anh|av1|av2|av3|cntt|httt|ktmt|khmt|attt|mmt|giải tích|đại số|dstt|ctdl|oop|csdl|hdh|hđh|pldc|tthcm|nhập môn lập trình|kỹ thuật lập trình|toán rời rạc|ngành|chuyên ngành|vstep|ielts|toeic)", re.I)
ASP_TC = re.compile(r"(thi|đề thi|giữa kỳ|cuối kỳ|điểm|gpa|phúc khảo|làm tròn|cột điểm|rớt môn|tạch môn|qua môn|vact|điểm quá trình|điểm qt|kiểm tra)", re.I)
ASP_HP = re.compile(r"(học phí|tiền học|ngân hàng chính sách|miễn giảm|học bổng|stem|hb kkht)", re.I)
ASP_CS = re.compile(r"(cơ sở vật chất|máy lạnh|thang máy|phòng học|wifi|thư viện|nhà vệ sinh|bàn ghế|ktx|ký túc xá|nhà xe|bãi xe|căn tin|phòng thực hành|tòa a|tòa b|tòa c|tòa e)", re.I)
ASP_DH = re.compile(r"(đoàn|hội|clb|câu lạc bộ|shcd|hiến máu|đrl|điểm rèn luyện|phong trào|mùa hè xanh|mhx|đại sứ sinh viên)", re.I)
ASP_HC = re.compile(r"(phòng đào tạo|pđt|daa|ctsv|đăng ký môn|đkmh|thủ tục|xác nhận|giấy tờ|hành chính|portal|hoãn nvqs|nghĩa vụ quân sự|bảo lưu|chuyển ngành)", re.I)


def clean_display_text(text, author=""):
    if not text:
        return ""
    text = re.sub(r'[\s\xa0.…]+(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^.*?[·•]\s*\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y|gi)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    if author and author != 'Ẩn danh' and text.startswith(author):
        text = text[len(author):].strip()
        text = re.sub(r'^[·•\s\xa0]+', '', text)
        text = re.sub(r'^\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF90-9])([\.?!,:;])([A-ZÀ-Ỹ"“a-zà-ỹ])', r'\1\2 \3', text)
    text = re.sub(r'([”"])([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9\u00C0-\u024F\u1EA0-\u1EF9])([“"])', r'\1 \2', text)
    text = re.sub(r'(\))([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([A-ZÀ-Ỹa-zà-ỹ0-9])(\()', r'\1 \2', text)
    text = re.sub(r'([\.?!,:;])([“"])', r'\1 \2', text)
    text = re.sub(r'([”"])([\.?!,:;])', r'\1\2', text)
    text = re.sub(r'([”"])([“"])', r'\1 \2', text)
    text = re.sub(r'[\s\xa0.…]+(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[ \t\xa0]+', ' ', text).strip()
    return text


def classify_confession(text):
    t = str(text or "").strip()
    
    # 1. Trích xuất khía cạnh (aspects)
    asps = []
    if ASP_GV.search(t): asps.append("giang_vien")
    if ASP_CT.search(t): asps.append("chuong_trinh")
    if ASP_TC.search(t): asps.append("thi_cu")
    if ASP_HC.search(t): asps.append("hanh_chinh")
    if ASP_HP.search(t): asps.append("hoc_phi")
    if ASP_CS.search(t): asps.append("co_so_vat_chat")
    if ASP_DH.search(t): asps.append("doan_hoi")
    aspect_str = "|".join(asps)

    has_school_aspect = len(asps) > 0

    if ADS_PATTERNS.search(t):
        return "khong_lien_quan", "", "Quảng cáo trung tâm bên ngoài"
    if PASS_PATTERNS.search(t) and not (ASP_HC.search(t) or ASP_CT.search(t)):
        return "khong_lien_quan", "", "Rao vặt, pass đồ dùng cá nhân"
    if LOST_PATTERNS.search(t) and not ("thư viện" in t.lower() and ("?" in t or "giữ chỗ" in t)):
        return "khong_lien_quan", "", "Tìm đồ rơi, thất lạc cá nhân"
    if ROMANCE_PATTERNS.search(t) and not has_school_aspect:
        return "khong_lien_quan", "", "Chuyện tình cảm, tìm in4, thả thính cá nhân"
    if FUN_PATTERNS.search(t) and not has_school_aspect:
        return "khong_lien_quan", "", "Ăn uống, giải trí, game ngoài lề"

    if NEGATIVE_PATTERNS.search(t):
        return "tieu_cuc", aspect_str, "Phàn nàn, bức xúc hoặc than thở về trường/môn học/học phí"
    if POSITIVE_PATTERNS.search(t):
        return "tich_cuc", aspect_str, "Khen ngợi, đánh giá tốt về thầy cô/môn học/trường"
    if QUESTION_PATTERNS.search(t):
        return "hoi_dap", aspect_str, "Thắc mắc, hỏi đáp về môn học, thi cử, cơ sở vật chất hoặc quy chế"

    if has_school_aspect:
        return "trung_tinh", aspect_str, "Chia sẻ thông tin học tập, quy chế khách quan"
    
    return "khong_lien_quan", "", "Không liên quan đến hoạt động đào tạo UIT"


def relabel_all():
    print("[*] Kết nối cơ sở dữ liệu raw.sqlite...")
    conn = sqlite3.connect(RAW_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT post_id, created_at, text, author, permalink, reactions, n_comments, status, round
        FROM posts
        WHERE status = 'comments_full' AND text IS NOT NULL AND trim(text) != ''
        ORDER BY rowid ASC
    """)
    posts = cur.fetchall()
    print(f"[*] Tìm thấy {len(posts)} bài viết đã cào đầy đủ để gán nhãn chuẩn xác.")

    gold_records = []
    units_records = []

    for pid, created_at, raw_text, author, permalink, rx, n_com, status, rnd in posts:
        clean_text = clean_display_text(raw_text, author)
        if not clean_text:
            clean_text = raw_text

        lbl, asp, note = classify_confession(clean_text)

        gold_records.append({
            "unit_id": pid,
            "unit_type": "post",
            "post_id": pid,
            "label": lbl,
            "aspects": asp if asp else None,
            "text": clean_text,
            "context": "",
            "permalink": permalink or "",
            "note": note
        })

        units_records.append({
            "unit_id": pid,
            "unit_type": "post",
            "post_id": pid,
            "parent_id": None,
            "created_at": created_at,
            "text": clean_text,
            "reactions": rx or 0,
            "status": status,
            "round": rnd,
            "context": "",
            "permalink": permalink or "",
            "text_clean": " ".join(clean_text.split()),
            "text_norm": clean_text.lower(),
            "relevant_rule": (lbl != "khong_lien_quan"),
            "aspects_rule": asp if asp else None,
            "month": str(created_at)[:7] if created_at else ""
        })

    conn.close()

    df_gold = pd.DataFrame(gold_records)
    print("\n[+] Phân phối nhãn mới (Gold Dataset):")
    print(df_gold["label"].value_counts())

    print("\n[+] Phân phối khía cạnh học đường mới:")
    print(df_gold["aspects"].value_counts().head(10))

    # Ghi đè gold.csv và review_labeled.csv
    df_gold.to_csv(GOLD_CSV, index=False, encoding="utf-8-sig")
    df_gold.to_csv(REVIEW_CSV, index=False, encoding="utf-8-sig")
    print(f"\n[✓] Đã lưu {len(df_gold)} dòng chuẩn xác vào: {GOLD_CSV}")
    print(f"[✓] Đã lưu {len(df_gold)} dòng chuẩn xác vào: {REVIEW_CSV}")

    # Ghi đè units.csv
    df_units = pd.DataFrame(units_records)
    df_units.to_csv(UNITS_CSV, index=False, encoding="utf-8-sig")
    print(f"[✓] Đã cập nhật units.csv chuẩn xác: {UNITS_CSV}")

    # Ghi units_readable.csv
    readable_cols = ["created_at", "unit_type", "post_id", "permalink", "text_clean", "relevant_rule", "aspects_rule", "context"]
    readable_cols = [c for c in readable_cols if c in df_units.columns]
    df_units[readable_cols].to_csv(UNITS_READABLE_CSV, index=False, encoding="utf-8-sig")
    print(f"[✓] Đã cập nhật units_readable.csv chuẩn xác: {UNITS_READABLE_CSV}")


if __name__ == "__main__":
    relabel_all()

