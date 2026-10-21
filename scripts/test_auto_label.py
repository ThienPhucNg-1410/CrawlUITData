import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import pandas as pd

df = pd.read_csv("data/clean/units.csv")
print(f"Total units to label: {len(df)}")

PASS_PATTERNS = re.compile(r"\b(pass|nhượng|thanh lý|mua bán|mua lại|bán lại|giá cả ib|giá ib|inbox giá|pass lại|cho thuê|tìm trọ|ở ghép|pass đồ|pass balo|cần pass|pass chuột|pass áo)\b", re.I)
LOST_PATTERNS = re.compile(r"(rơi|rớt|nhặt đ[uư][ợo]c|để quên|quên.*?ở phòng|thẻ sinh viên.*?quên|của ai quên|có ai nhặt|tìm đồ|thất lạc|củ sạc|chìa khóa|mất ví|rơi ví|rơi chìa|để quên chuột)", re.I)
ROMANCE_PATTERNS = re.compile(r"\b(crush|tỏ tình|người yêu|ny|nyc|tìm in4|xin in4|cún con|đẹp trai|xinh gái|gái xinh|tán trai|tán gái|first date|hẹn hò|thả thính|bạn nữ mặc|bạn nam mặc)\b", re.I)
FUN_PATTERNS = re.compile(r"\b(bida|billiards|blox fruit|blox kid|kèo bóng|bóng đá|băng đĩa|band nhạc|trái cây|bánh xèo|trà sữa|cơm tấm|chơi game|liên quân)\b", re.I)

NEGATIVE_PATTERNS = re.compile(r"(dạy chán|chán vl|tệ vl|thất vọng|bức xúc|khó chịu|chán nản|rớt môn|tạ môn|ngủ gật|vô trễ|đi trễ|không có tâm|ko có tâm|chấm gắt|chấm khó|điểm thấp|hút máu|học phí chát|tăng học phí|mạng như rùa|wifi như|web sập|portal lỗi|thang máy hư|máy lạnh hư|nhà vệ sinh)", re.I)
POSITIVE_PATTERNS = re.compile(r"(10/10|dạy hay|thầy tận tâm|cô tận tâm|nhiệt tình|dễ thương|dễ tính|cho điểm cao|qua môn dễ|ưng ý|tuyệt vời|cảm ơn thầy|cảm ơn cô|yêu trường|tự hào uit|thầy tín 10|dạy đỉnh)", re.I)

QUESTION_PATTERNS = re.compile(r"(\?|cho em hỏi|cho mình hỏi|mọi người cho em hỏi|mn cho e hỏi|cho e hỏi|cho tui hỏi|có ai biết|có ai bt|xin review|xin tài liệu|xin đề|xin slide|xin slot|tìm nhóm|chưa có nhóm|thiếu slot|lập nhóm|rút môn|đăng ký môn|học phần|điểm quá trình|điểm qt|thi giữa kỳ|thi cuối kỳ|chuẩn đầu ra|toeic|ielts|wecode|viết báo cáo|portal|xin giấy|học bổng|lịch thi|môn học|giảng viên)", re.I)

# Aspect cues
ASP_GV = re.compile(r"(thầy|cô|giảng viên|gv|thầy tín|thầy tình|thầy nhựt|thầy huy|cô hằng|cô thi)", re.I)
ASP_CT = re.compile(r"(môn|chương trình|học phần|đồ án|lab|wecode|tiếng anh|av1|av2|av3|cntt|httt|ktmt|khmt|attt|mmt)", re.I)
ASP_TC = re.compile(r"(thi|đề thi|giữa kỳ|cuối kỳ|điểm|gpa|phúc khảo|làm tròn)", re.I)
ASP_HP = re.compile(r"(học phí|tiền học|ngân hàng chính sách|miễn giảm|học bổng)", re.I)
ASP_CS = re.compile(r"(cơ sở vật chất|máy lạnh|thang máy|phòng học|wifi|thư viện|nhà vệ sinh|bàn ghế|ktx)", re.I)
ASP_DH = re.compile(r"(đoàn|hội|clb|câu lạc bộ|shcd|hiến máu|đrl|điểm rèn luyện)", re.I)

def classify_text(text):
    t = str(text or "")
    # 1. Kiểm tra không liên quan trước
    if PASS_PATTERNS.search(t):
        return "khong_lien_quan", "Rao vặt, pass đồ, mua bán"
    if LOST_PATTERNS.search(t):
        return "khong_lien_quan", "Tìm đồ rơi, nhặt được đồ thất lạc"
    if ROMANCE_PATTERNS.search(t):
        return "khong_lien_quan", "Chuyện tình cảm, tìm in4, thả thính ngoài lề"
    if FUN_PATTERNS.search(t):
        return "khong_lien_quan", "Hoạt động ăn uống giải trí ngoài lề"

    # 2. Kiểm tra khen / chê về trường / thầy cô
    if NEGATIVE_PATTERNS.search(t):
        return "tieu_cuc", "Bày tỏ không hài lòng, phàn nàn về trường/thầy cô/môn học"
    if POSITIVE_PATTERNS.search(t):
        return "tich_cuc", "Khen ngợi, đánh giá tốt về thầy cô/môn học"

    # 3. Kiểm tra hỏi đáp học tập
    if QUESTION_PATTERNS.search(t):
        return "hoi_dap", "Hỏi đáp thắc mắc về môn học, thi cử, quy chế đào tạo"

    # 4. Mặc định: trung tính
    return "trung_tinh", "Chia sẻ thông tin khách quan"

def extract_aspects(text):
    t = str(text or "")
    asps = []
    if ASP_GV.search(t): asps.append("giang_vien")
    if ASP_CT.search(t): asps.append("chuong_trinh")
    if ASP_TC.search(t): asps.append("thi_cu")
    if ASP_HP.search(t): asps.append("hoc_phi")
    if ASP_CS.search(t): asps.append("co_so_vat_chat")
    if ASP_DH.search(t): asps.append("doan_hoi")
    return "|".join(asps)

labels = []
notes = []
aspects = []
for txt in df["text"]:
    lbl, nt = classify_text(txt)
    labels.append(lbl)
    notes.append(nt)
    aspects.append(extract_aspects(txt))

df["label"] = labels
df["aspects"] = aspects
df["note"] = notes

print("\n--- PHÂN PHỐI NHÃN MỚI ---")
print(df["label"].value_counts())
