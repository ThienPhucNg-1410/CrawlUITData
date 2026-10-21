import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

o = Options()
o.add_argument("--headless=new")
o.add_argument("--disable-gpu")
profile = Path("d:/uit-confession-sentiment/.temp_test_profile")
o.add_argument(f"--user-data-dir={profile}")
driver = webdriver.Chrome(options=o)

try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139837221912339/"
    driver.get(url)
    time.sleep(3)
    info = driver.execute_script("""
        const link = document.querySelector('a[href*="1139915275237867"]');
        if (!link) return { found: false };
        const art = link.closest('div[role="article"]');
        if (!art) return { found: true, no_art: true };
        return {
            found: true,
            html: art.outerHTML.slice(0, 500),
            innerText: art.innerText,
            imgs: Array.from(art.querySelectorAll('img')).map(i => ({ src: i.src, alt: i.alt, aria: i.getAttribute('aria-label') }))
        };
    """)
    print("Found:", info.get("found"))
    print("Text:", repr(info.get("innerText")))
    print("Imgs:", info.get("imgs"))
finally:
    driver.quit()

