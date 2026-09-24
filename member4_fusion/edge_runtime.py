"""
Member 4: Edge Runtime Manager
Manages offline edge execution, ring buffers, memory footprint, and low-latency scheduling.
"""

import time
from collections import deque
from typing import Dict, List, Optional
import numpy as np

from config.schemas import MultimodalFusionContext


class EdgeRuntime:
    """
    High-performance Edge runtime controller for standalone space station operation.
    """

    def __init__(self, buffer_size: int = 500):
        self.buffer_size = buffer_size
        self.context_buffer: deque = deque(maxlen=buffer_size)
        self.latencies: deque = deque(maxlen=100)
        self.start_time: float = time.time()
        self.total_cycles: int = 0

    def record_cycle(self, context: MultimodalFusionContext, execution_time_ms: float):
        """
        Record edge telemetry cycle and track runtime performance.
        """
        self.total_cycles += 1
        self.context_buffer.append(context)
        self.latencies.append(execution_time_ms)

    def get_runtime_health(self) -> Dict:
        """
        Get edge device performance metrics.
        """
        uptime_sec = time.time() - self.start_time
        avg_latency = float(np.mean(self.latencies)) if self.latencies else 0.0
        p99_latency = float(np.percentile(self.latencies, 99)) if self.latencies else 0.0
        
        return {
            "edge_status": "OFFLINE_STANDALONE_OPERATIONAL",
            "uptime_seconds": round(uptime_sec, 1),
            "total_cycles_processed": self.total_cycles,
            "avg_latency_ms": round(avg_latency, 2),
            "p99_latency_ms": round(p99_latency, 2),
            "memory_buffer_usage": f"{len(self.context_buffer)}/{self.buffer_size} frames",
            "offline_mode_verified": True,
        }

    def get_latest_context(self) -> Optional[MultimodalFusionContext]:
        return self.context_buffer[-1] if self.context_buffer else None

    def get_telemetry_history(self, count: int = 50) -> List[Dict]:
        items = list(self.context_buffer)[-count:]
        return [
            {
                "timestamp": c.timestamp,
                "awbi": c.awbi_score,
                "stress": c.stress_index,
                "fatigue": c.fatigue_index,
                "cognitive_load": c.cognitive_load_index,
                "balance": c.psychological_balance,
            }
            for c in items
        ]
