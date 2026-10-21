"""Tiền xử lý tiếng Việt mạng xã hội (phần 6)."""
import csv
import re
import unicodedata
from pathlib import Path

ELONG = re.compile(r"(.)\1{2,}", re.U)
TAG = re.compile(r"\[(URL|EMAIL|SDT|MSSV|MXH|GV|TEN)\]")

def load_teencode(path="data/teencode.csv"):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, encoding="utf-8") as f:
        return {r["teen"].strip().lower(): r["chuan"].strip() for r in csv.DictReader(f)}

def normalize(text, teen=None, keep_emoji=True):
    t = unicodedata.normalize("NFC", text or "")
    t = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", t)
    flag = ""
    if ELONG.search(t):                          # "quááá" -> "quá" + cờ nhấn mạnh
        t = ELONG.sub(r"\1", t)
        flag = " <nhan_manh>"
    try:
        import emoji
        if keep_emoji:
            t = emoji.demojize(t, delimiters=(" <emo_", "> "), language="alias")
        else:
            t = emoji.replace_emoji(t, "")
    except ImportError:
        pass
    t = t.lower()
    if teen:
        t = " ".join(teen.get(w, w) for w in re.findall(r"\S+", t))
    t = re.sub(r"\s+", " ", t).strip()
    return t + flag

def segment(text):
    """Tách từ cho PhoBERT (tùy mô hình)."""
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text")
    except Exception:
        return text

def is_valid(text, min_words=3):
    stripped = TAG.sub("", text or "").strip()
    return len(stripped.split()) >= min_words
