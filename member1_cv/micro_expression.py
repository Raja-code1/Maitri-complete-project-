"""
Member 1: Micro-Expression & Facial Tension Analyzer
Detects fleeting micro-expressions, brow furrows, jaw clenching, and localized muscular tension.
"""

from collections import deque
from typing import Dict, List, Optional
import numpy as np

from config.schemas import VisualMicroExpression


class MicroExpressionAnalyzer:
    """
    Analyzes temporal micro-movements, brow furrows, and facial strain dynamics.
    """

    def __init__(self, history_len: int = 45):
        self.history_len = history_len
        self.brow_history: deque = deque(maxlen=history_len)
        self.jaw_history: deque = deque(maxlen=history_len)
        self.tension_history: deque = deque(maxlen=history_len)

    def analyze_facial_tension(
        self,
        brow_distance_ratio: float = 0.5,
        lip_compression_ratio: float = 0.2,
        symmetry_diff: float = 0.05,
    ) -> VisualMicroExpression:
        """
        Analyze facial tension indices.
        - brow_distance_ratio: Lower values indicate eyebrow furrowing (corrugator supercilii muscle contraction).
        - lip_compression_ratio: Lower values indicate thin, pressed lips / jaw tension.
        - symmetry_diff: Asymmetry in left vs right hemifacial movement.
        """
        # Brow furrow score: inverted scale where lower distance -> higher furrow
        brow_furrow = float(np.clip(1.0 - (brow_distance_ratio / 0.5), 0.0, 1.0))
        
        # Jaw clench score: lower lip height / compressed mouth -> higher tension
        jaw_clench = float(np.clip(1.0 - (lip_compression_ratio / 0.25), 0.0, 1.0))
        
        # Micro-tremor / dynamic variation
        self.brow_history.append(brow_furrow)
        self.jaw_history.append(jaw_clench)
        
        dynamic_jitter = 0.0
        if len(self.brow_history) >= 5:
            dynamic_jitter = float(np.std(list(self.brow_history)[-10:]) * 1.5)
            
        # Composite tension
        composite_tension = float(
            np.clip(
                0.45 * brow_furrow + 0.35 * jaw_clench + 0.10 * dynamic_jitter + 0.10 * symmetry_diff,
                0.0,
                1.0,
            )
        )
        self.tension_history.append(composite_tension)
        
        return VisualMicroExpression(
            brow_furrow=round(brow_furrow, 3),
            jaw_clench=round(jaw_clench, 3),
            tension_score=round(composite_tension, 3),
            asymmetry_index=round(float(np.clip(symmetry_diff, 0.0, 1.0)), 3),
        )
