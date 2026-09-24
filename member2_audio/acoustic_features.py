"""
Member 2: Acoustic Feature Extractor
Extracts Pitch (F0), Jitter, Shimmer, HNR, MFCCs, Spectral Centroid, and ZCR from audio.
Designed for 100% offline edge processing.
"""

import math
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy.signal import find_peaks

from config.settings import AUDIO_SAMPLE_RATE, PITCH_MIN_HZ, PITCH_MAX_HZ
from config.schemas import AcousticFeatures


class AcousticFeatureExtractor:
    """
    DSP engine for real-time acoustic and prosodic feature extraction.
    """

    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE):
        self.sample_rate = sample_rate

    def extract_f0_pitch(self, audio_data: np.ndarray) -> Tuple[float, float, np.ndarray]:
        """
        Estimate Fundamental Frequency (F0) using autocorrelation and peak detection.
        Returns: (mean_pitch_hz, pitch_variance, pitch_contour)
        """
        if audio_data is None or len(audio_data) < 256:
            return 140.0, 10.0, np.array([140.0])
            
        # Normalize audio signal
        signal = audio_data.astype(np.float64)
        if np.max(np.abs(signal)) > 1e-6:
            signal = signal / np.max(np.abs(signal))
            
        # Frame-by-frame pitch extraction (50ms frames with 50% overlap)
        frame_len = int(0.05 * self.sample_rate)
        hop_len = int(0.025 * self.sample_rate)
        
        min_lag = int(self.sample_rate / PITCH_MAX_HZ)
        max_lag = int(self.sample_rate / PITCH_MIN_HZ)
        
        pitches = []
        for start in range(0, len(signal) - frame_len, hop_len):
            frame = signal[start : start + frame_len]
            # Apply Hanning window
            windowed = frame * np.hanning(len(frame))
            # Autocorrelation
            corr = np.correlate(windowed, windowed, mode="full")
            corr = corr[len(corr) // 2 :]
            
            # Find candidate peak in valid pitch lag range
            if max_lag < len(corr):
                search_region = corr[min_lag:max_lag]
                if len(search_region) > 0 and np.max(search_region) > 0.25 * corr[0]:
                    peak_idx = np.argmax(search_region) + min_lag
                    f0 = self.sample_rate / float(peak_idx)
                    pitches.append(f0)
                    
        if len(pitches) == 0:
            return 140.0, 12.0, np.array([140.0])
            
        pitch_arr = np.array(pitches)
        mean_pitch = float(np.mean(pitch_arr))
        pitch_var = float(np.std(pitch_arr))
        return mean_pitch, pitch_var, pitch_arr

    def extract_jitter_and_shimmer(
        self, audio_data: np.ndarray
    ) -> Tuple[float, float, float]:
        """
        Calculate local Jitter (frequency instability), Shimmer (amplitude instability), and HNR.
        """
        if audio_data is None or len(audio_data) < 512:
            return 0.015, 0.035, 18.0
            
        signal = audio_data.astype(np.float64)
        # Find positive peaks (glottal pulses)
        peaks, props = find_peaks(signal, distance=int(self.sample_rate / 400.0), prominence=0.05)
        
        if len(peaks) < 4:
            return 0.015, 0.035, 18.0
            
        periods = np.diff(peaks) / float(self.sample_rate)
        amplitudes = np.abs(signal[peaks])
        
        # Local Jitter: mean absolute difference between consecutive periods / mean period
        mean_period = np.mean(periods)
        if mean_period > 1e-6:
            period_diffs = np.abs(np.diff(periods))
            jitter = float(np.mean(period_diffs) / mean_period)
        else:
            jitter = 0.015
            
        # Local Shimmer: mean absolute difference between consecutive amplitudes / mean amplitude
        mean_amp = np.mean(amplitudes)
        if mean_amp > 1e-6:
            amp_diffs = np.abs(np.diff(amplitudes))
            shimmer = float(np.mean(amp_diffs) / mean_amp)
        else:
            shimmer = 0.035
            
        # Harmonics-to-Noise Ratio (HNR in dB) approximation
        signal_var = np.var(signal)
        diff_var = np.var(np.diff(signal))
        if diff_var > 1e-8:
            hnr = float(10.0 * np.log10(max(1.0, signal_var / (diff_var * 0.5))))
        else:
            hnr = 20.0
            
        return (
            float(np.clip(jitter, 0.001, 0.20)),
            float(np.clip(shimmer, 0.001, 0.35)),
            float(np.clip(hnr, 0.0, 40.0)),
        )

    def extract_mfcc(self, audio_data: np.ndarray, num_mfcc: int = 13) -> List[float]:
        """
        Extract lightweight MFCC coefficients for edge acoustic profiling.
        """
        if audio_data is None or len(audio_data) < 512:
            return [round(float(x), 3) for x in np.zeros(num_mfcc)]
            
        signal = audio_data.astype(np.float64)
        # FFT power spectrum
        fft_spec = np.abs(np.fft.rfft(signal[:2048])) ** 2
        freqs = np.fft.rfftfreq(2048, 1.0 / self.sample_rate)
        
        # Construct triangular Mel filterbank
        mel_min = 0.0
        mel_max = 2595.0 * np.log10(1.0 + (self.sample_rate / 2.0) / 700.0)
        mel_points = np.linspace(mel_min, mel_max, num_mfcc + 2)
        hz_points = 700.0 * (10.0 ** (mel_points / 2595.0) - 1.0)
        bin_indices = np.floor((2048 + 1) * hz_points / self.sample_rate).astype(int)
        
        filter_energies = []
        for m in range(1, num_mfcc + 1):
            f_m_minus = bin_indices[m - 1]
            f_m = bin_indices[m]
            f_m_plus = bin_indices[m + 1]
            
            w = np.zeros(len(fft_spec))
            for k in range(f_m_minus, min(f_m, len(w))):
                w[k] = (k - f_m_minus) / max(1, f_m - f_m_minus)
            for k in range(f_m, min(f_m_plus, len(w))):
                w[k] = (f_m_plus - k) / max(1, f_m_plus - f_m)
                
            energy = np.sum(fft_spec * w)
            filter_energies.append(np.log(max(1e-8, energy)))
            
        # DCT (Discrete Cosine Transform) for cepstral decorrelation
        mfccs = []
        for i in range(num_mfcc):
            coef = sum(
                filter_energies[j] * math.cos(math.pi * i * (j + 0.5) / num_mfcc)
                for j in range(num_mfcc)
            )
            mfccs.append(round(float(coef), 3))
            
        return mfccs

    def extract_spectral_features(self, audio_data: np.ndarray) -> Tuple[float, float, float]:
        """
        Extract Spectral Centroid (Hz), Zero Crossing Rate (ZCR), and RMS Energy (dB).
        """
        if audio_data is None or len(audio_data) < 256:
            return 1800.0, 0.05, -22.0
            
        signal = audio_data.astype(np.float64)
        
        # Zero Crossing Rate
        zcr = float(np.mean(np.abs(np.diff(np.sign(signal)))) / 2.0)
        
        # RMS Energy
        rms = np.sqrt(np.mean(signal**2))
        rms_db = float(20.0 * np.log10(max(1e-6, rms)))
        
        # Spectral Centroid
        magnitude_spec = np.abs(np.fft.rfft(signal))
        freqs = np.fft.rfftfreq(len(signal), 1.0 / self.sample_rate)
        sum_mag = np.sum(magnitude_spec)
        if sum_mag > 1e-6:
            centroid = float(np.sum(freqs * magnitude_spec) / sum_mag)
        else:
            centroid = 1500.0
            
        return round(centroid, 1), round(zcr, 4), round(rms_db, 1)

    def extract_all(self, audio_data: np.ndarray) -> AcousticFeatures:
        """
        Run full DSP extraction pipeline on input audio array.
        """
        f0_mean, pitch_var, _ = self.extract_f0_pitch(audio_data)
        jitter, shimmer, hnr = self.extract_jitter_and_shimmer(audio_data)
        mfccs = self.extract_mfcc(audio_data, num_mfcc=13)
        centroid, zcr, rms_db = self.extract_spectral_features(audio_data)
        
        return AcousticFeatures(
            f0_pitch_hz=round(f0_mean, 1),
            pitch_variance=round(pitch_var, 1),
            jitter_local=round(jitter, 4),
            shimmer_local=round(shimmer, 4),
            hnr_db=round(hnr, 1),
            spectral_centroid_hz=round(centroid, 1),
            zero_crossing_rate=round(zcr, 4),
            rms_energy_db=round(rms_db, 1),
            mfcc_features=mfccs,
        )
