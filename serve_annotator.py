import http.server
import socketserver
import json
import urllib.parse
import os
import pandas as pd
import webbrowser

PORT = 8085
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "data", "labeled", "review_viewer.html")
CSV_FILE = os.path.join(BASE_DIR, "data", "labeled", "review_labeled.csv")
GOLD_FILE = os.path.join(BASE_DIR, "data", "labeled", "gold.csv")
XLSX_FILE = os.path.join(BASE_DIR, "data", "labeled", "danh_sach_kiem_tra_nhan.xlsx")

import re

def update_html_file(html_path, uid, new_lbl):
    if not os.path.exists(html_path):
        return
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        def repl_tr(m):
            tr_tag = m.group(1)
            tr_tag = re.sub(r'data-label="[^"]+"', f'data-label="{new_lbl}"', tr_tag)
            inner = m.group(2)
            inner = re.sub(r'class="label-select [^"]+"', f'class="label-select {new_lbl}"', inner)
            inner = re.sub(r'<option value="([^"]+)"\s*selected>', r'<option value="\1">', inner)
            inner = re.sub(f'<option value="{new_lbl}">', f'<option value="{new_lbl}" selected>', inner)
            return tr_tag + inner + '</tr>'
        
        pattern = re.compile(rf'(<tr[^>]+data-uid="{uid}"[^>]*>)(.*?)</tr>', re.DOTALL)
        updated = pattern.sub(repl_tr, html_text)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated)
    except Exception as e:
        print(f"[!] Error updating HTML: {e}")

class AnnotationHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path == "/" or url_parts.path == "/index.html":
            if os.path.exists(HTML_FILE):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(HTML_FILE, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "HTML file not found")
        else:
            super().do_GET()

    def do_POST(self):
        url_parts = urllib.parse.urlparse(self.path)
        if url_parts.path == "/api/update_label":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode('utf-8'))
                unit_id = str(payload.get('unit_id')).strip()
                new_label = str(payload.get('label')).strip()
                new_note = str(payload.get('note', '')).strip()

                valid_labels = ['trung_tinh', 'hoi_dap', 'khong_lien_quan', 'tieu_cuc', 'tich_cuc']
                if new_label not in valid_labels:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Invalid label: {new_label}"}).encode('utf-8'))
                    return

                # 1. Update review_labeled.csv
                if os.path.exists(CSV_FILE):
                    df = pd.read_csv(CSV_FILE, dtype={'unit_id': str})
                    mask = df['unit_id'] == unit_id
                    if mask.any():
                        df.loc[mask, 'label'] = new_label
                        if new_note:
                            df.loc[mask, 'note'] = new_note
                        df.to_csv(CSV_FILE, index=False)

                # 2. Update gold.csv if exists
                if os.path.exists(GOLD_FILE):
                    df_gold = pd.read_csv(GOLD_FILE, dtype={'unit_id': str})
                    mask_gold = df_gold['unit_id'] == unit_id
                    if mask_gold.any():
                        df_gold.loc[mask_gold, 'label'] = new_label
                        df_gold.to_csv(GOLD_FILE, index=False)

                # 3. Đồng bộ trực tiếp vào review_viewer.html để F5 KHÔNG BAO GIỜ BỊ MẤT
                update_html_file(HTML_FILE, unit_id, new_label)

                # Response
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "success",
                    "unit_id": unit_id,
                    "new_label": new_label
                }).encode('utf-8'))
                print(f"[UPDATED] Unit: {unit_id} -> {new_label} (Saved in CSV, Gold, & HTML!)")

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "Unknown endpoint")

def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    with socketserver.TCPServer(("", PORT), AnnotationHandler) as httpd:
        print("=====================================================")
        print(f" SERVER DAN NHAN DANG CHAY TAI: http://localhost:{PORT}")
        print(" Moi thay doi nhan tren Web se luu thang vao CSV!")
        print("=====================================================")
        httpd.serve_forever()

if __name__ == "__main__":
    run()
