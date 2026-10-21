"""Điều tiết tốc độ (phần 4): jitter, nghỉ dài ngẫu nhiên, backoff theo bậc."""
import random
import time

class Throttle:
    def __init__(self, cfg, sleep=time.sleep, rng=None):
        self.delays = cfg["delays"]
        self.long = cfg["long_pause"]
        self.mult = 1.0
        self.sleep = sleep
        self.rng = rng or random.Random()
        self.last_action = "start"

    def delay_for(self, kind):
        lo, hi = self.delays[kind]
        d = self.rng.uniform(lo, hi) * self.mult
        if self.rng.random() < self.long["probability"]:
            d += self.rng.uniform(*self.long["range"])
        return d

    def wait(self, kind):
        self.last_action = kind
        d = self.delay_for(kind)
        self.sleep(d)
        return d

    def escalate(self):
        """Bậc 1: dấu hiệu nhẹ -> gấp đôi mọi khoảng chờ trong phiên."""
        self.mult = min(self.mult * 2, 8)
