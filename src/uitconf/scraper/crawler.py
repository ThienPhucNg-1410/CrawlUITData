"""Thu thập bằng Selenium (phần 3). Hai giai đoạn:
  discover : cuộn feed, lấy BÀI (ưu tiên 1, nhẹ) -> bảng posts
  comments : mở permalink từng bài đã chọn, lấy BÌNH LUẬN (ưu tiên 2, nặng)
Chỉ nội dung công khai. Không lưu tên/ID/ảnh/link người dùng. Gặp checkpoint -> HardStop.
"""
import time
import uuid
from datetime import datetime

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By

from .guard import HardStop, check_blocked
from .parse import bucket_of, comment_id, parse_count, parse_time, post_id_from_href, round_of

# JS chạy trong trang: trả về danh sách bình luận với cấu trúc cha–con.
# Văn bản chỉ lấy từ node dir=auto KHÔNG nằm trong thẻ <a> (tên người dùng/mention nằm trong <a>)
# và KHÔNG đọc aria-label (chứa tên tác giả) -> tối thiểu hóa dữ liệu ngay từ nguồn.
JS_COMMENTS = r"""
const root = document.querySelector('div[role="main"]') || document.body;
const arts = Array.from(root.querySelectorAll('div[role="article"]'));
const postArt = arts[0];
const out = [];
arts.slice(1).forEach((a, i) => {
  const parent = a.parentElement ? a.parentElement.closest('div[role="article"]') : null;
  const pIdx = parent ? arts.indexOf(parent) - 1 : -1;   // -1 = bình luận gốc
  const parts = Array.from(a.querySelectorAll(arguments[0]))
    .filter(n => !n.closest('a') && !n.querySelector('div[role="article"]'))
    .map(n => n.innerText.trim()).filter(Boolean);
  out.push({idx: i, parent: (pIdx >= 0 && parent !== postArt) ? pIdx : -1, text: parts.join(' ')});
});
return out;
"""

def _sleep_if_blocked(driver):
    check_blocked(driver)

def _click_all(driver, xpath, throttle, max_clicks, scope=None):
    clicks = 0
    while clicks < max_clicks:
        try:
            els = (scope or driver).find_elements(By.XPATH, xpath)
        except Exception:
            break
        els = [e for e in els if e.is_displayed()]
        if not els:
            break
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", els[0])
            els[0].click()
        except (StaleElementReferenceException, Exception):
            break
        clicks += 1
        throttle.wait("after_expand")
        _sleep_if_blocked(driver)
    return clicks

def _parse_article(art, sel):
    """Trích 1 bài từ feed. Trả None nếu không phải bài hợp lệ."""
    try:
        links = art.find_elements(By.CSS_SELECTOR, sel["permalink"])
        if not links:
            return None
        href = links[0].get_attribute("href")
        pid = post_id_from_href(href)
        if not pid:
            return None
        time_raw = (links[0].get_attribute("aria-label") or links[0].text or "").strip()
        try:
            for b in art.find_elements(By.XPATH, sel["see_more_xpath"])[:1]:
                b.click()
                time.sleep(1.0)
        except Exception:
            pass
        nodes = [n for n in art.find_elements(By.CSS_SELECTOR, sel["text_nodes"])
                 if not n.find_elements(By.XPATH, "./ancestor::a")
                 and not n.find_elements(By.XPATH, "./ancestor::div[contains(@aria-label, 'Bình luận') or contains(@aria-label, 'Comment') or contains(@aria-label, 'Phản hồi')]")]
        text = "\n".join(n.text.strip() for n in nodes if n.text.strip())
        return {"post_id": pid, "permalink": href.split("?")[0], "time_raw": time_raw, "text": text}
    except Exception:
        return None

def discover(driver, conn, cfg, throttle, max_posts, session_id=None, force_reload=False, return_stats=False):
    sid = session_id or uuid.uuid4().hex[:8]
    sel, start, end = cfg["selectors"], cfg["start_date"], cfg.get("end_date")
    conn.execute("INSERT OR IGNORE INTO sessions(session_id, started_at, stage) VALUES(?,?,?)",
                 (sid, datetime.now().isoformat(), "discover"))
    target_url = cfg["page_url"]
    if "sorting_setting" not in target_url:
        target_url += ("&" if "?" in target_url else "?") + "sorting_setting=CHRONOLOGICAL"
    
    current_u = getattr(driver, "current_url", "") or ""
    if force_reload or "groups/congdongsinhvien.hcmuit" not in current_u:
        print(f"\n[DISCOVER] {'[FORCE-RELOAD] Đang tải lại feed từ đầu:' if force_reload else 'Đang mở URL:'} {target_url}")
        print(f"[DISCOVER] Giới hạn ngày: từ {start} đến {end or 'hôm nay'} | Mục tiêu phiên này: tối đa {max_posts} bài")
        driver.get(target_url)
        time.sleep(5)
        throttle.wait("between_posts")
        _sleep_if_blocked(driver)
    else:
        print(f"\n[DISCOVER] Giữ nguyên vị trí cuộn hiện tại trên feed để tiếp tục đào sâu xuống (không lướt lại từ đầu)...")
        print(f"[DISCOVER] Giới hạn ngày: từ {start} đến {end or 'hôm nay'} | Mục tiêu đợt này: {max_posts} bài")
    # Đọc danh sách tất cả post_id đã có trong DB vào bộ nhớ (set) để tra cứu O(1) tức thì
    existing_pids = {row[0] for row in conn.execute("SELECT post_id FROM posts").fetchall()}
    min_date_row = conn.execute("SELECT MIN(created_at) FROM posts WHERE created_at IS NOT NULL").fetchone()
    oldest_collected = min_date_row[0] if min_date_row and min_date_row[0] else None
    if oldest_collected:
        print(f"[DISCOVER] Đã có {len(existing_pids)} bài trong DB. Mốc bài cũ nhất đã lưu: {oldest_collected[:16]}")
        print(f"[DISCOVER] Bật chế độ Fast-Skip: lướt nhanh qua các bài đã có để đào tiếp các bài trước mốc này...")

    seen, new, errors, old_streak = set(), 0, 0, 0
    t0 = time.time()
    scroll_count = 0
    empty_streak = 0
    last_seen_count = 0
    last_scroll_h = 0

    while new < max_posts and time.time() - t0 < cfg["session"]["max_minutes"] * 60:
        for b in driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Đóng'], div[aria-label='Close'], div[role='button'][aria-label='Close']"):
            try:
                b.click()
            except Exception:
                pass
        # 1. Trích xuất danh sách bài viết nhanh chóng qua JavaScript (1 IPC call)
        items = []
        try:
            js_get_items = """
            const sel_art = arguments[0];
            const sel_link = arguments[1];
            const arts = document.querySelectorAll(sel_art);
            const res = [];
            for (let i = 0; i < arts.length; i++) {
                const a = arts[i].querySelector(sel_link);
                if (a && a.href) {
                    res.push({ idx: i, href: a.href });
                }
            }
            return res;
            """
            res = driver.execute_script(js_get_items, sel["article"], sel["permalink"])
            if isinstance(res, list):
                items = res
        except Exception:
            items = []

        # Fallback nếu execute_script trả về rỗng (hoặc trong môi trường test mock)
        if not items:
            try:
                arts = driver.find_elements(By.CSS_SELECTOR, sel["article"])
                for idx, art in enumerate(arts):
                    links = art.find_elements(By.CSS_SELECTOR, sel["permalink"])
                    if links:
                        h = links[0].get_attribute("href")
                        if h:
                            items.append({"idx": idx, "href": h})
            except Exception:
                pass

        all_articles = None
        for it in items:
            href = it.get("href", "")
            pid = post_id_from_href(href)
            if not pid or pid in seen:
                continue
            seen.add(pid)
            
            # Fast-Skip: Nếu bài đã có trong CSDL, bỏ qua ngay lập tức trong bộ nhớ Python
            if pid in existing_pids:
                continue
            
            # Chỉ truy vấn DOM phần tử khi phát hiện BÀI MỚI CHƯA CÓ TRONG CSDL
            if all_articles is None:
                all_articles = driver.find_elements(By.CSS_SELECTOR, sel["article"])
            if it["idx"] >= len(all_articles):
                continue
            art = all_articles[it["idx"]]

            rec = _parse_article(art, sel)
            if not rec:
                continue

            iso = parse_time(rec["time_raw"])
            
            # Kiểm tra chặn bài mới hơn end_date
            if iso and end and iso[:10] > end:
                print(f"  [-] Bài {rec['post_id']} ({iso[:10]}) mới hơn end_date ({end}), bỏ qua.")
                continue
            # Kiểm tra bài cũ hơn start_date
            if iso and iso[:10] < start:
                old_streak += 1
                print(f"  [-] Bài {rec['post_id']} ({iso[:10]}) cũ hơn start_date ({start}), chuỗi chạm mốc: {old_streak}/10.")
                continue
            old_streak = 0
            
            b = bucket_of(rec["post_id"])
            conn.execute(
                "INSERT INTO posts(post_id,created_at,time_raw,text,bucket,round,permalink,collected_at,session_id)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (rec["post_id"], iso, rec["time_raw"], rec["text"], b, round_of(b, cfg["rounds"]),
                 rec["permalink"], datetime.now().isoformat(), sid))
            conn.commit()               # checkpoint sau mỗi bài (3.9)
            existing_pids.add(rec["post_id"])
            new += 1
            summary = rec["text"][:70].replace("\n", " ") if rec["text"] else "(không có văn bản)"
            print(f"  [+] [{new}/{max_posts}] CÀO MỚI bài {rec['post_id']} | Thời gian: {iso or rec['time_raw']} | {summary}...")
            if new >= max_posts:
                break
        if old_streak >= 10:
            print(f"\n[DISCOVER] Đã chạm mốc thời gian {start} liên tục 10 lần. Dừng cuộn.")
            break

        # Kiểm tra tiến độ: nếu vẫn thấy post_id mới xuất hiện trên trang -> feed vẫn đang tải bình thường
        if len(seen) > last_seen_count:
            empty_streak = 0
        else:
            empty_streak += 1
        last_seen_count = len(seen)

        # Xử lý gỡ kẹt (Un-stuck) khi feed có dấu hiệu chậm tải:
        if empty_streak in (3, 6, 10, 15, 20, 26, 32):
            print(f"  [!] Feed chậm xuất hiện bài mới (chuỗi trống {empty_streak}). Đang gỡ kẹt lazy-load...")
            # 1. Thử bấm các nút "Thử lại" / "Tải lại" nếu Facebook hiển thị lỗi mạng
            try:
                retry_btns = driver.find_elements(By.XPATH, "//div[@role='button']//span[contains(text(), 'Thử lại') or contains(text(), 'thử lại') or contains(text(), 'Retry') or contains(text(), 'Tải lại') or contains(text(), 'Xem thêm')]")
                for btn in retry_btns:
                    driver.execute_script("arguments[0].click();", btn)
                    print("  [✓] Đã kích hoạt nút 'Thử lại' trên giao diện.")
                    time.sleep(1.5)
            except Exception:
                pass
            # 2. Giật cuộn ngược lên 3000px rồi nhấp xuống để kích hoạt IntersectionObserver & scroll event
            try:
                driver.execute_script("window.scrollBy(0, -3000);")
                time.sleep(1.2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                driver.execute_script("window.dispatchEvent(new Event('scroll'));")
                time.sleep(1.8)
            except Exception:
                pass

        max_empty = 36 if new == 0 else 18
        if empty_streak >= max_empty:
            print(f"\n[DISCOVER] Đã cuộn liên tục {empty_streak} lần mà không có bài nào mới xuất hiện (chạm đáy feed).")
            print(f"[DISCOVER] Kết thúc lượt quét bài đợt này (đã lưu {new} bài mới, tổng bài quét: {len(seen)}).")
            break

        scroll_count += 1
        
        # Nếu đang lướt qua các bài đã có (new == 0), cuộn nhanh 0.9s để vượt qua bài cũ
        if new == 0:
            driver.execute_script("window.scrollBy(0, 3500);")
            time.sleep(0.9)
            if scroll_count % 4 == 0 or len(seen) % 25 == 0:
                pct = int(len(seen) * 100 / max(1, len(existing_pids)))
                print(f"  [Fast-Skip Siêu Tốc] Đang lướt nhanh qua bài cũ: {len(seen)}/{len(existing_pids)} bài ({pct}%)...")
        else:
            driver.execute_script("window.scrollBy(0, 2200);")
            w = throttle.wait("scroll")
            if scroll_count % 12 == 0:
                import random
                pause_time = random.uniform(6.0, 10.0)
                print(f"  [~] Tạm dừng đọc bài {pause_time:.1f}s (giả lập người thật để giữ an toàn cho nick)...")
                time.sleep(pause_time)
            print(f"  [~] Cuộn trang lần {scroll_count}... (nghỉ {w:.1f}s, bài mới đợt này: {new}, tổng bài đã quét: {len(seen)})")
            
        _sleep_if_blocked(driver)
    conn.execute("UPDATE sessions SET ended_at=?, n_new=?, n_errors=? WHERE session_id=?",
                 (datetime.now().isoformat(), new, errors, sid))
    conn.commit()
    print(f"\n[DISCOVER] Hoàn thành phiên: Đã lưu {new} bài mới, {errors} lỗi tham chiếu.")
    if return_stats:
        return new, len(seen)
    return new

def select_posts_for_comments(conn, cfg, rnd, limit, relevant_fn):
    f = cfg["comments_filter"]
    rows = conn.execute("SELECT post_id, permalink, text, reactions, n_comments FROM posts "
                        "WHERE status='post_only' AND round<=? ORDER BY round, created_at", (rnd,)).fetchall()
    
    # Đọc nhãn từ gold.csv và review_labeled.csv nếu có
    # Chỉ lấy các bài có nhãn thuộc nhóm đánh giá thực thể trường: trung_tinh, tich_cuc, tieu_cuc (và hoi_dap nếu muốn đào thêm)
    valid_sentiment_pids = set()
    non_relevant_pids = set()
    try:
        import os
        import pandas as pd
        for pth in ["data/labeled/gold.csv", "data/labeled/review_labeled.csv"]:
            if os.path.exists(pth):
                df = pd.read_csv(pth)
                if "label" in df.columns and "post_id" in df.columns:
                    for _, row in df.iterrows():
                        pid = str(row["post_id"])
                        lbl = str(row["label"])
                        if lbl in ("trung_tinh", "tich_cuc", "tieu_cuc", "hoi_dap"):
                            valid_sentiment_pids.add(pid)
                        else:
                            non_relevant_pids.add(pid)
    except Exception:
        pass

    out = []
    for r in rows:
        pid = str(r["post_id"])
        # 1. Nếu post gốc KHÔNG phải là bài đánh giá trường (khong_lien_quan) -> BỎ QUA TUYỆT ĐỐI
        if pid in non_relevant_pids:
            continue
        # 2. Nếu bài đã được xác nhận là trung_tinh / tich_cuc / tieu_cuc / hoi_dap -> Ưu tiên lấy
        if pid not in valid_sentiment_pids and f.get("only_relevant", True):
            if not relevant_fn(r["text"] or ""):
                continue
        # 3. Kiểm tra số lượng phản hồi nếu có cấu hình
        if (r["n_comments"] or 0) < f["min_comments"] and (r["reactions"] or 0) < f["min_reactions"]:
            # chưa biết số liệu (None) thì vẫn cho qua
            if r["n_comments"] is not None or r["reactions"] is not None:
                continue
        out.append(r)
        if len(out) >= limit:
            break
    return out

def collect_comments(driver, conn, cfg, throttle, posts, session_id=None):
    sid = session_id or uuid.uuid4().hex[:8]
    sel = cfg["selectors"]
    conn.execute("INSERT OR IGNORE INTO sessions(session_id, started_at, stage) VALUES(?,?,?)",
                 (sid, datetime.now().isoformat(), "comments"))
    n_comments, errors = 0, 0
    t0 = time.time()
    total_posts = len(posts)
    print(f"\n[COMMENTS] Bắt đầu thu thập bình luận cho {total_posts} bài viết...")
    main_handle = driver.current_window_handle
    for idx, p in enumerate(posts, start=1):
        if time.time() - t0 > cfg["session"]["max_minutes"] * 60:
            print("[COMMENTS] Hết thời gian tối đa phiên cào bình luận.")
            break
        print(f"\n  [*] [{idx}/{total_posts}] Đang mở bài {p['post_id']} ({p['permalink']})...")
        try:
            # Mở tab phụ để cào bình luận, giữ nguyên vị trí cuộn của tab feed chính
            driver.switch_to.new_window('tab')
            driver.get(p["permalink"])
            throttle.wait("between_posts")
            _sleep_if_blocked(driver)
            for b in driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Đóng'], div[aria-label='Close'], div[role='button'][aria-label='Close']"):
                try:
                    b.click()
                except Exception:
                    pass
            k = cfg["session"]["max_expand_clicks"]
            c1 = _click_all(driver, sel["more_comments_xpath"], throttle, k)
            c2 = _click_all(driver, sel["reply_xpath"], throttle, k)
            rows = driver.execute_script(JS_COMMENTS, sel["text_nodes"])
            ids = {}
            post_comms = 0
            for r in rows:
                parent = ids.get(r["parent"]) if r["parent"] >= 0 else None
                cid = comment_id(p["post_id"], parent, r["text"], r["idx"])
                ids[r["idx"]] = cid
                if not r["text"]:
                    continue
                conn.execute("INSERT OR IGNORE INTO comments(comment_id,post_id,parent_id,text,collected_at,session_id)"
                             " VALUES(?,?,?,?,?,?)",
                             (cid, p["post_id"], parent, r["text"], datetime.now().isoformat(), sid))
                n_comments += 1
                post_comms += 1
            print(f"      -> Thu được {post_comms} bình luận cho bài {p['post_id']}.")
            full = (c1 < k and c2 < k)
            conn.execute("UPDATE posts SET status=? WHERE post_id=?",
                         ("comments_full" if full else "comments_partial", p["post_id"]))
            conn.commit()
        except HardStop:
            conn.execute("UPDATE sessions SET ended_at=?, n_new=?, n_errors=?, note=? WHERE session_id=?",
                         (datetime.now().isoformat(), n_comments, errors, "HARD_STOP", sid))
            conn.commit()
            raise
        except Exception as e:           # timeout/không thấy phần tử: ghi log, bỏ qua bài (3.7)
            errors += 1
            conn.execute("INSERT INTO warnings(at,session_id,kind,last_action) VALUES(?,?,?,?)",
                         (datetime.now().isoformat(), sid, f"error:{type(e).__name__}", throttle.last_action))
            conn.commit()
            throttle.escalate()          # backoff bậc 1
        finally:
            try:
                if len(driver.window_handles) > 1 and driver.current_window_handle != main_handle:
                    driver.close()
                driver.switch_to.window(main_handle)
            except Exception:
                pass
    conn.execute("UPDATE sessions SET ended_at=?, n_new=?, n_errors=? WHERE session_id=?",
                 (datetime.now().isoformat(), n_comments, errors, sid))
    conn.commit()
    return n_comments

def health_check(driver, cfg):
    """Chạy trên post mẫu đã biết kết quả; lệch -> dừng (3.6)."""
    sel = cfg["selectors"]
    for case in cfg.get("health_check", []):
        if not case.get("url"):
            continue
        driver.get(case["url"])
        time.sleep(5)
        check_blocked(driver)
        arts = driver.find_elements(By.CSS_SELECTOR, sel["article"])
        if not arts:
            return False, f"không thấy article ở {case['url']}"
        rec = _parse_article(arts[0], sel)
        if not rec or len(rec["text"]) < case["expect_min_text_len"]:
            return False, "text rỗng/quá ngắn"
        if case.get("expect_has_time") and not parse_time(rec["time_raw"]):
            return False, "không parse được thời gian"
    return True, "ok"
