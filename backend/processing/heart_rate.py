
import numpy as np
from scipy.signal import find_peaks


def extract_heart_rate(signal, fs=125):
    """
    Extract heart rate from a preprocessed PPG signal.

    Parameters:
        signal: filtered PPG signal
        fs: sampling frequency in Hz

    Returns:
        Dictionary containing BPM, peaks and intervals
    """

    signal = np.asarray(signal, dtype=float)

    # Check signal validity
    if len(signal) < fs * 3 or not np.all(np.isfinite(signal)):
        return {
            "heart_rate": None,
            "peaks": np.array([], dtype=int),
            "intervals": np.array([])
        }

    # Minimum distance between peaks.
    # 0.33 seconds corresponds to approximately 180 BPM.
    min_distance = int(0.33 * fs)

    # Detect PPG peaks
    peaks, properties = find_peaks(
        signal,
        distance=min_distance,
        prominence=max(np.std(signal) * 0.25, 1e-10)
    )

    # Calculate time difference between peaks
    intervals = np.diff(peaks) / fs

    # Keep physiologically plausible intervals for this prototype
    valid_intervals = intervals[
        (intervals >= 60 / 180) &
        (intervals <= 60 / 40)
    ]

    if len(valid_intervals) == 0:
        heart_rate = None
    else:
        # Median reduces sensitivity to occasional outliers
        heart_rate = 60 / np.median(valid_intervals)

    return {
        "heart_rate": heart_rate,
        "peaks": peaks,
        "intervals": valid_intervals
    }
