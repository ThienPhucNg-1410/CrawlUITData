import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd

# Đọc toàn bộ 29 đơn vị dữ liệu
df = pd.read_csv("data/clean/units.csv")

labels_dict = {
    # 1. Post: Trai tmđt sao lại gốt mình
    "1137454842150577": ("khong_lien_quan", 0, "", "Chuyện tình cảm riêng tư ngoài lề"),
    
    # 2. Post: First date dẫn đi ăn cơm tấm :))) ôi trai uit ơi
    "1137454488817279": ("khong_lien_quan", 0, "", "Bài viết vui/tình cảm cá nhân, không liên quan đến học tập hay đánh giá trường"),
    
    # 3. Post: Profile ntn phải cỡ nào mới đc vào clb AI v ạ
    "1137241605505234": ("hoi_dap", 0, "doan_hoi", "Hỏi điều kiện tham gia câu lạc bộ AI"),
    
    # 4. Post: Điểm QT mình đc làm tròn tới đâu v ạ
    "1137227098840018": ("hoi_dap", 0, "thi_cu", "Hỏi quy chế làm tròn điểm quá trình"),
    
    # 5. Post: Có ai nhặc được củ sạc này hong ạ
    "1137218335507561": ("khong_lien_quan", 0, "", "Tìm đồ thất lạc cá nhân"),
    
    # 6. Post: Dạ cho em hỏi anh chị hay in tài liệu ở đâu giá rẻ ạ...
    "1137208718841856": ("hoi_dap", 0, "ky_tuc_xa", "Hỏi địa điểm in ấn tài liệu học tập gần KTX"),
    
    # 7. Post: sau 1 tháng học... giảng viên môn này ko có tâm lắm (thầy vô trễ + ngủ nữa)...
    "1137195462176515": ("tieu_cuc", 0, "giang_vien|chuong_trinh", "Phàn nàn bức xúc về tác phong và chất lượng dạy của giảng viên"),
    
    # 8. Post: để quên chuột logitech ở phòng thực hành B2.16
    "1137180092178052": ("khong_lien_quan", 0, "", "Tìm đồ thất lạc cá nhân"),
    
    # 9. Post: g muốn lụm một anh uit lowkey cún con thì nên đi đâu để hốt v mn
    "1137147762181285": ("khong_lien_quan", 0, "", "Tâm sự tìm người yêu cá nhân"),
    
    # 10. Post: Tôi sau 2 tháng học UIT...
    "1137147162181345": ("khong_lien_quan", 0, "", "Bài viết vui/meme giải trí, không thể hiện quan điểm đánh giá trường"),
    
    # 11. Post: nữ trường khác xin tips cua nam uit ạ
    "1137146758848052": ("khong_lien_quan", 0, "", "Hỏi mẹo tán tỉnh sinh viên trường"),
    
    # 12. Post: Môn Nhập môn Thị giác Máy tính do thầy [GV] dạy có bạn nào chưa có nhóm...
    "1137168422179219": ("hoi_dap", 0, "giang_vien|chuong_trinh", "Tìm bạn cùng nhóm môn học"),
    
    # 13. Post: Mn có ai bt làm s xem các đề giữa/cuối kì của các năm trc ko?
    "1137142618848466": ("hoi_dap", 0, "thi_cu", "Hỏi cách tìm đề thi cũ để ôn tập"),
    
    # 14. Post: của bạn nào quên này Bạn nhặt đc ở phòng nào v ạ
    "1137097455519649": ("khong_lien_quan", 0, "", "Nhặt đồ rơi trả lại"),
    
    # 15. Post: Anh chị ơi, Cái này trên portal là xin loại giấy nào v
    "1137084418854286": ("hoi_dap", 0, "hanh_chinh", "Hỏi thủ tục xin giấy tờ trên portal trường"),
    
    # 16. Post: Mn ai học lớp It007.R17 của thầy [GV] cho mình hỏi cách viết báo cáo Lab...
    "1137057862190275": ("hoi_dap", 0, "giang_vien|chuong_trinh", "Hỏi hướng dẫn làm bài tập Lab môn học"),
    
    # 17. Post: Môn Nhập môn Thị giác Máy tính lớp CS231.R12 thầy [GV] có bạn nào chưa có nhóm...
    "1137069478855780": ("hoi_dap", 0, "giang_vien|chuong_trinh", "Tìm nhóm môn học"),
    
    # 18. Post: 5 LÝ DO BẠN NÊN CHỌN HỌC TẠI TOEIC BUDDIES...
    "1137098075519587": ("khong_lien_quan", 0, "", "Quảng cáo trung tâm tiếng Anh ngoài"),
    
    # 19. Post: Bạn nào quên chìa khoá trên ghế đá tui gửi bảo vệ giữ xe nha
    "1137034905525904": ("khong_lien_quan", 0, "", "Tìm đồ thất lạc cá nhân"),
    
    # 20. Post: Lớp ss004.r11 bạn nào chưa có nhóm hoặc nhóm thiếu slot cho mình join với.
    "1137939768868751": ("hoi_dap", 0, "chuong_trinh", "Tìm nhóm môn học kỹ năng mềm"),
    "1136939768868751": ("hoi_dap", 0, "chuong_trinh", "Tìm nhóm môn học"),
    
    # 21. Post: Sự kiện Healthinfo có được record và đăng công khai không v mọi người?
    "1136920468870681": ("hoi_dap", 0, "doan_hoi", "Hỏi tài liệu ghi hình sự kiện của trường"),
    
    # 22. Post: Hôm qua em để quên đồ ở phòng E34 thì đồ nó sẽ nằm ở đó hay...
    "1136885368874191": ("khong_lien_quan", 0, "", "Hỏi thủ tục tìm đồ rơi ở phòng học"),
    
    # 23. Post: Dạ anh chị ngành ATTT cho e hỏi là học trên trường hoặc sau này đi làm thì mình cài linux gì ạ...
    "1136653162230745": ("hoi_dap", 0, "chuong_trinh", "Hỏi kinh nghiệm học ngành An toàn thông tin"),
    
    # 24. Post: cho e hỏi đóng form wecode những bài tập cũ rồi nhưng em muốn sau luyện lại thì có thể mở thêm phần practice...
    "1136598038902924": ("hoi_dap", 0, "chuong_trinh|giang_vien", "Thắc mắc hệ thống chấm bài nộp wecode của trường"),
    
    # 25. Post: Ae cho tui hỏi nếu một bạn nữ chủ động ngồi cạnh mình...
    "1136609785568416": ("khong_lien_quan", 0, "", "Tâm sự chuyện tình cảm cá nhân"),
    
    # 26. Post: Vấn đề điểm cộng tuyển sinh IELTS 6.5, Nhì HSG tỉnh...
    "1136523312243730": ("hoi_dap", 0, "hanh_chinh", "Thắc mắc quy chế điểm cộng tuyển sinh vào trường"),
    
    # 27. Post: anh chị cho em hỏi anh chị sống sót qua môn nhập môn lập trình kiểu gì...
    "1136490378913690": ("hoi_dap", 0, "chuong_trinh", "Hỏi kinh nghiệm học và tài liệu môn Nhập môn lập trình"),
    
    # 28. Post: ôi đại học ơi... mới học 4 buổi đã thi giữa kì...
    "1136419612254100": ("khong_lien_quan", 0, "", "Bài viết giật tít than thở vui/troll, thông tin thi cử không đúng"),
    
    # 29. Post: Trong một đám sinh viên uit, ai ko mặc áo trường lanyard...
    "1136417842254277": ("khong_lien_quan", 0, "", "Bài vui vẻ về dấu hiệu nhận biết sinh viên năm cuối"),
    
    # 30. Post: chắc chbi sắm cano đi học =))) tôi iu Thủ Đức, iu sv làng DH
    "1136417635587631": ("khong_lien_quan", 0, "", "Đùa vui về tình trạng ngập nước làng đại học mùa mưa"),
    
    # 31. Post: Mấy các minigame thường đc cộng bao nhiu đrl v ạ
    "1136397425589652": ("hoi_dap", 0, "doan_hoi", "Hỏi quy chế cộng Điểm Rèn Luyện (ĐRL) hoạt động phong trào"),
    
    # 32. Post: Mn ơi cho em hỏi xét hb kkht như này đk ạ . e đg 9. mà không hiến máu...
    "1136388395590555": ("hoi_dap", 0, "hoc_phi", "Hỏi điều kiện xét Học bổng khuyến khích học tập"),
    
    # 33. Post: Cho em hỏi thư viện mình mở cửa đến mấy giờ v ạ?
    "1136385735590821": ("hoi_dap", 0, "co_so_vat_chat", "Hỏi giờ giấc hoạt động thư viện trường"),
    
    # 34. Post: cho em xin review ngành KTMT trường mình với ạ. Với lại a/c có tips gì...
    "1136382848924443": ("hoi_dap", 0, "chuong_trinh", "Xin review ngành học và phương pháp học tập"),
    
    # 35. Post: Em có làm rơi bóp tiền như hình (đã hơi cũ) ạ...
    "1136380032258058": ("khong_lien_quan", 0, "", "Tìm đồ thất lạc cá nhân"),
    
    # 36. Post: Sáng mình vừa gặp 1 bạn nữ trông cứ như em bé ấy... xin in4
    "1136360355593359": ("khong_lien_quan", 0, "", "Tâm sự tình cảm cá nhân ngoài lề"),
    
    # 37. Post: Chào mn, mình muốn xin in4 bạn nữ mặc áo đoàn sáng hôm nay...
    "1136354185593976": ("khong_lien_quan", 0, "", "Xin thông tin liên hệ bạn nữ ngoài lề"),
    
    # 38. Post: Dạ cho e hỏi khu giải trí khu A ngoài bàn bida vs bàn bóng đá, thì còn gì ko ạ
    "1136398585589536": ("khong_lien_quan", 0, "", "Hỏi về tiện ích giải trí/chơi bời ngoài lề, không thuộc học tập/tài liệu"),
    
    # 39. Post: FULL GIÁP TOEIC 4 KỸ NĂNG...
    "1138359618726766": ("khong_lien_quan", 0, "", "Quảng cáo trung tâm tiếng Anh bên ngoài"),
    
    # 40. Post: Môn Kỹ thuật phân tích yêu cầu lớp SE357.R11 còn thiếu nhóm...
    "1138191295410265": ("hoi_dap", 0, "chuong_trinh", "Tìm nhóm làm bài tập môn học"),
    
    # 41. Post: e làm chậm mấy bài quá trình 2 lần có bị s k ạ...
    "1138056582090403": ("hoi_dap", 0, "thi_cu", "Hỏi ảnh hưởng điểm số khi trễ bài quá trình"),
    
    # 42. Post: Tha thiết tìm 1 anh uit đi chơi noel vs em...
    "1137512378811490": ("khong_lien_quan", 0, "", "Tìm bạn đi chơi noel cá nhân"),
    
    # 43. Post: Có cách nào làm quen được với mấy chị khoá trên không ạ...
    "1138219352074126": ("khong_lien_quan", 0, "", "Hỏi cách làm quen khóa trên cá nhân"),
    
    # 44. Post: làm các bài template trên wecode ạ...
    "1137989542097107": ("hoi_dap", 0, "chuong_trinh", "Thắc mắc kỹ thuật nộp bài trên wecode của trường"),
    
    # 45. Post: Trg mình có nhóm discord gl hc hỏi chia sẻ tl k ạ...
    "1137872795442115": ("hoi_dap", 0, "chuong_trinh", "Hỏi nhóm học tập, chia sẻ tài liệu trường"),
    
    # 46. Post: Các bạn nào cùng trường dư thanh 8G PC DDR4 pass không...
    "1137794445449950": ("khong_lien_quan", 0, "", "Hỏi mua bán/pass linh kiện RAM cá nhân"),
    
    # 47. Post: Nếu em ko học av 1, 2, 3 mà nộp vstep b1...
    "1137457198817008": ("hoi_dap", 0, "hanh_chinh|thi_cu", "Hỏi quy chế miễn học phần tiếng Anh và chuẩn đầu ra"),
    "1137456215483773": ("hoi_dap", 0, "hanh_chinh|thi_cu", "Hỏi quy chế miễn học phần tiếng Anh và chuẩn đầu ra"),
    
    # 48. Post: Sinh viên ngành TKVM và chương trình tài năng có được học bổng STEM...
    "1137996192096442": ("hoi_dap", 0, "hoc_phi|chuong_trinh", "Hỏi chính sách học bổng STEM của ngành Thiết kế vi mạch"),
    
    # 49. Post: Helo Nguyễn Nhân người mà mình biết tên chứ không biết học ngành nào...
    "1137254688837259": ("khong_lien_quan", 0, "", "Nhắn nhủ tình cảm cá nhân"),
    
    # 50. Post: Mọi người ơi, tiêu chí quan trọng nhất để chọn 1 CLB năm nhất...
    "1138211705408224": ("hoi_dap", 0, "doan_hoi", "Hỏi kinh nghiệm chọn câu lạc bộ sinh viên"),
    
    # 51. Post: Dạ em là sinh viên năm nhất cho em hỏi vào thư viện trung tâm quy trình...
    "1137564162139645": ("hoi_dap", 0, "co_so_vat_chat", "Hỏi quy trình vào thư viện trung tâm ĐHQG"),
    
    # 52. Post: Mn ơi sáng nay e quên mang tiền lẻ để gửi xe...
    "1137358822160179": ("khong_lien_quan", 0, "", "Thắc mắc tiền gửi xe cá nhân"),
    
    # 53. Post: Đăng nhập vào thư viên trung tâm đhqg như thế nào vậy ạ...
    "1137271998835528": ("hoi_dap", 0, "co_so_vat_chat", "Hỏi cách đăng nhập tài khoản thư viện trung tâm"),
    
    # 54. Post: Mình xin 300 bài viết thiếu nhi của trường với ạ...
    "1137266518836076": ("hoi_dap", 0, "chuong_trinh", "Xin bộ tài liệu bài tập code thiếu nhi của trường"),
    
    # Comments
    # Comment: Ngồi kế auto đổ (thấy combo thở gấp...)
    "c_c05d32e9296cc536": ("khong_lien_quan", 0, "", "Bình luận vui đùa, không liên quan học tập hay trường"),
    
    # Comment: Đọc -> hiểu -> làm -> sai -> sửa -> hiểu sâu
    "c_254e42dce6900f1c": ("hoi_dap", 0, "chuong_trinh", "Giải đáp hướng dẫn thắc mắc học tập bài gốc"),
    
    # Comment: Em có thể tận dụng Gemini Plus từ tài khoản email trường nè...
    "c_a58cdc18c2e3db84": ("hoi_dap", 0, "chuong_trinh", "Giải đáp hướng dẫn thắc mắc học tập bài gốc"),
    
    # Comment: Tui không phải anh chị nhưng mà cũng có tí kinh nghiệm chia sẻ là: Về website tui thấy có GeeksforGeeks...
    "c_08828a1b8da4f449": ("hoi_dap", 0, "chuong_trinh", "Giải đáp hướng dẫn thắc mắc học tập bài gốc"),
}

import re

PASS_PATTERNS = re.compile(r"\b(pass|nhượng|thanh lý|mua bán|mua lại|bán lại|giá cả ib|giá ib|inbox giá|pass lại|cho thuê|tìm trọ|ở ghép|pass đồ|pass balo|cần pass|pass chuột|pass áo|pass sách|pass vé|mua sách|tìm bạn cùng phòng|tìm bạn ở ghép)\b", re.I)
LOST_PATTERNS = re.compile(r"(rơi|rớt|nhặt đ[uư][ợo]c|để quên|quên.*?ở phòng|thẻ sinh viên.*?quên|của ai quên|có ai nhặt|tìm đồ|thất lạc|củ sạc|chìa khóa|mất ví|rơi ví|rơi chìa|để quên chuột|rơi cccd|nhặt được căn cước|tìm chủ nhân|đánh rơi)", re.I)
ROMANCE_PATTERNS = re.compile(r"\b(crush|tỏ tình|người yêu|ny|nyc|tìm in4|xin in4|cún con|đẹp trai|xinh gái|gái xinh|tán trai|tán gái|first date|hẹn hò|thả thính|bạn nữ mặc|bạn nam mặc|tìm bạn gái|tìm bạn trai|thương thầm)\b", re.I)
FUN_PATTERNS = re.compile(r"\b(bida|billiards|blox fruit|blox kid|kèo bóng|bóng đá|băng đĩa|band nhạc|trái cây|bánh xèo|trà sữa|cơm tấm|chơi game|liên quân|đá pes|nhậu|ăn uống|quán ngon)\b", re.I)

NEGATIVE_PATTERNS = re.compile(r"(dạy chán|chán vl|tệ vl|thất vọng|bức xúc|khó chịu|chán nản|rớt môn|tạ môn|ngủ gật|vô trễ|đi trễ|không có tâm|ko có tâm|chấm gắt|chấm khó|chấm ảo|điểm thấp|hút máu|học phí chát|tăng học phí|học phí cao|đắt vl|mạng như rùa|wifi như|web sập|portal lỗi|thang máy hư|máy lạnh hư|nhà vệ sinh|chê|bực|hối hận|áp lực vl)", re.I)
POSITIVE_PATTERNS = re.compile(r"(10/10|dạy hay|thầy tận tâm|cô tận tâm|nhiệt tình|dễ thương|dễ tính|cho điểm cao|qua môn dễ|ưng ý|tuyệt vời|cảm ơn thầy|cảm ơn cô|yêu trường|tự hào uit|thầy tín 10|dạy đỉnh|thầy vui tính|cô nhiệt tình|điểm cao|hài lòng)", re.I)

QUESTION_PATTERNS = re.compile(r"(\?|cho em hỏi|cho mình hỏi|mọi người cho em hỏi|mn cho e hỏi|cho e hỏi|cho tui hỏi|có ai biết|có ai bt|xin review|xin tài liệu|xin đề|xin slide|xin slot|tìm nhóm|chưa có nhóm|thiếu slot|lập nhóm|rút môn|đăng ký môn|học phần|điểm quá trình|điểm qt|thi giữa kỳ|thi cuối kỳ|chuẩn đầu ra|toeic|ielts|wecode|viết báo cáo|portal|xin giấy|học bổng|lịch thi|môn học|giảng viên|thầy|cô|khoa|phòng đào tạo|pđt|ctsv|bảo lưu|chuyển ngành|chuyển lớp)", re.I)

ASP_GV = re.compile(r"(thầy|cô|giảng viên|gv|thầy tín|thầy tình|thầy nhựt|thầy huy|cô hằng|cô thi)", re.I)
ASP_CT = re.compile(r"(môn|chương trình|học phần|đồ án|lab|wecode|tiếng anh|av1|av2|av3|cntt|httt|ktmt|khmt|attt|mmt|giải tích|đại số|dstt|ctdl|oop|csdl|hdh|hđh)", re.I)
ASP_TC = re.compile(r"(thi|đề thi|giữa kỳ|cuối kỳ|điểm|gpa|phúc khảo|làm tròn|cột điểm)", re.I)
ASP_HP = re.compile(r"(học phí|tiền học|ngân hàng chính sách|miễn giảm|học bổng)", re.I)
ASP_CS = re.compile(r"(cơ sở vật chất|máy lạnh|thang máy|phòng học|wifi|thư viện|nhà vệ sinh|bàn ghế|ktx|nhà xe)", re.I)
ASP_DH = re.compile(r"(đoàn|hội|clb|câu lạc bộ|shcd|hiến máu|đrl|điểm rèn luyện)", re.I)

def classify_fallback(text):
    t = str(text or "")
    if PASS_PATTERNS.search(t):
        return "khong_lien_quan", "Rao vặt, pass đồ, mua bán"
    if LOST_PATTERNS.search(t):
        return "khong_lien_quan", "Tìm đồ rơi, nhặt được đồ thất lạc"
    if ROMANCE_PATTERNS.search(t):
        return "khong_lien_quan", "Chuyện tình cảm, tìm in4, thả thính ngoài lề"
    if FUN_PATTERNS.search(t):
        return "khong_lien_quan", "Hoạt động ăn uống, giải trí ngoài lề"
    if NEGATIVE_PATTERNS.search(t):
        return "tieu_cuc", "Bày tỏ không hài lòng, phàn nàn về trường/thầy cô/học phí/quy chế"
    if POSITIVE_PATTERNS.search(t):
        return "tich_cuc", "Khen ngợi, đánh giá tốt về thầy cô/môn học/trường"
    if QUESTION_PATTERNS.search(t):
        return "hoi_dap", "Hỏi đáp thắc mắc về môn học, thi cử, quy chế đào tạo"
    return "trung_tinh", "Chia sẻ thông tin học tập khách quan"

def extract_aspects_fallback(text):
    t = str(text or "")
    asps = []
    if ASP_GV.search(t): asps.append("giang_vien")
    if ASP_CT.search(t): asps.append("chuong_trinh")
    if ASP_TC.search(t): asps.append("thi_cu")
    if ASP_HP.search(t): asps.append("hoc_phi")
    if ASP_CS.search(t): asps.append("co_so_vat_chat")
    if ASP_DH.search(t): asps.append("doan_hoi")
    return "|".join(asps)

records = []
for r in df.itertuples():
    uid = str(r.unit_id)
    txt_clean = " ".join(str(r.text_clean).split())
    ctx_clean = " ".join(str(r.context).split()) if pd.notna(r.context) else ""
    plink = str(r.permalink) if pd.notna(r.permalink) else ""

    if uid in labels_dict:
        lab, sarc, asp, note = labels_dict[uid]
    else:
        lab, note = classify_fallback(txt_clean)
        asp = extract_aspects_fallback(txt_clean)
        sarc = 0

    records.append({
        "unit_id": uid,
        "unit_type": r.unit_type,
        "month": r.month,
        "permalink": plink,
        "context": ctx_clean,
        "text": txt_clean,
        "label": lab,
        "sarcasm": sarc,
        "aspects": asp,
        "note": note
    })

labeled_df = pd.DataFrame(records)

# Lưu cả vào annotator_A.csv và gold.csv
labeled_df.to_csv("data/labeled/annotator_A.csv", index=False, encoding="utf-8-sig")

gold_df = labeled_df.copy()
gold_df = gold_df.merge(df[["unit_id", "post_id", "created_at", "text_norm", "aspects_rule"]], on="unit_id")
gold_df.to_csv("data/labeled/gold.csv", index=False, encoding="utf-8-sig")

# File review trực quan CSV kèm link bài viết
readable_review = labeled_df[["unit_id", "unit_type", "label", "aspects", "sarcasm", "permalink", "text", "note"]]
readable_review.to_csv("data/labeled/review_labeled.csv", index=False, encoding="utf-8-sig")

print("Đã cập nhật gán nhãn tự động cho tất cả các bài viết.")
print(labeled_df["label"].value_counts())

# Xuất giao diện HTML trực quan tiện xem và kiểm tra
html_rows = []
badge_colors = {
    "hoi_dap": "#e67e22",
    "khong_lien_quan": "#7f8c8d",
    "tieu_cuc": "#e74c3c",
    "tich_cuc": "#27ae60",
    "trung_tinh": "#2980b9"
}

for idx, row in enumerate(records, start=1):
    c = badge_colors.get(row['label'], '#333')
    link_html = f'<a href="{row["permalink"]}" target="_blank" class="fblink">Xem bài FB ↗</a>' if row["permalink"] else '-'
    html_rows.append(f"""
    <tr data-label="{row['label']}">
        <td>{idx}</td>
        <td><code>{row['unit_id']}</code></td>
        <td><span class="badge" style="background:{c};">{row['label']}</span></td>
        <td><span class="asp">{row['aspects'] or '-'}</span></td>
        <td class="text-col">{row['text']}</td>
        <td class="note-col">{row['note']}</td>
        <td>{link_html}</td>
    </tr>
    """)

stats_html = "".join(f'<div class="stat-box" style="border-left: 4px solid {badge_colors.get(k, "#333")}"><div class="stat-num">{v}</div><div class="stat-lbl">{k}</div></div>' for k, v in labeled_df["label"].value_counts().items())

html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<title>Kiểm tra Gán nhãn Confession UIT ({len(records)} bài)</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
    .container {{ max-width: 1400px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
    h1 {{ margin-top: 0; font-size: 24px; color: #1a365d; }}
    .stats-bar {{ display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }}
    .stat-box {{ background: #f8fafc; padding: 12px 18px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-width: 120px; }}
    .stat-num {{ font-size: 20px; font-weight: bold; color: #1e293b; }}
    .stat-lbl {{ font-size: 13px; color: #64748b; margin-top: 2px; }}
    .controls {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }}
    input#search {{ padding: 10px 14px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 6px; width: 350px; outline: none; }}
    .filter-btn {{ padding: 8px 14px; border: 1px solid #cbd5e1; background: #fff; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }}
    .filter-btn.active {{ background: #1a365d; color: #fff; border-color: #1a365d; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }}
    th, td {{ padding: 12px 10px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; font-weight: 600; color: #475569; position: sticky; top: 0; }}
    tr:hover {{ background: #f8fafc; }}
    .badge {{ color: #fff; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase; white-space: nowrap; }}
    .asp {{ color: #475569; font-size: 11px; background: #edf2f7; padding: 2px 6px; border-radius: 3px; display: inline-block; }}
    .text-col {{ max-width: 550px; line-height: 1.5; word-wrap: break-word; }}
    .note-col {{ max-width: 220px; font-size: 12px; color: #64748b; font-style: italic; }}
    .fblink {{ color: #2563eb; text-decoration: none; font-weight: 500; white-space: nowrap; }}
    .fblink:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="container">
    <h1>📋 Bảng Kiểm Tra & Đánh Giá Nhãn Confession UIT</h1>
    <p>Tổng số: <strong>{len(records)} bài viết</strong> đã được làm sạch, trích xuất và gán nhãn sơ bộ.</p>
    
    <div class="stats-bar">
        {stats_html}
    </div>

    <div class="controls">
        <input type="text" id="search" placeholder="🔍 Tìm kiếm nội dung bài viết, ID, từ khóa..." onkeyup="filterTable()">
        <button class="filter-btn active" onclick="setFilter('all', this)">Tất cả</button>
        <button class="filter-btn" onclick="setFilter('hoi_dap', this)">Hỏi đáp</button>
        <button class="filter-btn" onclick="setFilter('khong_lien_quan', this)">Không liên quan</button>
        <button class="filter-btn" onclick="setFilter('tieu_cuc', this)">Tiêu cực</button>
        <button class="filter-btn" onclick="setFilter('tich_cuc', this)">Tích cực</button>
        <button class="filter-btn" onclick="setFilter('trung_tinh', this)">Trung tính</button>
    </div>

    <table id="dataTable">
        <thead>
            <tr>
                <th style="width: 40px;">#</th>
                <th style="width: 130px;">Unit ID</th>
                <th style="width: 120px;">Nhãn</th>
                <th style="width: 130px;">Khía cạnh</th>
                <th>Nội dung confession</th>
                <th>Lý do / Ghi chú</th>
                <th style="width: 90px;">Link gốc</th>
            </tr>
        </thead>
        <tbody>
            {"".join(html_rows)}
        </tbody>
    </table>
</div>

<script>
let currentFilter = 'all';

function setFilter(lbl, btn) {{
    currentFilter = lbl;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filterTable();
}}

function filterTable() {{
    let q = document.getElementById('search').value.toLowerCase();
    let rows = document.querySelectorAll('#dataTable tbody tr');
    rows.forEach(r => {{
        let lab = r.getAttribute('data-label');
        let text = r.innerText.toLowerCase();
        let matchFilter = (currentFilter === 'all' || lab === currentFilter);
        let matchSearch = text.includes(q);
        r.style.display = (matchFilter && matchSearch) ? '' : 'none';
    }});
}}
</script>
</body>
</html>
"""

with open("data/labeled/review_viewer.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Đã tạo file giao diện trực quan: data/labeled/review_viewer.html")


