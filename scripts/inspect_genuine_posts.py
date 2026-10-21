import pandas as pd, sys, re
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")

df = pd.read_csv("data/labeled/review_labeled.csv")

AD_ENGLISH = re.compile(
    r"(ares english|toeic buddies|izone|ielts fighter|anh ngữ|trung tâm tiếng anh|trung tâm ngoại ngữ|khoá học toeic|khóa học toeic|khoá học ielts|khóa học ielts|luyện thi toeic|luyện thi ielts|lấy lại căn bản|mất gốc.*toeic|đảm bảo đầu ra.*toeic|cam kết đầu ra|học phí siêu sinh viên|ưu đãi học phí|đăng ký khoá học|combo 4 kỹ năng|thầy hùng cô nhi|tt ngoại ngữ|học toeic phí rẻ|thi máy iig)",
    re.I
)

REPLY_INDICATORS = re.compile(
    r"(\b(nha em|nhé em|đi em|nha bạn|nhé bạn|nha b|nhé b|đâu em|đâu bạn|hả bạn|hả e|hả em|chưa em|chưa b|chưa bạn|vậy bạn|vậy em|nhé chủ tus|nha chủ tus|v bạn|nha og|nha ông|nè bạn|nè em|nè b|thôi em|thôi b|nè c|nha c)\b|"
    r"^(đương nhiên|học ít|xài vina|tháng 11|cho tui chơi|bá khí|được nha|đc nha|k tính điểm|nếu được|csdl khong có|sáng nay thi ko đc|pldc in hết|đã từng rất|mr đtn|đừng dùng|có thì có mà|trường mình k áp lực|nhưng mà thư viện|đều là sinh viên|ngồi kế auto|lên gg search|tái bản mấy|bạn tìm tôi|lớp thầy .* hả|đã có đi nhận|có môn .* chưa|bạn học .* à|đi hc nhóm có|bạn khách có|đã qua phòng|hảo hoàng|trong kỳ này còn|tui tham gia|ụa sinh viên|up lên đi|quần dài đi|hoàng gia bảo|em lên a101|nhà văn hoá sinh viên|mình có điểm pk|cho tui xin slot|cho mình xin slot|bạn liên hệ|đăng ký ở|đợi thông báo|liên hệ ctsv|lên phòng đào tạo|vào daa|vào portal|lên web trường|chúc mừng bạn|tùy em|tùy bạn|inbox mình|ib mình|mình pass|pass lại|mình có nè)\b)",
    re.I
)

genuine_samples = []
for r in df.itertuples():
    t = str(r.text)
    if AD_ENGLISH.search(t): continue
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    first_line = lines[0] if lines else ""
    words = first_line.split()
    is_tag = (len(words) in (2, 3, 4) and len(lines) >= 2 and len(t) < 120 and words[0][0].isupper() and words[1][0].isupper() and not first_line.endswith("?"))
    is_reply = bool(REPLY_INDICATORS.search(t))
    is_short_answer = (len(t) < 100 and not any(q in t.lower() for q in ["cho em hỏi", "cho mình hỏi", "mn cho em hỏi", "mọi người cho", "review", "cfs", "#uit", "thắc mắc"]))

    if not (is_reply or is_tag or is_short_answer):
        genuine_samples.append((r.unit_id, t))

print(f"Tổng số bài gốc thuần túy: {len(genuine_samples)}")
print("\n--- 10 bài gốc đầu tiên ---")
for uid, text in genuine_samples[:10]:
    print(f"\n[{uid}]:\n{text[:150]}...")

