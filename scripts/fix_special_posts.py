import sys
import os
import time
import sqlite3
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))
sys.path.insert(0, str(BASE_DIR))

import uitconf.config as C
from uitconf.scraper.driver import make_driver
from scripts.fix_all_posts import EXTRACT_JS, export_dataset

cfg = C.load()
driver = make_driver(cfg, headless=True)
conn = sqlite3.connect(BASE_DIR / "data" / "raw" / "raw.sqlite")
c = conn.cursor()

pids = ['1139252691970792', '1111408351421893', '1111363704759691']

try:
    for pid in pids:
        url = f"https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/{pid}/"
        driver.get(url)
        time.sleep(2.5)
        res = driver.execute_script(EXTRACT_JS)
        
        author = res.get('author') or 'Người tham gia ẩn danh'
        text = res.get('text') or ''
        
        print(f"PID {pid}:")
        print(f"  Author: {author}")
        print(f"  Text  : {text[:100]}")
        
        if text:
            c.execute("UPDATE posts SET text = ?, author = ? WHERE post_id = ?", (text, author, pid))
            conn.commit()
            print(f"  --> Updated in DB!")
            
finally:
    driver.quit()
    conn.close()

export_dataset()
print("All done and re-exported!")
