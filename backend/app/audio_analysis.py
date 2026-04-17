"""
OVO Backend — Audio Analysis
─────────────────────────────
Uses librosa to extract musical metadata from .wav files:
  • BPM (tempo detection)
  • Key (chroma-based estimation)
  • Duration (formatted as M:SS)
"""

import logging
from pathlib import Path

import librosa
import numpy as np

logger = logging.getLogger("ovo")

# ──────────────────────────────────────────────
# Key estimation helpers
# ──────────────────────────────────────────────

# Krumhansl-Kessler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _estimate_key(y: np.ndarray, sr: int) -> tuple[str, str]:
    """
    Estimates the musical key using chroma features and
    Krumhansl-Kessler key-finding algorithm.

    Returns: (note, mode) e.g. ("A", "Min") or ("C", "Maj")
    """
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)

    # Normalize
    chroma_mean = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-8)

    best_corr = -2.0
    best_key = "C"
    best_mode = "Maj"

    for shift in range(12):
        # Rotate the chroma vector
        rotated = np.roll(chroma_mean, -shift)

        # Correlate with major profile
        major_corr = np.corrcoef(rotated, MAJOR_PROFILE)[0, 1]
        if major_corr > best_corr:
            best_corr = major_corr
            best_key = NOTE_NAMES[shift]
            best_mode = "Maj"

        # Correlate with minor profile
        minor_corr = np.corrcoef(rotated, MINOR_PROFILE)[0, 1]
        if minor_corr > best_corr:
            best_corr = minor_corr
            best_key = NOTE_NAMES[shift]
            best_mode = "Min"

    return best_key, best_mode


def _format_duration(seconds: float) -> str:
    """Formats seconds into M:SS string."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def analyze_audio(file_path: str) -> dict:
    """
    Analyzes a .wav file and returns musical metadata.

    Args:
        file_path: Path to the .wav file

    Returns:
        {
            "bpm": int,
            "key": str,       # e.g. "A Min"
            "duration": str,   # e.g. "0:30"
            "duration_sec": float,
        }
    """
    logger.info(f"🎵 Analyzing audio: {Path(file_path).name}")

    # Load audio file
    y, sr = librosa.load(file_path, sr=22050, mono=True)

    # Duration
    duration_sec = librosa.get_duration(y=y, sr=sr)
    duration_str = _format_duration(duration_sec)
    logger.info(f"  Duration: {duration_str} ({duration_sec:.1f}s)")

    # BPM detection
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    # tempo can be an array; take the first element
    bpm = int(round(float(np.atleast_1d(tempo)[0])))
    logger.info(f"  BPM: {bpm}")

    # Key estimation
    note, mode = _estimate_key(y, sr)
    key_str = f"{note} {mode}"
    logger.info(f"  Key: {key_str}")

    return {
        "bpm": bpm,
        "key": key_str,
        "duration": duration_str,
        "duration_sec": duration_sec,
    }
