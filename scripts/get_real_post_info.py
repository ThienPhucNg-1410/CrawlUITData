import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True)
try:
    url = 'https://www.facebook.com/groups/congdongsinhvien.hcmuit/posts/1139252691970792/'
    driver.get(url)
    time.sleep(5)

    js = """
    // Trong trang permalink, bài chính là bài nằm trong vùng có liên kết chứa đúng post_id
    // hoặc nằm ngay trước các nút 'Thích', 'Bình luận' chính của bài!
    // Hoặc trích xuất từ document.title:
    const title = document.title;
    
    // Tìm post text nằm ngay trong container chính
    // Tìm nút Phù hợp nhất hoặc khu vực bình luận
    const commentHeader = Array.from(document.querySelectorAll('div, span'))
        .find(e => e.innerText && (e.innerText.trim() === 'Phù hợp nhất' || e.innerText.trim() === 'Tất cả bình luận' || e.innerText.trim() === 'Most relevant'));

    let container = commentHeader ? commentHeader.closest('div[role="dialog"]') || commentHeader.closest('div[role="main"]') || commentHeader.parentElement.parentElement.parentElement.parentElement : null;

    // Tìm author trong container
    let author = '';
    let post_text = '';

    if (container) {
        const uLink = container.querySelector('a[href*="/user/"], h2 a, h3 a, strong a');
        if (uLink) author = uLink.innerText.trim();
        
        // Post text là div[dir="auto"] nằm TRÊN khu vực bình luận trong container
        const dirs = Array.from(container.querySelectorAll('div[dir="auto"]'))
            .filter(d => !d.closest('div[role="article"]') && d.innerText.trim().length > 0);
        if (dirs.length > 0) {
            post_text = dirs[0].innerText.trim();
        }
    }

    return {
        title: title,
        containerFound: !!container,
        author: author,
        post_text: post_text
    };
    """
    res = driver.execute_script(js)
    print("Result:", res)
finally:
    driver.quit()

