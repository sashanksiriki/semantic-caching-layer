"""
Observability. Without this, you cannot actually prove the "cuts costs
30-60%" claim to anyone - you just have vibes. This tracks hit rate and
*measured* latency saved (not a hardcoded guess) in-memory; swap for
Prometheus counters/StatsD in a real deployment.

Latency saved per hit = (running average of real LLM-call latency on
misses) - (this hit's actual latency). That's an honest estimate: "if
this had been a miss, based on what misses have actually cost us
recently, here's roughly what we avoided paying in wait time."
"""
import time


class Metrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.blocked_non_cacheable = 0
        self.total_latency_saved_sec = 0.0
        self._avg_miss_latency_sec = 0.0
        self.started_at = time.time()

    def record_hit(self, actual_latency_sec: float) -> None:
        self.hits += 1
        # Only counts as "saved" once we've actually observed at least
        # one real miss to compare against -- before that we have no
        # basis for a number and shouldn't fabricate one.
        if self._avg_miss_latency_sec > 0:
            saved = max(0.0, self._avg_miss_latency_sec - actual_latency_sec)
            self.total_latency_saved_sec += saved

    def record_miss(self, actual_latency_sec: float) -> None:
        self.misses += 1
        # Running average, weighted toward recent calls so it tracks
        # real provider latency instead of drifting from one early outlier.
        if self._avg_miss_latency_sec == 0.0:
            self._avg_miss_latency_sec = actual_latency_sec
        else:
            self._avg_miss_latency_sec = (
                0.8 * self._avg_miss_latency_sec + 0.2 * actual_latency_sec
            )

    def record_blocked(self) -> None:
        self.blocked_non_cacheable += 1

    def snapshot(self) -> dict:
        total_cacheable = self.hits + self.misses
        hit_rate = self.hits / total_cacheable if total_cacheable else 0.0
        return {
            "uptime_sec": round(time.time() - self.started_at, 1),
            "hits": self.hits,
            "misses": self.misses,
            "blocked_non_cacheable": self.blocked_non_cacheable,
            "hit_rate": round(hit_rate, 3),
            "avg_miss_latency_sec": round(self._avg_miss_latency_sec, 3),
            "measured_latency_saved_sec": round(self.total_latency_saved_sec, 2),
        }


metrics = Metrics()
