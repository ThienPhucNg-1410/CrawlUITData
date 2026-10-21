"""Quy tắc dừng cứng (3.8) + khóa nghỉ giữa các phiên. KHÔNG có logic né/giải captcha."""
from datetime import datetime, timedelta
from pathlib import Path

class HardStop(Exception):
    pass

URL_MARKERS = ("checkpoint", "/login", "captcha", "two_step_verification")
TEXT_MARKERS = (
    "xác nhận danh tính", "confirm your identity", "tạm thời bị chặn", "temporarily blocked",
    "bạn tạm thời không thể", "hoạt động bất thường", "unusual activity",
    "tài khoản của bạn đã bị hạn chế", "your account has been restricted",
    "security check", "kiểm tra bảo mật",
)

from selenium.webdriver.common.by import By

def check_blocked(driver):
    try:
        url = getattr(driver, "current_url", "").lower()
        for m in URL_MARKERS:
            if m in url:
                raise HardStop(f"url marker: {m}")
        
        # Chỉ kiểm tra modal/dialog hoặc banner cảnh báo của hệ thống Facebook,
        # TRÁNH quét nhầm nội dung bài đăng/bình luận của sinh viên!
        if hasattr(driver, "find_elements"):
            dialogs = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'], div[role='alert'], div[aria-modal='true']")
            dialog_text = " ".join([d.text.lower() for d in dialogs if getattr(d, "is_displayed", lambda: True)()])
            for m in TEXT_MARKERS:
                if m in dialog_text:
                    raise HardStop(f"text marker: {m}")
        else:
            source = getattr(driver, "page_source", "").lower()
            for m in TEXT_MARKERS:
                if m in source:
                    raise HardStop(f"text marker: {m}")
    except HardStop:
        raise
    except Exception:
        # Nếu cửa sổ trình duyệt bị đóng hoặc mất kết nối DevTools
        pass

def set_cooldown(path, hours):
    Path(path).write_text((datetime.now() + timedelta(hours=hours)).isoformat())

def cooldown_remaining(path):
    p = Path(path)
    if not p.exists():
        return None
    until = datetime.fromisoformat(p.read_text().strip())
    return until - datetime.now() if until > datetime.now() else None
