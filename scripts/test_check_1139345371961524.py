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
o.add_argument("--blink-settings=imagesEnabled=false")
profile = Path("d:/uit-confession-sentiment/.temp_test_profile")
o.add_argument(f"--user-data-dir={profile}")
driver = webdriver.Chrome(options=o)

try:
    url = "https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139345371961524/"
    driver.get(url)
    time.sleep(3.5)
    
    js = """
    const res = {};
    res.title = document.title;
    
    // Look at main post article
    const articles = Array.from(document.querySelectorAll('div[role="article"]'));
    res.totalArticles = articles.length;
    
    const postArticle = articles.find(a => {
        const aria = (a.getAttribute('aria-label') || '').toLowerCase();
        return !aria.includes('bình luận') && !aria.includes('comment') && !aria.includes('trả lời');
    }) || articles[0];
    
    if (postArticle) {
        res.postArticleAria = postArticle.getAttribute('aria-label');
        res.postArticleText = postArticle.innerText.slice(0, 1500);
        const msgNode = postArticle.querySelector('div[data-ad-preview="message"], div[data-ad-comet-preview="message"]');
        res.msgText = msgNode ? msgNode.innerText : '';
        const h2 = postArticle.querySelector('h2');
        res.h2Text = h2 ? h2.innerText : '';
    }
    return res;
    """
    data = driver.execute_script(js)
    print("Title:", data.get("title"))
    print("Total articles:", data.get("totalArticles"))
    print("Post Article Aria:", data.get("postArticleAria"))
    print("H2 Text:", data.get("h2Text"))
    print("Msg Text:", repr(data.get("msgText")))
    print("Post Article Text Snippet:\n", data.get("postArticleText", "")[:600])
finally:
    driver.quit()

