import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

import uitconf.config as C
from uitconf.scraper.driver import make_driver
from uitconf.scraper.parse import parse_time, post_id_from_href

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)

try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/search/?q=k19"
    print(f"Loading URL: {url}")
    driver.get(url)
    time.sleep(5)
    print("Page title:", driver.title)
    
    # 1. Inspect filters available on search page
    filter_inspect_js = """
    const elements = Array.from(document.querySelectorAll('div[role="button"], span, div[role="radio"], div[role="checkbox"], a'));
    const matches = elements
        .map(e => (e.innerText || '').trim())
        .filter(t => t.length > 0 && (
            t.includes('Ngày đăng') || t.includes('Năm') || t.includes('Mới đây nhất') ||
            t.includes('Phù hợp nhất') || t.includes('Date') || t.includes('Recent') ||
            t.includes('Bài viết') || t.includes('Posts') || t.includes('2026')
        ));
    return Array.from(new Set(matches)).slice(0, 30);
    """
    filters_found = driver.execute_script(filter_inspect_js)
    print("\n--- FILTERS FOUND ---")
    for f in filters_found:
        print(" -", f)

    # 2. Inspect articles in search feed
    articles_inspect_js = """
    const articles = Array.from(document.querySelectorAll('div[role="feed"] > div, div[role="article"]'));
    return articles.map(art => {
        const text = art.innerText || '';
        if (text.length < 20) return null;
        
        // Find any link inside the article
        const links = Array.from(art.querySelectorAll('a[href]')).map(a => a.href);
        
        // Find timestamp text
        const spans = Array.from(art.querySelectorAll('span, a')).map(s => (s.innerText || '').trim());
        const timeMatch = spans.find(t => t.match(/^\\d+\\s*(tháng|thg|ngày|giờ|phút|d|h|m|w|y)/i) || t.match(/^\\d+\\s*thg\\s*\\d+/i) || t.includes('trước'));
        
        return {
            text_snippet: text.slice(0, 100).replace(/\\n/g, ' '),
            time_str: timeMatch || 'N/A',
            links: links.slice(0, 5)
        };
    }).filter(Boolean).slice(0, 10);
    """
    articles = driver.execute_script(articles_inspect_js)
    print(f"\n--- ARTICLES FOUND ({len(articles)}) ---")
    for a in articles:
        print(f"Time: {a['time_str']}")
        print(f"Snippet: {a['text_snippet']}")
        print(f"Links: {a['links']}")
        print("-" * 50)

finally:
    driver.quit()
