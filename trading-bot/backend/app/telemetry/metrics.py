import time
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    def __init__(self):
        self.latency_stats: Dict[str, List[float]] = {}

    def record_latency(self, component: str, duration_ms: float):
        if component not in self.latency_stats:
            self.latency_stats[component] = []
        self.latency_stats[component].append(duration_ms)
        if len(self.latency_stats[component]) > 100:
            self.latency_stats[component].pop(0)

    def get_summary(self) -> Dict:
        summary = {}
        for comp, values in self.latency_stats.items():
            if values:
                summary[comp] = {
                    "avg": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "last": values[-1]
                }
        return summary

metrics = MetricsCollector()
