import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def clean_display_text(text, author=""):
    if not text:
        return ""
    # 1. Bỏ boilerplate các nút bấm ở đuôi
    text = re.sub(r'[\s\xa0]*(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    # 2. Bỏ phần đầu bị dính 'Tác giả · Thời gian'
    text = re.sub(r'^.*?[·•]\s*\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y|gi)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    if author and author != 'Ẩn danh' and text.startswith(author):
        text = text[len(author):].strip()
        text = re.sub(r'^[·•\s\xa0]+', '', text)
        text = re.sub(r'^\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    # 3. Tách từ dính liền sau dấu câu: 'chữ.Chữ' -> 'chữ. Chữ'
    text = re.sub(r'([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF90-9])([\.?!,:;])([A-ZÀ-Ỹ\"“a-zà-ỹ])', r'\1\2 \3', text)
    # Tách dấu ngoặc kép dính liền chữ: '""Trời' -> '"" Trời'
    text = re.sub(r'([”"])([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9\u00C0-\u024F\u1EA0-\u1EF9])([“"])', r'\1 \2', text)
    # Tách dấu ngoặc đơn: '(6H30-14H)LƯU Ý' -> '(6H30-14H) LƯU Ý'
    text = re.sub(r'(\))([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([A-ZÀ-Ỹa-zà-ỹ0-9])(\()', r'\1 \2', text)
    # Tách dấu chấm dính với ngoặc kép: 'not."Our' -> 'not. "Our'
    text = re.sub(r'([\.?!,:;])([“"])', r'\1 \2', text)
    text = re.sub(r'([”"])([\.?!,:;])', r'\1\2', text)
    # Tách hai dấu ngoặc kép liền nhau: 'another.""Trời' -> 'another." "Trời'
    text = re.sub(r'([”"])([“"])', r'\1 \2', text)
    # 4. Tách các nút bấm còn sót lại ở đuôi lần 2
    text = re.sub(r'[\s\xa0]*(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    # 5. Chuẩn hóa khoảng trắng thừa
    text = re.sub(r'[ \t\xa0]+', ' ', text).strip()
    return text

s1 = 'exception.What you are going through has a name: Duck Syndrome... You are not."Our advisors all have 4.0 GPAs... family issues.Clubs are not that important... time anyway.As Fukuzawa Yukichi wrote: "Heaven does not create one person above or below another.""Trời không tạo ra người đứng trên người, cũng không tạo ra người đứng dưới người." nhéThíchTrả lờiXem bản dịchChia sẻ'
s2 = 'XÔI XÉO, XÔI TRẮNG TẬN TOÀ KTX B, CÁC TRƯỜNG ĐẠI HỌC SÁNG T5 (6H30-14H)LƯU Ý: QUÁN CHỈ NHẬN TIỀN MẶT HOẶC CK TRỰC TIẾP CHO SHIPPER, KHÔNG NHẬN CK QUA ZÉP LÀO(ZL) Ạ- Xôi đùi gà #25k'

print('S1 Cleaned:\n', clean_display_text(s1))
print('\nS2 Cleaned:\n', clean_display_text(s2))

