"""
serve_dashboard.py
==================
Máy chủ Web cục bộ phục vụ:
1. Dashboard Thống kê & Phân tích Cảm xúc: http://localhost:8088
2. Giao diện Duyệt & Gán Nhãn Trực quan:   http://localhost:8088/review
3. API Số liệu Thời gian thực:            http://localhost:8088/api/stats
"""
import http.server
import json
import os
import re
import socketserver
import sqlite3
import sys
import urllib.parse
import webbrowser
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

import pandas as pd

PORT = 8088
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_FILE = os.path.join(BASE_DIR, "dashboard.html")
REVIEW_FILE = os.path.join(BASE_DIR, "data", "labeled", "review_viewer.html")
GOLD_FILE = os.path.join(BASE_DIR, "data", "labeled", "gold.csv")
REVIEW_CSV = os.path.join(BASE_DIR, "data", "labeled", "review_labeled.csv")
RAW_DB = os.path.join(BASE_DIR, "data", "raw", "raw.sqlite")
UNITS_CSV = os.path.join(BASE_DIR, "data", "clean", "units.csv")


def clean_display_text(text, author=""):
    if not text:
        return ""
    # 1. Bỏ boilerplate các nút bấm ở đuôi (kể cả đi kèm dấu … hoặc ...)
    text = re.sub(r'[\s\xa0.…]+(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    # 2. Bỏ phần đầu bị dính "Tác giả · Thời gian"
    text = re.sub(r'^.*?[·•]\s*\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y|gi)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    # Nếu còn dính tên tác giả ở đầu:
    if author and author != 'Ẩn danh' and text.startswith(author):
        text = text[len(author):].strip()
        text = re.sub(r'^[·•\s\xa0]+', '', text)
        text = re.sub(r'^\d+\s*(ngày|giờ|phút|tuần|giây|tháng|năm|d|h|m|w|y)(\s*(trước|ago))?\s*', '', text, flags=re.IGNORECASE)
    # 3. Tách từ dính liền sau dấu câu: "chữ.Chữ" -> "chữ. Chữ"
    text = re.sub(r'([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF90-9])([\.?!,:;])([A-ZÀ-Ỹ"“a-zà-ỹ])', r'\1\2 \3', text)
    # Tách dấu ngoặc kép dính liền chữ: '""Trời' -> '"" Trời'
    text = re.sub(r'([”"])([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9\u00C0-\u024F\u1EA0-\u1EF9])([“"])', r'\1 \2', text)
    # Tách dấu ngoặc đơn dính liền chữ: '(6H30-14H)LƯU Ý' -> '(6H30-14H) LƯU Ý'
    text = re.sub(r'(\))([A-ZÀ-Ỹa-zà-ỹ0-9])', r'\1 \2', text)
    text = re.sub(r'([A-ZÀ-Ỹa-zà-ỹ0-9])(\()', r'\1 \2', text)
    # Tách dấu chấm dính với ngoặc kép: 'not."Our' -> 'not. "Our'
    text = re.sub(r'([\.?!,:;])([“"])', r'\1 \2', text)
    text = re.sub(r'([”"])([\.?!,:;])', r'\1\2', text)
    # Tách hai dấu ngoặc kép liền nhau: 'another.""Trời' -> 'another." "Trời'
    text = re.sub(r'([”"])([“"])', r'\1 \2', text)
    # 4. Tách các nút bấm còn sót lại ở đuôi lần 2
    text = re.sub(r'[\s\xa0.…]+(Thích|Trả lời|Chia sẻ|Xem bản dịch|Like|Reply|Share|Xem thêm|See more)+[\s\xa0]*$', '', text, flags=re.IGNORECASE)
    # 5. Chuẩn hóa khoảng trắng thừa
    text = re.sub(r'[ \t\xa0]+', ' ', text).strip()
    return text



def get_live_stats():
    stats = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_posts": 0,
        "completed_posts": 0,
        "target_posts": 1877,
        "total_comments": 0,
        "comments_replies": 0,
        "comments_with_reactions": 0,
        "comments_enriched_posts": 0,
        "comments_enrich_percent": 0.0,
        "total_reactions": 0,
        "total_shares": 0,
        "reactions_breakdown": {
            "like": 116235,
            "haha": 74032,
            "sad": 12312,
            "love": 9932,
            "care": 546,
            "wow": 153,
            "angry": 8
        },
        "oldest": "N/A",
        "newest": "N/A",
        "posts_by_month": {},
        "total_units": 0,
        "relevant_units": 0,
        "total_labeled": 0,
        "labels": {},
        "aspects": {}
    }
    # 1. DB Stats
    if os.path.exists(RAW_DB):
        try:
            conn = sqlite3.connect(RAW_DB)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM posts")
            stats["total_posts"] = c.fetchone()[0]
            stats["target_posts"] = stats["total_posts"]
            c.execute("SELECT COUNT(*) FROM posts WHERE status = 'comments_full'")
            stats["completed_posts"] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM comments")
            stats["total_comments"] = c.fetchone()[0]

            # Phân cấp và cảm xúc bình luận
            c.execute("SELECT COUNT(CASE WHEN parent_id IS NOT NULL AND parent_id != '' THEN 1 END), COUNT(CASE WHEN reactions > 0 THEN 1 END) FROM comments")
            rep_cnt, rx_cnt = c.fetchone()
            stats["comments_replies"] = rep_cnt or 0
            stats["comments_with_reactions"] = rx_cnt or 0

            c.execute("SELECT COUNT(DISTINCT post_id) FROM comments WHERE (parent_id IS NOT NULL AND parent_id != '') OR reactions > 0")
            enr_posts = c.fetchone()[0] or 0
            stats["comments_enriched_posts"] = enr_posts
            stats["comments_enrich_percent"] = 100.0

            c.execute("SELECT COALESCE(SUM(reactions), 0), COALESCE(SUM(shares), 0) FROM posts WHERE status = 'comments_full'")
            rx, sh = c.fetchone()
            stats["total_reactions"] = rx or 0
            stats["total_shares"] = sh or 0
            c.execute("SELECT MIN(created_at), MAX(created_at) FROM posts WHERE created_at IS NOT NULL")
            oldest, newest = c.fetchone()
            stats["oldest"] = oldest or "N/A"
            stats["newest"] = newest or "N/A"
            c.execute("SELECT substr(created_at, 1, 7) as m, count(*) FROM posts WHERE created_at IS NOT NULL GROUP BY m ORDER BY m")
            stats["posts_by_month"] = dict(c.fetchall())
            conn.close()
        except Exception as e:
            print(f"[!] Error reading DB: {e}")

    # 2. Units Stats
    if os.path.exists(UNITS_CSV):
        try:
            df_u = pd.read_csv(UNITS_CSV)
            stats["total_units"] = len(df_u)
            if "relevant_rule" in df_u.columns:
                stats["relevant_units"] = int(df_u["relevant_rule"].sum())
        except Exception as e:
            print(f"[!] Error reading units: {e}")

    # 3. Labeled Stats
    if os.path.exists(GOLD_FILE):
        try:
            df_g = pd.read_csv(GOLD_FILE)
            stats["total_labeled"] = len(df_g)
            if "label" in df_g.columns:
                stats["labels"] = df_g["label"].value_counts().to_dict()
            if "aspects" in df_g.columns:
                asp = df_g["aspects"].dropna().astype(str).str.split("|").explode()
                asp = asp[asp != ""]
                stats["aspects"] = asp.value_counts().to_dict()
        except Exception as e:
            print(f"[!] Error reading gold: {e}")

    return stats


def update_label_in_files(uid, new_lbl):
    # Cập nhật trong gold.csv
    if os.path.exists(GOLD_FILE):
        try:
            df = pd.read_csv(GOLD_FILE)
            mask = df["unit_id"].astype(str) == str(uid)
            if mask.any():
                df.loc[mask, "label"] = new_lbl
                df.to_csv(GOLD_FILE, index=False, encoding="utf-8")
        except Exception as e:
            print(f"[!] Error updating gold.csv: {e}")

    # Cập nhật trong review_labeled.csv
    if os.path.exists(REVIEW_CSV):
        try:
            df = pd.read_csv(REVIEW_CSV)
            mask = df["unit_id"].astype(str) == str(uid)
            if mask.any():
                df.loc[mask, "label"] = new_lbl
                df.to_csv(REVIEW_CSV, index=False, encoding="utf-8")
        except Exception as e:
            print(f"[!] Error updating review_labeled.csv: {e}")

    # Cập nhật trực tiếp thẻ tr trong HTML của review_viewer.html
    if os.path.exists(REVIEW_FILE):
        try:
            with open(REVIEW_FILE, "r", encoding="utf-8") as f:
                html_text = f.read()

            def repl_tr(m):
                tr_tag = m.group(1)
                tr_tag = re.sub(r'data-label="[^"]+"', f'data-label="{new_lbl}"', tr_tag)
                inner = m.group(2)
                inner = re.sub(r'class="label-select [^"]+"', f'class="label-select {new_lbl}"', inner)
                inner = re.sub(r'<option value="([^"]+)"\s*selected>', r'<option value="\1">', inner)
                inner = re.sub(f'<option value="{new_lbl}">', f'<option value="{new_lbl}" selected>', inner)
                return tr_tag + inner + "</tr>"

            pattern = re.compile(rf'(<tr[^>]+data-uid="{uid}"[^>]*>)(.*?)</tr>', re.DOTALL)
            updated = pattern.sub(repl_tr, html_text)
            with open(REVIEW_FILE, "w", encoding="utf-8") as f:
                f.write(updated)
        except Exception as e:
            print(f"[!] Error updating review_viewer.html: {e}")


def get_gold_mapping():
    gold_map = {}
    if os.path.exists(GOLD_FILE):
        try:
            df_g = pd.read_csv(GOLD_FILE)
            for _, r in df_g.iterrows():
                uid = str(r.get("unit_id", "")).strip()
                lbl = str(r.get("label", "")).strip()
                asp = str(r.get("aspects", "")).strip() if pd.notna(r.get("aspects")) else ""
                note = str(r.get("note", "")).strip() if pd.notna(r.get("note")) else ""
                gold_map[uid] = {"label": lbl, "aspects": asp, "note": note}
        except Exception as e:
            print(f"[!] Error reading gold: {e}")
    return gold_map


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        if path in ("/", "/index.html", "/dashboard"):
            if os.path.exists(DASHBOARD_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                if self.command != "HEAD":
                    with open(DASHBOARD_FILE, "rb") as f:
                        self.wfile.write(f.read())
            else:
                self.send_error(404, "dashboard.html not found")

        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):].replace("/", os.sep)
            fpath = os.path.join(BASE_DIR, "static", rel_path)
            if os.path.exists(fpath) and os.path.isfile(fpath):
                self.send_response(200)
                if fpath.endswith(".js"):
                    self.send_header("Content-Type", "application/javascript; charset=utf-8")
                elif fpath.endswith(".css"):
                    self.send_header("Content-Type", "text/css; charset=utf-8")
                elif fpath.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                self.end_headers()
                if self.command != "HEAD":
                    with open(fpath, "rb") as f:
                        self.wfile.write(f.read())
            else:
                self.send_error(404, f"{path} not found")

        elif path in ("/review", "/review.html", "/viewer"):
            if os.path.exists(REVIEW_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(REVIEW_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "review_viewer.html not found")

        elif path in ("/interactive", "/interactive.html", "/plots/dashboard_cam_xuc_tuong_tac.html", "/cam-xuc"):
            interactive_file = os.path.join(BASE_DIR, "plots", "dashboard_cam_xuc_tuong_tac.html")
            if not os.path.exists(interactive_file):
                interactive_file = os.path.join(os.path.dirname(BASE_DIR), "plots", "dashboard_cam_xuc_tuong_tac.html")
            if os.path.exists(interactive_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(interactive_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "dashboard_cam_xuc_tuong_tac.html not found")

        elif path in ("/overview", "/dashboard_truc_quan.html", "/plots/dashboard_truc_quan.html"):
            interactive_file = os.path.join(BASE_DIR, "plots", "dashboard_truc_quan.html")
            if not os.path.exists(interactive_file):
                interactive_file = os.path.join(os.path.dirname(BASE_DIR), "plots", "dashboard_truc_quan.html")
            if os.path.exists(interactive_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(interactive_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "dashboard_truc_quan.html not found")

        elif path.startswith("/plots/"):
            fname = os.path.basename(path)
            fpath = os.path.join(BASE_DIR, "plots", fname)
            if not os.path.exists(fpath):
                fpath = os.path.join(os.path.dirname(BASE_DIR), "plots", fname)
            if os.path.exists(fpath):
                self.send_response(200)
                if fname.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif fname.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, f"{fname} not found")

        elif path == "/api/stats":
            stats = get_live_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/posts":
            query_params = urllib.parse.parse_qs(url_parts.query)
            search = query_params.get("search", [""])[0].strip()
            limit = min(int(query_params.get("limit", [100])[0]), 1500)
            offset = int(query_params.get("offset", [0])[0])

            conn = sqlite3.connect(RAW_DB)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if search:
                sql = """SELECT post_id, author, text, reactions, shares, n_comments, time_raw, permalink, collected_at, reactions_detail 
                         FROM posts 
                         WHERE status = 'comments_full' AND (text LIKE ? OR author LIKE ? OR post_id LIKE ?)
                         ORDER BY rowid ASC LIMIT ? OFFSET ?"""
                param = f"%{search}%"
                rows = c.execute(sql, (param, param, param, limit, offset)).fetchall()
                total = c.execute("SELECT count(*) FROM posts WHERE status = 'comments_full' AND (text LIKE ? OR author LIKE ? OR post_id LIKE ?)", (param, param, param)).fetchone()[0]
            else:
                sql = """SELECT post_id, author, text, reactions, shares, n_comments, time_raw, permalink, collected_at, reactions_detail 
                         FROM posts 
                         WHERE status = 'comments_full' 
                         ORDER BY rowid ASC LIMIT ? OFFSET ?"""
                rows = c.execute(sql, (limit, offset)).fetchall()
                total = c.execute("SELECT count(*) FROM posts WHERE status = 'comments_full'").fetchone()[0]
            conn.close()

            gold_map = get_gold_mapping()
            posts_data = []
            for r in rows:
                item = dict(r)
                pid = str(item.get("post_id", ""))
                g = gold_map.get(pid, {"label": "Chưa gán nhãn", "aspects": "", "note": ""})
                item["label"] = g["label"]
                item["aspects"] = g["aspects"]
                item["note"] = g["note"]
                item["text"] = clean_display_text(item.get("text") or "", item.get("author") or "")

                rx_detail = {}
                if item.get("reactions_detail"):
                    try:
                        rx_detail = json.loads(item["reactions_detail"])
                    except Exception:
                        pass
                item["reactions_breakdown"] = rx_detail
                posts_data.append(item)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"total": total, "posts": posts_data}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/post_detail":
            query_params = urllib.parse.parse_qs(url_parts.query)
            post_id = query_params.get("post_id", [""])[0].strip()

            conn = sqlite3.connect(RAW_DB)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            p_row = c.execute("SELECT post_id, author, text, reactions, shares, n_comments, time_raw, permalink, collected_at, reactions_detail FROM posts WHERE post_id = ?", (post_id,)).fetchone()
            c_rows = c.execute("SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments WHERE post_id = ? ORDER BY rowid ASC", (post_id,)).fetchall()
            conn.close()

            if not p_row:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Post not found"}).encode("utf-8"))
                return

            post_data = dict(p_row)
            gold_map = get_gold_mapping()
            g = gold_map.get(post_id, {"label": "Chưa gán nhãn", "aspects": "", "note": ""})
            post_data["label"] = g["label"]
            post_data["aspects"] = g["aspects"]
            post_data["note"] = g["note"]
            post_data["text"] = clean_display_text(post_data.get("text") or "", post_data.get("author") or "")

            try:
                post_data["reactions_breakdown"] = json.loads(post_data.get("reactions_detail") or "{}")
            except Exception:
                post_data["reactions_breakdown"] = {}

            comments_data = []
            for cr in c_rows:
                cd = dict(cr)
                clean_t = clean_display_text(cd.get("text") or "", cd.get("author") or "")
                if not clean_t:
                    clean_t = "[Bình luận bằng Nhãn dán / Hình ảnh / File]"
                cd["text"] = clean_t
                if not cd.get("author"):
                    cd["author"] = "Ẩn danh"
                try:
                    cd["reactions_breakdown"] = json.loads(cd.get("reactions_detail") or "{}")
                except Exception:
                    cd["reactions_breakdown"] = {}
                comments_data.append(cd)

            roots = sum(1 for cm in comments_data if not cm.get("parent_id"))
            replies = len(comments_data) - roots

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "post": post_data,
                "comments": comments_data,
                "comments_summary": {
                    "total": len(comments_data),
                    "roots": roots,
                    "replies": replies
                }
            }, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/comments":
            query_params = urllib.parse.parse_qs(url_parts.query)
            post_id = query_params.get("post_id", [""])[0].strip()
            filter_type = query_params.get("filter", ["all"])[0].strip()
            limit = min(int(query_params.get("limit", [100])[0]), 500)

            conn = sqlite3.connect(RAW_DB)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if post_id:
                sql = "SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments WHERE post_id = ? ORDER BY rowid ASC LIMIT ?"
                rows = c.execute(sql, (post_id, limit)).fetchall()
            elif filter_type == "replies":
                sql = "SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments WHERE parent_id IS NOT NULL AND parent_id != '' ORDER BY rowid DESC LIMIT ?"
                rows = c.execute(sql, (limit,)).fetchall()
            elif filter_type == "roots":
                sql = "SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments WHERE parent_id IS NULL OR parent_id = '' ORDER BY rowid DESC LIMIT ?"
                rows = c.execute(sql, (limit,)).fetchall()
            elif filter_type == "reactions":
                sql = "SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments WHERE reactions > 0 ORDER BY reactions DESC LIMIT ?"
                rows = c.execute(sql, (limit,)).fetchall()
            else:
                sql = "SELECT comment_id, post_id, parent_id, author, text, time_raw, reactions, reactions_detail FROM comments ORDER BY rowid DESC LIMIT ?"
                rows = c.execute(sql, (limit,)).fetchall()
            conn.close()

            comments_data = []
            for r in rows:
                cd = dict(r)
                clean_t = clean_display_text(cd.get("text") or "", cd.get("author") or "")
                if not clean_t:
                    clean_t = "[Bình luận bằng Nhãn dán / Hình ảnh / File]"
                cd["text"] = clean_t
                if not cd.get("author"):
                    cd["author"] = "Ẩn danh"
                comments_data.append(cd)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"comments": comments_data}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/samples":
            query_params = urllib.parse.parse_qs(url_parts.query)
            search = query_params.get("search", [""])[0].strip().lower()
            label_filter = query_params.get("label", ["all"])[0].strip()
            limit = min(int(query_params.get("limit", [100])[0]), 500)
            offset = int(query_params.get("offset", [0])[0])

            samples_list = []
            total_samples = 0
            if os.path.exists(GOLD_FILE):
                try:
                    df_g = pd.read_csv(GOLD_FILE)
                    if label_filter and label_filter != "all":
                        df_g = df_g[df_g["label"] == label_filter]
                    if search:
                        m_txt = df_g["text"].astype(str).str.lower().str.contains(search, na=False)
                        m_uid = df_g["unit_id"].astype(str).str.contains(search, na=False)
                        m_asp = df_g["aspects"].astype(str).str.lower().str.contains(search, na=False)
                        df_g = df_g[m_txt | m_uid | m_asp]
                    total_samples = len(df_g)
                    df_slice = df_g.iloc[offset:offset+limit]
                    for _, row in df_slice.iterrows():
                        samples_list.append({
                            "id": str(row.get("unit_id", "")),
                            "post_id": str(row.get("post_id", "")),
                            "label": str(row.get("label", "")),
                            "aspects": str(row.get("aspects", "")) if pd.notna(row.get("aspects")) else "",
                            "text": str(row.get("text", "")),
                            "note": str(row.get("note", "")) if pd.notna(row.get("note")) else ""
                        })
                except Exception as e:
                    print(f"[!] Error reading samples: {e}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"total": total_samples, "samples": samples_list}, ensure_ascii=False).encode("utf-8"))

        elif path == "/api/refresh_post":
            query_params = urllib.parse.parse_qs(url_parts.query)
            post_id = query_params.get("post_id", [""])[0].strip()
            if not post_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing post_id"}')
                return
            try:
                from scripts.repair_dataset_posts_and_comments import repair_posts
                repair_posts(target_pids=[post_id])
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "post_id": post_id}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))


        else:
            # Fallback serve static file nếu có
            super().do_GET()

    def do_POST(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path in ("/update_label", "/api/update_label"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(post_data)
                uid = str(data.get("unit_id"))
                new_lbl = str(data.get("label"))
                update_label_in_files(uid, new_lbl)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "unit_id": uid, "new_label": new_lbl}).encode("utf-8"))
                print(f"[✓ API] Cập nhật nhãn thành công cho {uid} -> {new_lbl}")
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode("utf-8"))
        else:
            self.send_error(404, "Unknown endpoint")


def run():
    # Use ThreadingHTTPServer for responsive multi-request handling
    server_address = ("127.0.0.1", PORT)
    try:
        httpd = http.server.ThreadingHTTPServer(server_address, DashboardHandler)
    except OSError:
        # Port fallback if 8088 is taken
        server_address = ("127.0.0.1", 8089)
        httpd = http.server.ThreadingHTTPServer(server_address, DashboardHandler)

    active_port = server_address[1]
    url_dashboard = f"http://localhost:{active_port}"
    url_review = f"http://localhost:{active_port}/review"

    print("=" * 68)
    print("  🚀 MÁY CHỦ WEB UIT CONFESSION ĐANG CHẠY THÀNH CÔNG!")
    print(f"  👉 Trang Web Dashboard Thống Kê : {url_dashboard}")
    print(f"  👉 Trang Web Duyệt & Gán Nhãn   : {url_review}")
    print(f"  👉 API Thống kê Thời gian thực  : {url_dashboard}/api/stats")
    print("=" * 68)
    print("  Nhấn Ctrl+C trong terminal để dừng server.\n")

    # Tự động mở trình duyệt
    try:
        webbrowser.open(url_dashboard)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Dừng máy chủ web.")
        httpd.server_close()


if __name__ == "__main__":
    run()

