import random, sys
sys.path.insert(0, "src")
from uitconf.anonymize import anonymize
from uitconf.preprocess import normalize, is_valid, load_teencode
from uitconf.scraper.timer import Throttle
from uitconf.scraper.parse import post_id_from_href, bucket_of, round_of, parse_count, parse_time
from uitconf.analysis import bootstrap_ci
from uitconf.config import load

def test_anonymize_pii():
    t = anonymize("Liên hệ 0912 345 678 hoặc a.b@gm.com, MSSV 21520001, xem https://fb.com/xyz, thầy Nguyễn Văn An dạy dở")
    for leak in ("0912", "a.b@gm.com", "21520001", "fb.com", "Nguyễn"):
        assert leak not in t
    assert "[SDT]" in t and "[EMAIL]" in t and "[MSSV]" in t and "[URL]" in t and "thầy [GV]" in t

def test_normalize():
    teen = load_teencode("data/teencode.csv")
    n = normalize("Hp năm nay đắt quááááá 😡", teen)
    assert "học phí" in n and "<nhan_manh>" in n and "quá" in n and "quáááá" not in n

def test_is_valid():
    assert not is_valid("ok [URL]") and is_valid("học phí tăng quá nhiều")

def test_throttle_bounds_and_backoff():
    cfg = load("configs/config.yaml")
    waits = []
    th = Throttle(cfg, sleep=waits.append, rng=random.Random(1))
    th.rng.random = lambda: 0.99          # tắt nghỉ dài
    d1 = th.wait("scroll"); assert 4 <= d1 <= 10
    th.escalate(); d2 = th.wait("scroll"); assert 8 <= d2 <= 20

def test_parse():
    assert post_id_from_href("https://facebook.com/x/posts/pfbid02AbC?x=1") == "pfbid02AbC"
    assert post_id_from_href("https://facebook.com/x/posts/12345") == "12345"
    b = bucket_of("pfbid02AbC"); assert 0 <= b < 100 and b == bucket_of("pfbid02AbC")
    assert round_of(10, {1: [0, 30], 2: [30, 65], 3: [65, 100]}) == 1
    assert parse_count("1,2K") == 1200 and parse_count("35") == 35
    t_iso = parse_time("2024-05-15")
    assert t_iso is not None and "2024-05-15" in t_iso

def test_bootstrap():
    m, lo, hi = bootstrap_ci([1] * 30 + [0] * 70)
    assert lo <= m <= hi and abs(m - 0.3) < 1e-9
