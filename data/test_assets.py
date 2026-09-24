"""
Data & Test Assets Generator
Generates synthetic audio waveforms and video test frames for offline testing.
"""

import numpy as np
import cv2
from typing import Tuple


def generate_synthetic_audio(
    duration_sec: float = 3.0,
    sample_rate: int = 16000,
    f0_hz: float = 140.0,
    jitter_amount: float = 0.01,
    noise_level: float = 0.02,
) -> np.ndarray:
    """
    Generate synthetic voiced audio waveform with controlled pitch, harmonic structure, and jitter.
    """
    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False)
    
    # Phase accumulator with jitter
    phase = 0.0
    signal = np.zeros(total_samples)
    
    for i in range(total_samples):
        # Apply jitter frequency perturbation
        instant_f0 = f0_hz * (1.0 + np.random.normal(0, jitter_amount))
        phase += 2.0 * np.pi * instant_f0 / sample_rate
        # Voice harmonics (F0, 2*F0, 3*F0)
        signal[i] = (
            0.6 * np.sin(phase)
            + 0.25 * np.sin(2.0 * phase)
            + 0.15 * np.sin(3.0 * phase)
        )
        
    # Add ambient spacecraft cabin white noise
    noise = np.random.normal(0, noise_level, total_samples)
    signal = signal + noise
    
    # Normalize to 16-bit range
    signal = signal / (np.max(np.abs(signal)) + 1e-6)
    return (signal * 32767).astype(np.int16)


def generate_synthetic_face_frame(
    width: int = 320,
    height: int = 240,
    eye_open: bool = True,
    smiling: bool = False,
    tense_brow: bool = False,
) -> np.ndarray:
    """
    Generate synthetic face frame for computer vision testing.
    """
    # Neutral space cabin background
    frame = np.full((height, width, 3), 45, dtype=np.uint8)
    
    # Draw face oval
    center_x, center_y = width // 2, height // 2
    cv2.ellipse(frame, (center_x, center_y), (60, 80), 0, 0, 360, (180, 190, 200), -1)
    
    # Draw eyes
    eye_y = center_y - 20
    left_eye_x = center_x - 25
    right_eye_x = center_x + 25
    
    if eye_open:
        cv2.circle(frame, (left_eye_x, eye_y), 8, (255, 255, 255), -1)
        cv2.circle(frame, (left_eye_x, eye_y), 4, (40, 40, 40), -1)
        cv2.circle(frame, (right_eye_x, eye_y), 8, (255, 255, 255), -1)
        cv2.circle(frame, (right_eye_x, eye_y), 4, (40, 40, 40), -1)
    else:
        # Closed eyelids (slits)
        cv2.line(frame, (left_eye_x - 8, eye_y), (left_eye_x + 8, eye_y), (50, 50, 50), 2)
        cv2.line(frame, (right_eye_x - 8, eye_y), (right_eye_x + 8, eye_y), (50, 50, 50), 2)
        
    # Draw eyebrows
    brow_y = eye_y - 12
    if tense_brow:
        # Slanted downward toward center (furrowed)
        cv2.line(frame, (left_eye_x - 10, brow_y - 2), (left_eye_x + 10, brow_y + 4), (30, 30, 30), 3)
        cv2.line(frame, (right_eye_x - 10, brow_y + 4), (right_eye_x + 10, brow_y - 2), (30, 30, 30), 3)
    else:
        cv2.line(frame, (left_eye_x - 10, brow_y), (left_eye_x + 10, brow_y), (30, 30, 30), 2)
        cv2.line(frame, (right_eye_x - 10, brow_y), (right_eye_x + 10, brow_y), (30, 30, 30), 2)
        
    # Draw mouth
    mouth_y = center_y + 35
    if smiling:
        cv2.ellipse(frame, (center_x, mouth_y - 5), (20, 12), 0, 0, 180, (50, 50, 200), 2)
    else:
        cv2.line(frame, (center_x - 15, mouth_y), (center_x + 15, mouth_y), (50, 50, 200), 2)
        
    return frame
