import sys
import pytest
from unittest.mock import MagicMock
sys.path.insert(0, "src")

# Mock selenium modules if not installed in current environment
if "selenium" not in sys.modules:
    try:
        import selenium
    except ImportError:
        from unittest.mock import MagicMock
        sel_mock = MagicMock()
        class FakeNoSuchElementException(Exception): pass
        class FakeStaleElementReferenceException(Exception): pass
        sel_mock.common.exceptions.NoSuchElementException = FakeNoSuchElementException
        sel_mock.common.exceptions.StaleElementReferenceException = FakeStaleElementReferenceException
        sel_mock.webdriver.common.by.By.CSS_SELECTOR = "css selector"
        sel_mock.webdriver.common.by.By.XPATH = "xpath"
        sys.modules["selenium"] = sel_mock
        sys.modules["selenium.common"] = sel_mock.common
        sys.modules["selenium.common.exceptions"] = sel_mock.common.exceptions
        sys.modules["selenium.webdriver"] = sel_mock.webdriver
        sys.modules["selenium.webdriver.common"] = sel_mock.webdriver.common
        sys.modules["selenium.webdriver.common.by"] = sel_mock.webdriver.common.by
        sys.modules["selenium.webdriver.chrome"] = sel_mock.webdriver.chrome
        sys.modules["selenium.webdriver.chrome.options"] = sel_mock.webdriver.chrome.options

from uitconf.db import connect
from uitconf.scraper import crawler
from uitconf.scraper.guard import HardStop
from uitconf.scraper.timer import Throttle
import uitconf.config as C


def test_select_posts_for_comments(tmp_path):
    conn = connect(str(tmp_path / "test.sqlite"))
    cfg = C.load("configs/config.yaml")

    # Tạo các post với điều kiện khác nhau
    # 1: relevant, reactions >= 10, round 1 -> chọn
    conn.execute(
        "INSERT INTO posts(post_id, permalink, text, reactions, n_comments, round, status) VALUES(?,?,?,?,?,?,?)",
        ("p1", "http://fb.com/p1", "UIT học phí năm nay", 15, 2, 1, "post_only")
    )
    # 2: not relevant, reactions 20 -> bị loại do f['only_relevant']
    conn.execute(
        "INSERT INTO posts(post_id, permalink, text, reactions, n_comments, round, status) VALUES(?,?,?,?,?,?,?)",
        ("p2", "http://fb.com/p2", "Hôm nay trời đẹp", 20, 10, 1, "post_only")
    )
    # 3: relevant, reactions < 10 và n_comments < 3 -> bị loại do tương tác thấp
    conn.execute(
        "INSERT INTO posts(post_id, permalink, text, reactions, n_comments, round, status) VALUES(?,?,?,?,?,?,?)",
        ("p3", "http://fb.com/p3", "Ký túc xá UIT", 5, 1, 1, "post_only")
    )
    # 4: relevant, reactions is None (chưa biết số liệu) -> vẫn giữ
    conn.execute(
        "INSERT INTO posts(post_id, permalink, text, reactions, n_comments, round, status) VALUES(?,?,?,?,?,?,?)",
        ("p4", "http://fb.com/p4", "Thầy cô UIT tuyệt vời", None, None, 1, "post_only")
    )
    # 5: round 2 trong khi chỉ query round 1 -> bị lọc ở SQL
    conn.execute(
        "INSERT INTO posts(post_id, permalink, text, reactions, n_comments, round, status) VALUES(?,?,?,?,?,?,?)",
        ("p5", "http://fb.com/p5", "UIT phòng đào tạo", 50, 20, 2, "post_only")
    )
    conn.commit()

    rel_fn = lambda text: "uit" in text.lower()
    selected = crawler.select_posts_for_comments(conn, cfg, rnd=1, limit=10, relevant_fn=rel_fn)

    pids = [r["post_id"] for r in selected]
    assert "p1" in pids
    assert "p4" in pids
    assert "p2" not in pids
    assert "p3" not in pids
    assert "p5" not in pids


def test_health_check_logic():
    cfg = {
        "selectors": {"article": "div.art", "permalink": "a.link", "text_nodes": "div.txt", "see_more_xpath": ""},
        "health_check": [
            {"url": "https://facebook.com/test", "expect_min_text_len": 10, "expect_has_time": False}
        ]
    }

    # Case 1: Driver tìm thấy article hợp lệ
    mock_driver = MagicMock()
    mock_driver.current_url = "https://facebook.com/test"
    mock_driver.page_source = "<html></html>"

    mock_art = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.return_value = "https://facebook.com/posts/12345"
    mock_link.text = "10 phút trước"
    mock_txt = MagicMock()
    mock_txt.text = "Bài viết mẫu dài hơn 10 ký tự hợp lệ"
    mock_txt.find_elements.return_value = []

    def find_art_elements(by, sel):
        if sel == "a.link":
            return [mock_link]
        elif sel == "div.txt":
            return [mock_txt]
        return []

    mock_art.find_elements = MagicMock(side_effect=find_art_elements)
    mock_driver.find_elements = MagicMock(return_value=[mock_art])

    import time
    orig_sleep = time.sleep
    time.sleep = lambda s: None
    try:
        ok, msg = crawler.health_check(mock_driver, cfg)
        assert ok is True, f"Failed with: {msg}"
        assert msg == "ok"
    finally:
        time.sleep = orig_sleep

    # Case 2: Driver không tìm thấy article
    mock_driver.find_elements.return_value = []
    ok, msg = crawler.health_check(mock_driver, cfg)
    assert ok is False
    assert "không thấy article" in msg


def test_discover_mock(tmp_path):
    conn = connect(str(tmp_path / "raw.sqlite"))
    cfg = C.load("configs/config.yaml")
    cfg["start_date"] = "2024-01-01"
    cfg["end_date"] = "2026-12-31"
    cfg["session"]["max_minutes"] = 1
    throttle = Throttle(cfg, sleep=lambda x: None)

    mock_driver = MagicMock()
    mock_driver.current_url = "https://facebook.com/page"
    mock_driver.page_source = "<html></html>"

    mock_art = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.side_effect = lambda attr: "https://facebook.com/posts/pfbid999" if attr == "href" else "2024-05-01"
    mock_link.text = ""

    mock_txt = MagicMock()
    mock_txt.text = "Bài đăng thử nghiệm mock discover uit"
    mock_txt.find_elements.return_value = []

    def art_find(by, sel):
        if "permalink" in sel or "posts" in sel:
            return [mock_link]
        if "text_nodes" in sel or "dir" in sel:
            return [mock_txt]
        return []

    mock_art.find_elements = art_find
    mock_driver.find_elements.return_value = [mock_art]

    n = crawler.discover(mock_driver, conn, cfg, throttle, max_posts=1)
    assert n == 1
    post = conn.execute("SELECT * FROM posts WHERE post_id='pfbid999'").fetchone()
    assert post is not None
    assert "Bài đăng thử nghiệm" in post["text"]


def test_discover_skips_posts_after_end_date(tmp_path, monkeypatch):
    conn = connect(str(tmp_path / "raw.sqlite"))
    cfg = C.load("configs/config.yaml")
    cfg["end_date"] = "2024-04-30"
    cfg["session"]["max_minutes"] = 1
    throttle = Throttle(cfg, sleep=lambda x: None)

    mock_driver = MagicMock()
    mock_driver.page_source = "<html></html>"
    mock_art = MagicMock()
    mock_link = MagicMock()
    mock_link.get_attribute.side_effect = lambda attr: "https://facebook.com/posts/pfbid1000" if attr == "href" else "2024-05-01"
    mock_link.text = ""
    mock_text = MagicMock()
    mock_text.text = "A post after the collection window"
    mock_text.find_elements.return_value = []
    mock_art.find_elements.side_effect = lambda by, sel: [mock_link] if "posts" in sel else [mock_text]
    mock_driver.find_elements.return_value = [mock_art]

    clock = [0]
    mock_driver.execute_script.side_effect = lambda *_: clock.__setitem__(0, 2)
    monkeypatch.setattr(crawler.time, "time", lambda: clock[0])
    n = crawler.discover(mock_driver, conn, cfg, throttle, max_posts=1)

    assert n == 0
    assert conn.execute("SELECT 1 FROM posts WHERE post_id='pfbid1000'").fetchone() is None
