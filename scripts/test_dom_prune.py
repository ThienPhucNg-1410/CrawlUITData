import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, 'src')
import uitconf.config as C
from uitconf.scraper.driver import make_driver

cfg = C.load()
driver = make_driver(cfg, headless=True, enable_images=False)
try:
    url = cfg['page_url']
    driver.get(url)
    time.sleep(5)
    
    print("Initial title:", driver.title)
    
    for i in range(15):
        driver.execute_script("window.scrollBy(0, 3000);")
        time.sleep(1.2)
        
        # Test pruning
        prune_js = """
        const arts = Array.from(document.querySelectorAll('div[role="article"]'));
        let pruned = 0;
        if (arts.length > 30) {
            for (let j = 0; j < arts.length - 20; j++) {
                arts[j].remove();
                pruned++;
            }
        }
        return { total: arts.length, pruned: pruned };
        """
        res = driver.execute_script(prune_js)
        print(f"Scroll {i+1}: Total arts before prune = {res['total']}, pruned = {res['pruned']}")
        
    # Check if feed still loads after pruning
    driver.execute_script("window.scrollBy(0, 3000);")
    time.sleep(2)
    after_count = driver.execute_script("return document.querySelectorAll('div[role=\"article\"]').length;")
    print("After further scroll, articles count:", after_count)
finally:
    driver.quit()

