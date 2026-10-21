import json
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=False, enable_images=False)
driver.get("https://www.facebook.com/groups/congdongsinhvien.hcmuit/?sorting_setting=CHRONOLOGICAL")

import time
time.sleep(6)

# Inspect div[role="feed"] and all /posts/ links on the page
js = """
let feed = document.querySelector('div[role="feed"]');
let allPostLinks = Array.from(document.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]')).map(a => ({
    text: a.innerText.trim(),
    href: a.href,
    parentTag: a.parentElement ? a.parentElement.tagName : '',
    hasArticleAncestor: !!a.closest('div[role="article"]')
}));

return {
    hasFeed: !!feed,
    feedChildrenCount: feed ? feed.children.length : 0,
    feedChildrenRoles: feed ? Array.from(feed.children).map(c => c.getAttribute('role')) : [],
    postLinks: allPostLinks.slice(0, 10)
};
"""
data = driver.execute_script(js)
with open("logs/dom_debug.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved detailed feed debug info to logs/dom_debug.json")

driver.quit()
