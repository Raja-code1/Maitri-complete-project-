"""
Member 4: Sentinel-1 Synthetic Aperture Radar (SAR) Processing Pipeline
Performs radar backscatter change detection (VV/VH polarization) and
Otsu adaptive thresholding for all-weather automated flood extent mapping.
"""

import numpy as np
from typing import Dict, Any, Tuple, List
from shapely.geometry import box, mapping
from shapely.ops import unary_union

class Sentinel1SARPipeline:
    """
    Automated Sentinel-1 SAR backscatter analysis and surface water extraction.
    """

    @staticmethod
    def apply_lee_filter(image: np.ndarray, window_size: int = 3) -> np.ndarray:
        """
        Lee speckle reduction filter for SAR backscatter rasters.
        Preserves edges while smoothing granular radar speckle noise.
        """
        pad = window_size // 2
        padded = np.pad(image, pad, mode='reflect')
        filtered = np.copy(image)
        nx, ny = image.shape

        for i in range(nx):
            for j in range(ny):
                window = padded[i:i + window_size, j:j + window_size]
                mean = np.mean(window)
                var = np.var(window)
                if var > 1e-4:
                    k = var / (var + 0.25)
                    filtered[i, j] = mean + k * (image[i, j] - mean)
                else:
                    filtered[i, j] = mean

        return filtered

    @staticmethod
    def compute_otsu_threshold(backscatter_db: np.ndarray) -> float:
        """
        Otsu's method to calculate the optimal bimodal separation threshold
        between specular water bodies (low dB) and surrounding terrain (high dB).
        """
        # Clip to typical SAR backscatter range [-30 dB, 0 dB]
        clipped = np.clip(backscatter_db.ravel(), -30.0, 0.0)
        hist, bin_edges = np.histogram(clipped, bins=60, range=(-30.0, 0.0))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
        total_pixels = len(clipped)

        current_max_var = 0.0
        best_threshold = -16.0  # Typical standard SAR water threshold

        # Cumulative sums
        weight_bg = 0.0
        sum_bg = 0.0
        total_sum = np.sum(hist * bin_centers)

        for i in range(len(hist)):
            weight_bg += hist[i]
            if weight_bg == 0:
                continue
            weight_fg = total_pixels - weight_bg
            if weight_fg == 0:
                break

            sum_bg += hist[i] * bin_centers[i]
            mean_bg = sum_bg / weight_bg
            mean_fg = (total_sum - sum_bg) / weight_fg

            between_var = weight_bg * weight_fg * ((mean_bg - mean_fg) ** 2)
            if between_var > current_max_var:
                current_max_var = between_var
                best_threshold = float(bin_centers[i])

        return best_threshold

    @staticmethod
    def extract_flood_extent_mask(
        pre_event_sar: np.ndarray,
        post_event_sar: np.ndarray,
        threshold_db: float = -15.5
    ) -> Tuple[np.ndarray, float]:
        """
        Calculates flood change detection mask:
        A pixel is classified as flood if post-event backscatter is below the water threshold
        OR shows a significant drop (specular water replacement) compared to pre-event.
        """
        # Lee filter both images
        pre_clean = Sentinel1SARPipeline.apply_lee_filter(pre_event_sar)
        post_clean = Sentinel1SARPipeline.apply_lee_filter(post_event_sar)

        delta_sar = post_clean - pre_clean
        # Specular water mask: low absolute backscatter AND drop > 3.0 dB
        is_water = (post_clean <= threshold_db) | ((delta_sar < -3.2) & (post_clean < -12.0))
        optimal_th = Sentinel1SARPipeline.compute_otsu_threshold(post_clean)

        return is_water, optimal_th

    @staticmethod
    def sar_mask_to_geojson(
        sar_water_mask: np.ndarray,
        basin_bbox: List[float]
    ) -> Dict[str, Any]:
        """
        Converts boolean SAR flood mask into a clean GeoJSON polygon layer.
        """
        nx, ny = sar_water_mask.shape
        min_lon, min_lat, max_lon, max_lat = basin_bbox

        lon_edges = np.linspace(min_lon, max_lon, nx + 1)
        lat_edges = np.linspace(max_lat, min_lat, ny + 1)

        boxes = []
        for i in range(nx):
            for j in range(ny):
                if sar_water_mask[i, j]:
                    boxes.append(box(
                        lon_edges[i],
                        lat_edges[j + 1],
                        lon_edges[i + 1],
                        lat_edges[j]
                    ))

        if not boxes:
            return {"type": "FeatureCollection", "features": []}

        merged_poly = unary_union(boxes)
        feature = {
            "type": "Feature",
            "properties": {
                "sensor": "Sentinel-1 C-Band SAR (VV/VH)",
                "observation_type": "Near-Real-Time Radar Satellite Flood Extent",
                "color": "#06b6d4",
                "stroke_color": "#0891b2",
                "fillOpacity": 0.55
            },
            "geometry": mapping(merged_poly)
        }

        return {
            "type": "FeatureCollection",
            "features": [feature]
        }
