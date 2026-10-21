"""
scripts/discover_by_search.py
==============================
Tìm kiếm và phát hiện các bài viết lịch sử từ tháng 01/2026 đến tháng 06/2026
thông qua tính năng Search của Group Facebook UIT.
- Khắc phục giới hạn độ sâu cuộn feed của Facebook.
- Dùng từ khóa chủ đạo sinh viên UIT hay thảo luận.
- Tự động trích xuất permalink, thời gian và chèn vào bảng posts (status='post_only').
"""

import sys
import time
import random
import logging
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.db import connect
from uitconf.scraper.driver import make_driver
from uitconf.scraper.guard import check_blocked, HardStop
from uitconf.scraper.parse import parse_time, post_id_from_href, bucket_of, round_of

log = logging.getLogger("SearchDiscovery")

SEARCH_KEYWORDS = [
    "k19", "k18", "k17", "thi", "môn", "thầy", "học", "đkmh", 
    "điểm", "khoa", "học phí", "toeic", "chuẩn đầu ra", "đồ án", 
    "thực tập", "kỳ hè", "tín chỉ", "ctdt", "giảng viên", "học bổng", "phúc khảo"
]


def run_search_discovery(headless=True, max_keywords=5):
    cfg = C.load()
    db_path = BASE_DIR / cfg["paths"]["raw_db"]
    conn = connect(str(db_path))

    c = conn.cursor()
    c.execute("SELECT post_id FROM posts")
    existing_pids = {row[0] for row in c.fetchall()}

    session_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conn.execute(
        "INSERT INTO sessions (session_id, started_at, stage, note) VALUES (?, ?, ?, ?)",
        (session_id, datetime.now().isoformat(), "discover_by_search", f"keywords={len(SEARCH_KEYWORDS)}")
    )
    conn.commit()

    driver = None
    total_new = 0

    # Xáo trộn từ khóa để đa dạng hóa kết quả
    keywords = list(SEARCH_KEYWORDS)
    random.shuffle(keywords)
    selected_keywords = keywords[:max_keywords]

    log.info("=" * 68)
    log.info(f"🔍 BẮT ĐẦU TÌM KIẾM BÀI VIẾT QUA FACEBOOK GROUP SEARCH")
    log.info(f"- Từ khóa đợt này ({len(selected_keywords)}): {', '.join(selected_keywords)}")
    log.info("=" * 68)

    try:
        driver = make_driver(cfg, headless=headless, enable_images=False)

        for kw_idx, kw in enumerate(selected_keywords, 1):
            search_url = f"https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q={kw}"
            log.info(f"\n[{kw_idx}/{len(selected_keywords)}] Tìm kiếm với từ khóa: '{kw}' ...")

            try:
                driver.get(search_url)
                time.sleep(random.uniform(3.5, 5.0))
            except Exception as e:
                log.warning(f"[!] Lỗi khi mở URL search: {e}")
                continue

            # Kiểm tra chặn tài khoản
            try:
                check_blocked(driver)
            except HardStop as hs:
                log.error(f"[CRITICAL] Bị rate limit: {hs}")
                break

            kw_new_count = 0
            seen_in_kw = set()

            # Cuộn 8 - 12 lần cho mỗi từ khóa để lấy bài
            for scroll_i in range(10):
                js_extract = """
                const links = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]'));
                return links.map(a => {
                    const art = a.closest('div[role="feed"]') || a.closest('div[role="article"]') || a.parentElement;
                    let text = '';
                    if (art) {
                        const tNodes = Array.from(art.querySelectorAll('div[dir="auto"]'));
                        text = tNodes.map(n => n.innerText.trim()).filter(Boolean).join('\\n');
                    }
                    return {
                        href: a.href.split('?')[0],
                        text: text,
                        aria: a.getAttribute('aria-label') || (a.querySelector('span') ? a.querySelector('span').innerText : '') || a.innerText || ''
                    };
                });
                """
                try:
                    candidates = driver.execute_script(js_extract)
                except Exception:
                    candidates = []

                if isinstance(candidates, list):
                    for item in candidates:
                        href = item.get("href", "")
                        pid = post_id_from_href(href)
                        if not pid or pid in seen_in_kw:
                            continue
                        seen_in_kw.add(pid)

                        if pid in existing_pids:
                            continue

                        raw_t = item.get("aria", "") or ""
                        iso_t = parse_time(raw_t)
                        post_txt = item.get("text", "")

                        # Lọc bài viết trong năm 2026
                        if iso_t and not iso_t.startswith("2026"):
                            continue

                        bucket = bucket_of(pid)
                        round_num = round_of(bucket, cfg["rounds"])
                        now_iso = datetime.now().isoformat()

                        conn.execute("""
                            INSERT OR IGNORE INTO posts 
                            (post_id, created_at, time_raw, text, bucket, round, permalink, collected_at, session_id, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'post_only')
                        """, (pid, iso_t, raw_t, post_txt, bucket, round_num, href, now_iso, session_id))
                        conn.commit()

                        existing_pids.add(pid)
                        kw_new_count += 1
                        total_new += 1

                        month_str = iso_t[:7] if iso_t else "2026"
                        snippet = post_txt.replace('\n', ' ')[:45]
                        log.info(f"  [+] Đào được PID {pid} | Tháng {month_str} | {snippet!r}")

                # Cuộn tiếp
                try:
                    driver.execute_script("window.scrollBy(0, 2200);")
                    time.sleep(random.uniform(1.5, 2.5))
                except Exception:
                    time.sleep(2)

            log.info(f"  => Từ khóa '{kw}' phát hiện thêm: +{kw_new_count} bài viết mới.")
            time.sleep(random.uniform(3.0, 5.0))

    except Exception as e:
        log.error(f"[Search] Ngoại lệ tìm kiếm: {e}", exc_info=True)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        conn.close()
        log.info(f"[Search] Hoàn tất đợt tìm kiếm. Tổng cộng phát hiện mới: +{total_new} bài.")

    return total_new


if __name__ == "__main__":
    run_search_discovery(headless=True, max_keywords=3)

