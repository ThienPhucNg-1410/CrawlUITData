"""Hàm thuần (không cần trình duyệt) để test được: id bài, thời gian, hash vòng."""
import hashlib
import re
from datetime import datetime

PFBID = re.compile(r"(pfbid[0-9A-Za-z]+)")
NUMERIC = re.compile(r"/posts/(\d+)")

def post_id_from_href(href):
    if not href:
        return None
    m = PFBID.search(href) or NUMERIC.search(href)
    return m.group(1) if m else None

def bucket_of(post_id):
    return int(hashlib.sha1(post_id.encode()).hexdigest(), 16) % 100

def round_of(bucket, rounds_cfg):
    for r, (lo, hi) in rounds_cfg.items():
        if lo <= bucket < hi:
            return int(r)
    return max(int(r) for r in rounds_cfg)

def comment_id(post_id, parent_id, text, idx):
    h = hashlib.sha1(f"{post_id}|{parent_id}|{idx}|{text[:200]}".encode()).hexdigest()[:16]
    return f"c_{h}"

def parse_time(raw):
    """Best-effort; luôn lưu time_raw để kiểm tra lại. Trả ISO hoặc None."""
    if not raw:
        return None
    r = raw.strip().lower()
    if r in ("vừa xong", "just now", "vừa mới đăng"):
        return datetime.now().isoformat()
    try:
        import dateparser
        d = dateparser.parse(raw, languages=["vi", "en"],
                             settings={"PREFER_DATES_FROM": "past", "RELATIVE_BASE": datetime.now()})
        return d.isoformat() if d else None
    except Exception:
        return None

def parse_count(s):
    """'1,2K' / '3 N' / '1.234' -> int"""
    if not s:
        return 0
    s = s.strip().lower().replace(",", ".")
    m = re.match(r"([\d.]+)\s*(k|n|nghìn|tr|m)?", s)
    if not m:
        return 0
    try:
        num = float(m.group(1)) if m.group(1).count(".") <= 1 else float(m.group(1).replace(".", ""))
    except ValueError:
        return 0
    mult = {"k": 1e3, "n": 1e3, "nghìn": 1e3, "tr": 1e6, "m": 1e6}.get(m.group(2), 1)
    return int(num * mult)
