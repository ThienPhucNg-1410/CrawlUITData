"""Ẩn danh hóa hai lớp (phần 2): regex + (tùy chọn) NER, rồi người kiểm mẫu ngẫu nhiên."""
import re

CAP = r"[A-ZÀ-ỸĐ][a-zà-ỹđ]*"
PATTERNS = [
    ("URL",   re.compile(r"(https?://\S+|www\.\S+|\b\S+\.(com|vn|me|net|edu|org|io|ly|gle)/\S*)", re.I)),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("SDT",   re.compile(r"(?<!\d)(\+?84|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}(?!\d)")),
    ("MSSV",  re.compile(r"(?<!\d)\d{8}(?!\d)")),
    ("MXH",   re.compile(r"@\w{3,}")),
]
# Chức danh không phân biệt hoa thường + tên viết hoa: chỉ thay phần tên, giữ chức danh
GV_KEEP = re.compile(rf"(?i:\b(thầy|cô|gv|giảng viên|ts|ths|pgs|gs|tc|th\.?s)\.?\s+)({CAP}(\s+{CAP}){{0,3}})")

def regex_layer(text):
    t = text
    t = GV_KEEP.sub(lambda m: f"{m.group(1)} [GV]", t)
    for tag, pat in PATTERNS:
        if tag == "GV":
            continue
        t = pat.sub(f"[{tag}]", t)
    return t

_ner = None
def ner_layer(text):
    """Tùy chọn: underthesea NER thay thực thể người (PER). Bỏ qua nếu chưa cài."""
    global _ner
    try:
        if _ner is None:
            from underthesea import ner
            _ner = ner
        out, cur = [], []
        for tok, _pos, _chunk, tag in _ner(text):
            if tag.endswith("PER"):
                if not cur:
                    out.append("[TEN]")
                cur.append(tok)
            else:
                cur = []
                out.append(tok)
        return " ".join(out)
    except Exception:
        return text

def anonymize(text, use_ner=False):
    t = regex_layer(text or "")
    return ner_layer(t) if use_ner else t
