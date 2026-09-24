"""
Member 5: Tile Cache & Spatial Indexing Manager
Manages spatial chunking, caching, and GeoJSON streaming for large volume hydrodynamics.
"""

from typing import Dict, Any, List, Optional
import time

class TileCacheManager:
    """
    In-memory spatial index and cache for rapid layer streaming.
    """

    def __init__(self, max_cached_runs: int = 15):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self.max_cached_runs = max_cached_runs

    def store_run(self, task_id: str, results: Dict[str, Any]) -> None:
        """
        Caches run results and evicts oldest entries if exceeding budget.
        """
        if len(self._cache) >= self.max_cached_runs:
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            self._cache.pop(oldest_key, None)
            self._timestamps.pop(oldest_key, None)

        self._cache[task_id] = results
        self._timestamps[task_id] = time.time()

    def get_run(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached run by task_id.
        """
        return self._cache.get(task_id)

    def get_layer(self, task_id: str, layer_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves specific GeoJSON layer (e.g., 'delft3d_contours', 'sph_envelope', 'gee_satellite').
        """
        run_data = self.get_run(task_id)
        if not run_data:
            return None
        return run_data.get("layers", {}).get(layer_name)
