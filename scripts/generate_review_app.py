import os, sys, re, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

# 1. Đọc dữ liệu sạch
units_path = "data/clean/units.csv"
if not os.path.exists(units_path):
    print("Không tìm thấy data/clean/units.csv")
    sys.exit(1)

df = pd.read_csv(units_path)
print(f"[+] Đã đọc {len(df)} units từ {units_path}")

# 2. Định nghĩa các Regex Patterns theo Rule v4.1 (7 ASPECTS UIT, KHÔNG KTX)
ASP_CT = re.compile(r"\b(môn|môn học|học phần|đồ án|lab|wecode|chương trình|tài liệu|slide|giáo trình|bài giảng|bài tập|chuẩn đầu ra|cntt|httt|ktmt|khmt|attt|mmt|tmdt|tkvm|giải tích|đại số|dstt|ctdl|oop|csdl|hdh|hđh|nmlt|ktdl)\b", re.I)
ASP_TC = re.compile(r"\b(thi|đề thi|kỳ thi|giữa kỳ|cuối kỳ|gpa|cpa|điểm|phúc khảo|làm tròn|điểm quá trình|điểm qt|điểm thi|rớt môn|nợ môn|học lại|thi lại|cột điểm)\b", re.I)
ASP_HP = re.compile(r"\b(học phí|tiền học|tín chỉ|học bổng|hb|kkht|stem|miễn giảm|hỗ trợ chi phí|ngân hàng chính sách|vay vốn)\b", re.I)
ASP_CS = re.compile(r"\b(cơ sở vật chất|csvc|máy lạnh|điều hòa|quạt|thang máy|phòng học|phòng lab|wifi|mạng trường|thư viện|tvtt|bàn ghế|nhà vệ sinh|wc|bãi xe|gửi xe|nhà xe|tòa a|tòa b|tòa c|tòa e|toà a|toà b|toà c|toà e|tòa|toà|nhà phục vụ|căn tin|canteen)\b", re.I)
ASP_HC = re.compile(r"\b(phòng đào tạo|pđt|pdt|ctsv|phòng công tác sinh viên|bảo lưu|chuyển ngành|chuyển trường|rút môn|đăng ký môn|dkmh|portal|daa|giấy xác nhận|bảng điểm|thủ tục)\b", re.I)
ASP_DH = re.compile(r"\b(đoàn|hội|clb|câu lạc bộ|shcd|sinh hoạt công dân|hiến máu|đrl|điểm rèn luyện|tình nguyện|xuân tình nguyện|xtn|mùa hè xanh|mhx)\b", re.I)

def extract_aspects(text):
    t = str(text or "")
    asps = []
    # Kiểm tra Giảng viên: tránh bắt nhầm 'mấy cô' căn tin, 'cô lao công', 'cô là phụ huynh'
    is_gv = False
    if re.search(r"\b(thầy cô|giảng viên|gv|cố vấn học tập|cvht|trợ giảng|ta)\b", t, re.I):
        is_gv = True
    elif re.search(r"\b(thầy)\b", t, re.I):
        is_gv = True
    elif re.search(r"\b(cô)\b", t, re.I):
        if not re.search(r"(cô là ph|cô là phụ huynh|mấy cô|cô lao công|cô bán|cô phục vụ|cô quét)", t, re.I):
            is_gv = True
    if is_gv:
        asps.append("giang_vien")
    if ASP_CT.search(t): asps.append("chuong_trinh")
    if ASP_TC.search(t): asps.append("thi_cu")
    if ASP_HP.search(t): asps.append("hoc_phi")
    if ASP_CS.search(t): asps.append("co_so_vat_chat")
    if ASP_HC.search(t): asps.append("hanh_chinh")
    if ASP_DH.search(t): asps.append("doan_hoi")
    return asps

# 3. NHẬN DIỆN QUẢNG CÁO KHÓA HỌC NGOÀI (Ares English, Toeic, Ielts, Lái xe...) -> BỎ QUA TUYỆT ĐỐI
AD_ENGLISH_PATTERNS = re.compile(
    r"(ares english|toeic buddies|izone|ielts fighter|anh ngữ|trung tâm tiếng anh|trung tâm ngoại ngữ|khoá học toeic|khóa học toeic|khoá học ielts|khóa học ielts|khoá toeic|khóa toeic|lớp toeic|lớp ielts|luyện thi toeic|luyện thi ielts|lấy lại căn bản|mất gốc.*toeic|đảm bảo đầu ra.*toeic|cam kết đầu ra|học phí siêu sinh viên|ưu đãi học phí|đăng ký khoá học|combo 4 kỹ năng|thầy hùng cô nhi|tt ngoại ngữ|học toeic phí rẻ|thi máy iig|đào tạo lái xe|bằng lái)",
    re.I
)

# 4. NHẬN DIỆN COMMENT/REPLY VÀ BÀI GỐC CHUẨN XÁC
POST_PATTERNS = re.compile(
    r"^(#cfs|\[cfs\]|confession|chào mọi người|chào mn|mọi người cho|mn cho|dạ cho em hỏi|admin duyệt|ad duyệt|góc pass|cần pass|tìm đồ|nhặt được|tìm trọ|ở ghép)",
    re.I
)
REPLY_INDICATORS = re.compile(
    r"(\b(chủ tus|chủ thớt|thớt|nha em|nhé em|đi em|nha bạn|nhé bạn|nha b|nhé b|đâu em|đâu bạn|hả bạn|hả e|hả em|chưa em|chưa b|chưa bạn|vậy bạn|vậy em|nè bạn|nè em|nè b|thôi em|thôi b|nè c|nha c|nha anh|nhé anh)\b|"
    r"\b(chúc em|chúc bạn|khuyên em|khuyên bạn|welcome e|welcome em|cố lên|yên tâm|đừng lo|đừng bỏ|mình từng|mình thấy|mình cựu|anh từng|anh thấy|chị từng|hồi anh|hồi a|hồi mình|năm ngoái|trước anh|a năm|anh năm|hồi trc|hồi trước)\b|"
    r"^(rì viu|review vài|tips sinh tồn|nhà phục vụ sv|chuẩn bị giày|khả năng dữ liệu|bổ sung chứng chỉ|không bắt buộc|mọi sự kiện|cô \[gv\]|thầy \[gv\]|mr đtn|ok,|có gì đâu|thời gian đào tạo|làm nghiên cứu|tức là lớp)\b|"
    r"^\s*[-+*•]\s+)",
    re.I
)

# Patterns ngoài lề khác
PASS_PATTERNS = re.compile(r"\b(pass|nhượng|thanh lý|mua bán|mua lại|bán lại|giá cả ib|giá ib|inbox giá|pass lại|cho thuê|tìm trọ|ở ghép|pass đồ|pass balo|cần pass|pass chuột|pass áo|pass sách|pass vé|mua sách|tìm bạn cùng phòng|tìm bạn ở ghép)\b", re.I)
LOST_PATTERNS = re.compile(r"(rơi|rớt|nhặt đ[uư][ợo]c|để quên|quên.*?ở phòng|thẻ sinh viên.*?quên|của ai quên|có ai nhặt|tìm đồ|thất lạc|củ sạc|chìa khóa|mất ví|rơi ví|rơi chìa|để quên chuột|rơi cccd|nhặt được căn cước|tìm chủ nhân|đánh rơi)", re.I)
ROMANCE_PATTERNS = re.compile(r"\b(crush|tỏ tình|người yêu|ny|nyc|tìm in4|xin in4|cún con|đẹp trai|xinh gái|gái xinh|tán trai|tán gái|first date|hẹn hò|thả thính|bạn nữ mặc|bạn nam mặc|tìm bạn gái|tìm bạn trai|thương thầm|mê trai|mê gái)\b", re.I)
FUN_PATTERNS = re.compile(r"\b(bida|billiards|blox fruit|blox kid|kèo bóng|bóng đá|băng đĩa|band nhạc|trái cây|bánh xèo|trà sữa|cơm tấm|chơi game|liên quân|đá pes|nhậu|ăn uống|quán ngon)\b", re.I)

# Patterns cảm xúc & hỏi đáp
NEGATIVE_PATTERNS = re.compile(r"(dạy chán|chán vl|tệ vl|thất vọng|bức xúc|khó chịu|chán nản|rớt môn|tạ môn|ngủ gật|vô trễ|đi trễ|không có tâm|ko có tâm|chấm gắt|chấm khó|chấm ảo|điểm thấp|hút máu|học phí chát|tăng học phí|học phí cao|đắt vl|mạng như rùa|wifi như|web sập|portal lỗi|thang máy hư|máy lạnh hư|nhà vệ sinh|chê|bực|hối hận|áp lực vl|ức chế|dạy tệ|\bcay\b|còn cay)", re.I)
POSITIVE_PATTERNS = re.compile(r"(10/10|dạy hay|thầy tận tâm|cô tận tâm|nhiệt tình|dễ thương|dễ tính|cho điểm cao|qua môn dễ|ưng ý|tuyệt vời|cảm ơn thầy|cảm ơn cô|yêu trường|tự hào uit|thầy tín 10|dạy đỉnh|thầy vui tính|cô nhiệt tình|điểm cao|hài lòng|tốt bụng|xuất sắc)", re.I)
QUESTION_PATTERNS = re.compile(r"(\?|cho em hỏi|cho mình hỏi|mọi người cho em hỏi|mn cho e hỏi|cho e hỏi|cho tui hỏi|có ai biết|có ai bt|xin review|xin tài liệu|xin đề|xin slide|xin slot|tìm nhóm|chưa có nhóm|thiếu slot|lập nhóm|hỏi về|tư vấn|làm sao để|như thế nào|bao giờ|ở đâu)", re.I)

existing_user_labels = {}
if os.path.exists("data/labeled/review_labeled.csv"):
    try:
        old_df = pd.read_csv("data/labeled/review_labeled.csv", dtype={"unit_id": str})
        for _, r_old in old_df.iterrows():
            ouid = str(r_old["unit_id"]).strip()
            olbl = str(r_old.get("label", "")).strip()
            onote = str(r_old.get("note", "")).strip()
            if olbl and olbl in ['trung_tinh', 'hoi_dap', 'khong_lien_quan', 'tieu_cuc', 'tich_cuc']:
                existing_user_labels[ouid] = (olbl, onote)
        print(f"[+] Đã đọc và bảo toàn {len(existing_user_labels)} nhãn hiện có từ data/labeled/review_labeled.csv")
    except Exception as e:
        print(f"[!] Warning reading old labels: {e}")

post_labels = {}
post_asps = {}
records = []

for r in df.itertuples():
    uid = str(r.unit_id)
    txt = " ".join(str(getattr(r, 'text_clean', getattr(r, 'text', ''))).split())
    ctx = " ".join(str(getattr(r, 'context', '')).split()) if pd.notna(getattr(r, 'context', None)) else ""
    plink = str(getattr(r, 'permalink', '')) if pd.notna(getattr(r, 'permalink', None)) else ""
    p_id = str(getattr(r, 'post_id', uid))

    # 1. PHÂN LOẠI CHÍNH XÁC BÀI GỐC (POST) vs BÌNH LUẬN (COMMENT)
    # Chỉ các bài mang tiêu đề hỏi chung / confession rõ ràng và không đối thoại mới là Post
    is_genuine_post = bool(POST_PATTERNS.search(txt)) and not bool(REPLY_INDICATORS.search(txt))
    u_type = "post" if is_genuine_post else "comment"

    # 2. XỬ LÝ QUẢNG CÁO TIẾNG ANH NGOÀI (BỎ QUA -> KHÔNG LIÊN QUAN, XÓA ASPECT)
    if AD_ENGLISH_PATTERNS.search(txt) and uid not in existing_user_labels:
        label = "khong_lien_quan"
        note = "Quảng cáo khóa học / trung tâm tiếng Anh ngoài (Bỏ qua)"
        records.append({
            "unit_id": uid, "unit_type": u_type, "post_id": p_id, "label": label,
            "aspects": "", "text": txt, "context": ctx, "permalink": plink, "note": note
        })
        continue

    # Trích xuất khía cạnh UIT
    asps = extract_aspects(txt)

    # 3. Kế thừa từ bài gốc nếu là comment
    if u_type == "comment" and p_id in post_labels:
        parent_label = post_labels[p_id]
        if parent_label == "khong_lien_quan" and uid not in existing_user_labels:
            label = "khong_lien_quan"
            note = "Bình luận thuộc bài gốc không liên quan"
            records.append({
                "unit_id": uid, "unit_type": u_type, "post_id": p_id, "label": label,
                "aspects": "|".join(asps), "text": txt, "context": ctx, "permalink": plink, "note": note
            })
            continue
        elif not asps and p_id in post_asps:
            asps = post_asps[p_id]

    # 4. Phân loại theo các rule chuẩn
    if PASS_PATTERNS.search(txt):
        label, note = "khong_lien_quan", "Rao vặt, pass đồ, tìm trọ ngoài lề"
    elif LOST_PATTERNS.search(txt):
        label, note = "khong_lien_quan", "Tìm đồ rơi, nhặt đồ thất lạc"
    elif ROMANCE_PATTERNS.search(txt):
        label, note = "khong_lien_quan", "Chuyện tình cảm, tìm in4, thả thính cá nhân"
    elif FUN_PATTERNS.search(txt):
        label, note = "khong_lien_quan", "Ăn uống, vui chơi giải trí ngoài lề"
    elif NEGATIVE_PATTERNS.search(txt) and asps:
        label, note = "tieu_cuc", "Phàn nàn/bức xúc về thực thể đào tạo hoặc trường"
    elif POSITIVE_PATTERNS.search(txt) and asps:
        label, note = "tich_cuc", "Khen ngợi/hài lòng về giảng viên/môn học/trường"
    elif QUESTION_PATTERNS.search(txt) and (asps or re.search(r"(học|thi|trường|uit|lớp|kỳ|môn)", txt, re.I)):
        label, note = "hoi_dap", "Thắc mắc/hỏi đáp về quy chế, môn học, hoạt động đào tạo"
    elif asps:
        # BẮT BUỘC CÓ ASPECT MỚI ĐƯỢC LÀ TRUNG TÍNH (đánh giá khách quan thực thể UIT)
        label, note = "trung_tinh", "Đánh giá/thông tin khách quan về cơ sở vật chất, môn học, giáo viên, trường"
    else:
        # Không có aspect nào trong 7 aspect UIT -> KHÔNG LIÊN QUAN
        label, note = "khong_lien_quan", "Không liên quan đến đánh giá thực thể đào tạo UIT"

    # 5. BẢO TỒN TUYỆT ĐỐI NHÃN NGƯỜI DÙNG ĐÃ CHỈNH SỬA / GÁN
    if uid in existing_user_labels:
        u_lbl, u_note = existing_user_labels[uid]
        label = u_lbl
        if u_note:
            note = u_note

    if u_type == "post":
        post_labels[uid] = label
        post_asps[uid] = asps

    records.append({
        "unit_id": uid,
        "unit_type": u_type,
        "post_id": p_id,
        "label": label,
        "aspects": "|".join(asps),
        "text": txt,
        "context": ctx,
        "permalink": plink,
        "note": note
    })

labeled_df = pd.DataFrame(records)
os.makedirs("data/labeled", exist_ok=True)
labeled_df.to_csv("data/labeled/review_labeled.csv", index=False, encoding="utf-8-sig")
labeled_df.to_csv("data/labeled/gold.csv", index=False, encoding="utf-8-sig")

print("\n=== THỐNG KÊ SAU KHI CẬP NHẬT LUẬT MỚI ===")
print("Phân bố nhãn:")
print(labeled_df["label"].value_counts())
print("\nPhân bố loại bài:")
print(labeled_df["unit_type"].value_counts())
print(f"Tổng số units: {len(labeled_df)}")

# 5. Tạo HTML giao diện trực quan với BỘ LỌC CẢI TIẾN
badge_colors = {
    "hoi_dap": "#b45309",
    "khong_lien_quan": "#475569",
    "tieu_cuc": "#b91c1c",
    "tich_cuc": "#15803d",
    "trung_tinh": "#0369a1"
}

html_rows = []
for idx, row in enumerate(records, start=1):
    uid = row["unit_id"]
    u_type = row["unit_type"]
    lbl = row["label"]
    asps_str = row["aspects"]
    txt = row["text"]
    note = row["note"]
    plink = row["permalink"]
    
    is_comm = (u_type == "comment")
    type_badge = '<span class="type-badge comment">BÌNH LUẬN</span>' if is_comm else '<span class="type-badge post">BÀI GỐC</span>'
    tr_class = 'is-comment' if is_comm else 'is-post'

    # Aspect tags
    asps_html = ""
    if asps_str:
        for a in asps_str.split("|"):
            if a.strip():
                asps_html += f'<span class="asp-badge">{a.strip()}</span>'
    else:
        asps_html = '<span style="color:#94a3b8;">-</span>'

    # Select dropdown options
    options = ""
    for opt in ["trung_tinh", "hoi_dap", "khong_lien_quan", "tich_cuc", "tieu_cuc"]:
        sel = "selected" if opt == lbl else ""
        options += f'<option value="{opt}" {sel}>{opt}</option>'

    select_html = f'''<select class="label-select {lbl}" data-uid="{uid}" onchange="updateLabel('{uid}', this.value, this)">{options}</select>'''
    link_html = f'<a href="{plink}" target="_blank" class="fblink">Xem bài FB ↗</a>' if plink else '-'

    html_rows.append(f"""
    <tr class="{tr_class}" data-label="{lbl}" data-type="{u_type}" data-aspects="{asps_str}" data-uid="{uid}">
        <td style="color:#64748b; font-weight:600;">{idx}</td>
        <td>{type_badge}</td>
        <td><code style="font-size:12px; font-weight:600; color:#1e293b;">{uid}</code></td>
        <td>{select_html}</td>
        <td>{asps_html}</td>
        <td class="text-col">{txt}</td>
        <td class="note-col">{note}</td>
        <td>{link_html}</td>
    </tr>
    """)

stats_html = "".join([
    f'''<div class="stat-box" style="border-left-color: {badge_colors.get(k, '#333')};" onclick="setLabelFilter('{k}')">
        <div class="stat-num" style="color: {badge_colors.get(k, '#333')};">{v}</div>
        <div class="stat-lbl">{k}</div>
    </div>'''
    for k, v in labeled_df["label"].value_counts().items()
])

html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hệ Thống Gán Nhãn & Duyệt Dữ Liệu Confession UIT ({len(records)} đơn vị)</title>
<style>
    :root {{
        --primary: #1a365d;
        --bg: #f8fafc;
        --card-bg: #ffffff;
        --border: #e2e8f0;
        --text: #1e293b;
    }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
    .container {{ max-width: 1550px; margin: 0 auto; background: var(--card-bg); padding: 25px 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }}
    
    .header-bar {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid var(--border); padding-bottom: 15px; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: 22px; color: var(--primary); display: flex; align-items: center; gap: 8px; }}
    .header-desc {{ font-size: 13px; color: #64748b; margin-top: 5px; }}
    
    .stats-bar {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
    .stat-box {{ background: #f1f5f9; padding: 10px 18px; border-radius: 8px; border-left: 4px solid var(--primary); min-width: 130px; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }}
    .stat-box:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px rgba(0,0,0,0.08); background: #e2e8f0; }}
    .stat-num {{ font-size: 22px; font-weight: 700; color: #0f172a; }}
    .stat-lbl {{ font-size: 12px; color: #64748b; text-transform: uppercase; font-weight: 600; margin-top: 2px; }}

    /* CONTROL PANEL CẢI TIẾN */
    .controls {{ display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; align-items: center; background: #f8fafc; padding: 14px 18px; border-radius: 10px; border: 1px solid var(--border); }}
    .control-group {{ display: flex; align-items: center; gap: 6px; }}
    .control-label {{ font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; }}
    
    select.filter-select {{
        padding: 8px 12px;
        font-size: 13px;
        font-weight: 600;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #fff;
        color: #1e293b;
        outline: none;
        cursor: pointer;
    }}
    select.filter-select:focus {{ border-color: #2563eb; }}
    
    input#search {{ padding: 8px 14px; font-size: 13px; border: 1px solid #cbd5e1; border-radius: 6px; width: 300px; outline: none; }}
    input#search:focus {{ border-color: #2563eb; ring: 2px solid #bfdbfe; }}
    
    .btn-reset {{
        padding: 8px 14px;
        background: #e2e8f0;
        border: none;
        border-radius: 6px;
        color: #334155;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: background 0.15s;
    }}
    .btn-reset:hover {{ background: #cbd5e1; }}
    
    #count-display {{ margin-left: auto; font-size: 13px; font-weight: 700; color: #0f172a; background: #e0f2fe; padding: 6px 14px; border-radius: 6px; border: 1px solid #bae6fd; }}
    
    .table-wrapper {{ overflow-x: auto; max-height: 75vh; border: 1px solid var(--border); border-radius: 8px; position: relative; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }}
    thead th {{ background: #f1f5f9; color: #334155; font-weight: 600; padding: 12px 10px; border-bottom: 2px solid var(--border); position: sticky; top: 0; z-index: 10; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
    tbody td {{ padding: 10px 10px; border-bottom: 1px solid #e2e8f0; vertical-align: top; }}
    tbody tr:hover {{ background: #f8fafc; }}
    tbody tr.is-comment {{ background: #faf5ff; }}
    tbody tr.is-comment:hover {{ background: #f3e8ff; }}
    
    .type-badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
    .type-badge.post {{ background: #dbeafe; color: #1e40af; }}
    .type-badge.comment {{ background: #f3e8ff; color: #6b21a8; }}
    
    .text-col {{ max-width: 540px; min-width: 320px; line-height: 1.5; word-wrap: break-word; }}
    .note-col {{ max-width: 220px; min-width: 180px; font-size: 12px; color: #475569; line-height: 1.4; }}
    .asp-badge {{ display: inline-block; padding: 2px 7px; border-radius: 4px; font-size: 11px; font-weight: 500; background: #e2e8f0; color: #334155; margin-right: 3px; margin-bottom: 3px; }}
    .fblink {{ color: #2563eb; text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px; background: #eff6ff; border-radius: 4px; border: 1px solid #bfdbfe; font-size: 12px; }}
    .fblink:hover {{ background: #dbeafe; text-decoration: none; }}
    
    .label-select {{
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        border: 2px solid transparent;
        outline: none;
        transition: all 0.2s;
    }}
    .label-select.trung_tinh {{ background: #e0f2fe; color: #0369a1; border-color: #bae6fd; }}
    .label-select.hoi_dap {{ background: #fef3c7; color: #b45309; border-color: #fde68a; }}
    .label-select.khong_lien_quan {{ background: #f1f5f9; color: #475569; border-color: #cbd5e1; }}
    .label-select.tich_cuc {{ background: #dcfce7; color: #15803d; border-color: #bbf7d0; }}
    .label-select.tieu_cuc {{ background: #fee2e2; color: #b91c1c; border-color: #fecaca; }}
    
    .status-toast {{
        position: fixed;
        bottom: 20px;
        right: 25px;
        background: #0f172a;
        color: #fff;
        padding: 10px 18px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-size: 13px;
        display: none;
        align-items: center;
        gap: 8px;
        z-index: 1000;
    }}
    .status-toast.show {{ display: flex; animation: fadeInOut 2.5s forwards; }}
    @keyframes fadeInOut {{
        0% {{ opacity: 0; transform: translateY(10px); }}
        15% {{ opacity: 1; transform: translateY(0); }}
        85% {{ opacity: 1; transform: translateY(0); }}
        100% {{ opacity: 0; transform: translateY(10px); }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header-bar">
        <div>
            <h1>📊 Hệ Thống Gán Nhãn & Duyệt Dữ Liệu Confession UIT</h1>
            <div class="header-desc">
                Dữ liệu mới cào: <strong>{len(records)} đơn vị</strong> | Phân loại chuẩn: <strong>{len(labeled_df[labeled_df["unit_type"]=="post"])} Bài Gốc</strong>, <strong>{len(labeled_df[labeled_df["unit_type"]=="comment"])} Bình Luận</strong> | 
                <span style="color:#059669; font-weight:600;">● Mọi chỉnh sửa nhãn trên web được tự động lưu ngay vào file CSV & CSDL!</span>
            </div>
        </div>
    </div>
    
    <!-- STATS BAR - BẤM VÀO ĐỂ LỌC NHANH -->
    <div class="stats-bar">
        {stats_html}
    </div>

    <!-- BỘ ĐIỀU KHIỂN & LỌC CẢI TIẾN HOÀN TOÀN -->
    <div class="controls">
        <div class="control-group">
            <span class="control-label">Nhãn:</span>
            <select id="labelFilter" class="filter-select" onchange="filterTable()">
                <option value="all">Tất cả nhãn</option>
                <option value="hoi_dap">🟠 Hỏi đáp</option>
                <option value="trung_tinh">🔵 Trung tính</option>
                <option value="khong_lien_quan">⚪ Không liên quan</option>
                <option value="tich_cuc">🟢 Tích cực</option>
                <option value="tieu_cuc">🔴 Tiêu cực</option>
            </select>
        </div>

        <div class="control-group">
            <span class="control-label">Loại:</span>
            <select id="typeFilter" class="filter-select" onchange="filterTable()">
                <option value="all">Tất cả (Bài & Cmt)</option>
                <option value="post">📘 Chỉ Bài Gốc</option>
                <option value="comment">💬 Chỉ Bình Luận</option>
            </select>
        </div>

        <div class="control-group">
            <span class="control-label">Khía cạnh:</span>
            <select id="aspectFilter" class="filter-select" onchange="filterTable()">
                <option value="all">Tất cả khía cạnh</option>
                <option value="giang_vien">Giảng viên</option>
                <option value="chuong_trinh">Chương trình / Môn học</option>
                <option value="thi_cu">Thi cử / Điểm số</option>
                <option value="hoc_phi">Học phí / Học bổng</option>
                <option value="co_so_vat_chat">Cơ sở vật chất</option>
                <option value="hanh_chinh">Hành chính / Đào tạo</option>
                <option value="doan_hoi">Đoàn hội / CLB</option>
            </select>
        </div>

        <div class="control-group">
            <input type="text" id="search" placeholder="🔍 Tìm nội dung, ID..." oninput="filterTable()">
        </div>

        <button class="btn-reset" onclick="resetFilters()">↺ Đặt lại bộ lọc</button>
        
        <div id="count-display">Đang hiển thị: {len(records)}/{len(records)}</div>
    </div>

    <div class="table-wrapper">
        <table id="dataTable">
            <thead>
                <tr>
                    <th style="width: 35px;">#</th>
                    <th style="width: 105px;">Loại</th>
                    <th style="width: 155px;">Unit ID</th>
                    <th style="width: 140px;">Nhãn Cảm Xúc</th>
                    <th style="width: 160px;">Khía Cạnh (Aspects)</th>
                    <th>Nội Dung Văn Bản</th>
                    <th style="width: 220px;">Lý Do / Ghi Chú</th>
                    <th style="width: 110px;">Facebook</th>
                </tr>
            </thead>
            <tbody>
                {"".join(html_rows)}
            </tbody>
        </table>
    </div>
</div>

<div id="toast" class="status-toast">
    <span id="toast-icon">✓</span>
    <span id="toast-msg">Đã cập nhật nhãn thành công!</span>
</div>

<script>
function setLabelFilter(lbl) {{
    document.getElementById('labelFilter').value = lbl;
    filterTable();
}}

function resetFilters() {{
    document.getElementById('labelFilter').value = 'all';
    document.getElementById('typeFilter').value = 'all';
    document.getElementById('aspectFilter').value = 'all';
    document.getElementById('search').value = '';
    filterTable();
}}

function filterTable() {{
    let targetLabel = document.getElementById('labelFilter').value;
    let targetType = document.getElementById('typeFilter').value;
    let targetAspect = document.getElementById('aspectFilter').value;
    let q = document.getElementById('search').value.trim().toLowerCase();
    
    let rows = document.querySelectorAll('#dataTable tbody tr');
    let visibleCount = 0;

    for (let i = 0; i < rows.length; i++) {{
        let r = rows[i];
        let rLabel = r.getAttribute('data-label');
        let rType = r.getAttribute('data-type');
        let rAspects = r.getAttribute('data-aspects') || '';

        // 1. Kiểm tra bộ lọc Nhãn
        let matchLabel = (targetLabel === 'all' || rLabel === targetLabel);
        
        // 2. Kiểm tra bộ lọc Loại (post vs comment)
        let matchType = (targetType === 'all' || rType === targetType);
        
        // 3. Kiểm tra bộ lọc Khía cạnh
        let matchAspect = (targetAspect === 'all' || rAspects.includes(targetAspect));

        // 4. Kiểm tra tìm kiếm từ khóa CHỈ TRÊN nội dung văn bản và UID (KHÔNG quét options của select)
        let matchSearch = true;
        if (q.length > 0) {{
            let textCol = r.querySelector('.text-col');
            let noteCol = r.querySelector('.note-col');
            let uid = r.getAttribute('data-uid') || '';
            let searchable = (textCol ? textCol.textContent : '') + ' ' + (noteCol ? noteCol.textContent : '') + ' ' + uid;
            matchSearch = searchable.toLowerCase().includes(q);
        }}

        if (matchLabel && matchType && matchAspect && matchSearch) {{
            r.style.display = '';
            visibleCount++;
        }} else {{
            r.style.display = 'none';
        }}
    }}

    document.getElementById('count-display').innerText = `Đang hiển thị: ${{visibleCount}}/${{rows.length}}`;
}}

function showToast(msg, isError = false) {{
    let toast = document.getElementById('toast');
    let toastMsg = document.getElementById('toast-msg');
    let toastIcon = document.getElementById('toast-icon');
    toastMsg.innerText = msg;
    toastIcon.innerText = isError ? '⚠' : '✓';
    toast.style.background = isError ? '#dc2626' : '#0f172a';
    toast.classList.remove('show');
    void toast.offsetWidth;
    toast.classList.add('show');
}}

function updateLabel(unitId, newLabel, selectEl) {{
    selectEl.className = 'label-select ' + newLabel;
    let tr = selectEl.closest('tr');
    tr.setAttribute('data-label', newLabel);

    fetch('/api/update_label', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ unit_id: unitId, label: newLabel }})
    }})
    .then(res => res.json())
    .then(data => {{
        if (data.status === 'success') {{
            showToast(`Đã lưu: ${{unitId}} ➔ ${{newLabel}}`);
        }} else {{
            showToast(`Lỗi: ${{data.error || 'Không thể lưu'}}`, true);
        }}
    }})
    .catch(err => {{
        showToast('Lỗi kết nối máy chủ!', true);
    }});
}}
</script>
</body>
</html>
"""

with open("data/labeled/review_viewer.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n[✓] ĐÃ CẬP NHẬT HOÀN TẤT data/labeled/review_viewer.html VỚI BỘ LỌC CẢI TIẾN VÀ BỎ QUA QUẢNG CÁO TIẾNG ANH!")
