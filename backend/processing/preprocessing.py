
import numpy as np

from scipy.signal import (
    butter,
    sosfiltfilt,
    iirnotch,
    filtfilt
)


# ==========================================
# 1. HIGH PASS FILTER
# Removes low-frequency noise
# ==========================================

def high_pass_filter(signal, fs, cutoff=0.5, order=4):

    signal = np.asarray(signal, dtype=float)

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains NaN or infinite values")

    if not 0 < cutoff < fs / 2:
        raise ValueError("Invalid cutoff frequency")

    sos = butter(
        order,
        cutoff,
        btype="highpass",
        fs=fs,
        output="sos"
    )

    return sosfiltfilt(sos, signal)


# ==========================================
# 2. LOW PASS FILTER
# Removes high-frequency noise
# ==========================================

def low_pass_filter(signal, fs, cutoff=5.0, order=4):

    signal = np.asarray(signal, dtype=float)

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains NaN or infinite values")

    if not 0 < cutoff < fs / 2:
        raise ValueError("Invalid cutoff frequency")

    sos = butter(
        order,
        cutoff,
        btype="lowpass",
        fs=fs,
        output="sos"
    )

    return sosfiltfilt(sos, signal)


# ==========================================
# 3. BAND PASS FILTER
# Keeps selected frequency range
# ==========================================

def band_pass_filter(
    signal,
    fs,
    lowcut=0.5,
    highcut=5.0,
    order=4
):

    signal = np.asarray(signal, dtype=float)

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains NaN or infinite values")

    if not 0 < lowcut < highcut < fs / 2:
        raise ValueError("Invalid band-pass frequencies")

    sos = butter(
        order,
        [lowcut, highcut],
        btype="bandpass",
        fs=fs,
        output="sos"
    )

    return sosfiltfilt(sos, signal)


# ==========================================
# 4. NOTCH FILTER
# Removes specific frequency interference
# Example: 50 Hz electrical noise
# ==========================================

def notch_filter(signal, fs, frequency=50, Q=30):

    signal = np.asarray(signal, dtype=float)

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains NaN or infinite values")

    if not 0 < frequency < fs / 2:
        raise ValueError("Invalid notch frequency")

    if Q <= 0:
        raise ValueError("Q must be positive")

    b, a = iirnotch(
        frequency,
        Q,
        fs
    )

    return filtfilt(b, a, signal)


# ==========================================
# 5. HAMPEL FILTER
# Detects and replaces sudden outliers
# ==========================================

def hampel_filter(signal, window=7, threshold=3.0):

    signal = np.asarray(signal, dtype=float)

    if not np.all(np.isfinite(signal)):
        raise ValueError("Signal contains NaN or infinite values")

    if window < 1 or threshold <= 0:
        raise ValueError("Invalid Hampel parameters")

    result = signal.copy()

    outlier_mask = np.zeros(
        len(signal),
        dtype=bool
    )

    for i in range(len(signal)):

        start = max(0, i - window)

        end = min(len(signal), i + window + 1)

        section = signal[start:end]

        median = np.median(section)

        mad = np.median(
            np.abs(section - median)
        )

        sigma = 1.4826 * mad

        if sigma > 0:

            if abs(signal[i] - median) > threshold * sigma:

                outlier_mask[i] = True

                result[i] = median

    return result, outlier_mask


# ==========================================
# 6. COMPLETE PREPROCESSING PIPELINE
# ==========================================

def preprocess_signal(
    signal,
    fs,
    use_hampel=True,
    use_notch=False
):

    original = np.asarray(signal, dtype=float)

    # Step 1: Hampel filtering
    if use_hampel:

        processed, outlier_mask = hampel_filter(
            original
        )

    else:

        processed = original.copy()

        outlier_mask = np.zeros(
            len(original),
            dtype=bool
        )

    # Step 2: Optional 50 Hz notch filtering
    if use_notch and 50 < fs / 2:

        processed = notch_filter(
            processed,
            fs,
            frequency=50
        )

    # Step 3: Butterworth band-pass filtering
    processed = band_pass_filter(
        processed,
        fs,
        lowcut=0.5,
        highcut=min(5.0, fs * 0.4)
    )

    return processed, outlier_mask
