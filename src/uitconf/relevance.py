"""Tầng 1: lọc 'liên quan UIT' bằng từ khóa (phần 1, Quyết định 3) + gán aspect sơ bộ."""
import re

def _compile(words):
    return re.compile("|".join(r"(?<!\w)" + re.escape(w) + r"(?!\w)" for w in words), re.I)

class RuleTagger:
    def __init__(self, aspects_cfg):
        self.rel = _compile(aspects_cfg["relevance_keywords"])
        self.asp = {k: _compile(v) for k, v in aspects_cfg["aspects"].items()}

    def is_relevant(self, text):
        return bool(self.rel.search(text or ""))

    def aspects(self, text):
        return [k for k, p in self.asp.items() if p.search(text or "")]
