
import numpy as np
import pandas as pd

from scipy.signal import find_peaks


# ============================================
# 1. MISSING DATA QUALITY
# ============================================

def missing_data_quality(signal):

    signal = np.asarray(signal, dtype=float)

    missing_ratio = np.mean(~np.isfinite(signal))

    quality = 1 - missing_ratio

    return float(quality), float(missing_ratio * 100)


# ============================================
# 2. SPIKE QUALITY
# ============================================

def spike_quality(outlier_mask):

    outlier_mask = np.asarray(
        outlier_mask,
        dtype=bool
    )

    spike_percentage = np.mean(outlier_mask) * 100

    # Provisional penalty scale:
    # 5% flagged samples corresponds to zero quality.

    quality = 1 - spike_percentage / 5

    quality = np.clip(quality, 0, 1)

    return float(quality), float(spike_percentage)


# ============================================
# 3. FLATLINE DETECTION
# ============================================

def flatline_quality(signal):

    signal = np.asarray(signal, dtype=float)

    valid = signal[np.isfinite(signal)]

    if len(valid) < 2:
        return 0.0, 100.0

    differences = np.abs(np.diff(valid))

    amplitude = np.ptp(valid)

    tolerance = max(amplitude * 1e-4, 1e-12)

    flat_samples = np.sum(differences <= tolerance)

    flat_percentage = (
        flat_samples / len(differences)
    ) * 100

    quality = 1 - flat_percentage / 10

    quality = np.clip(quality, 0, 1)

    return float(quality), float(flat_percentage)


# ============================================
# 4. HEARTBEAT PEAK DETECTION
# ============================================

def peak_quality(signal, fs):

    signal = np.asarray(signal, dtype=float)

    valid = np.isfinite(signal)

    signal = signal[valid]

    if len(signal) < fs * 3:
        return 0.0, 0, 0.0

    signal_std = np.std(signal)

    if signal_std < 1e-10:
        return 0.0, 0, 0.0

    peaks, properties = find_peaks(
        signal,
        distance=int(fs * 0.33),
        prominence=max(signal_std * 0.25, 1e-10)
    )

    if len(peaks) < 3:
        return 0.0, len(peaks), 0.0

    intervals = np.diff(peaks) / fs

    # Broad technical pulse-interval limits
    plausible = (
        (intervals >= 0.33) &
        (intervals <= 1.5)
    )

    interval_quality = np.mean(plausible)

    return float(interval_quality), len(peaks), float(
        np.mean(plausible) * 100
    )


# ============================================
# 5. PULSE AMPLITUDE CONSISTENCY
# ============================================

def amplitude_quality(signal, fs):

    signal = np.asarray(signal, dtype=float)

    signal_std = np.std(signal)

    if signal_std < 1e-10:
        return 0.0

    peaks, properties = find_peaks(
        signal,
        distance=int(fs * 0.33),
        prominence=max(signal_std * 0.25, 1e-10)
    )

    prominences = properties.get("prominences", [])

    if len(prominences) < 3:
        return 0.0

    median_prominence = np.median(prominences)

    if median_prominence <= 0:
        return 0.0

    # Robust coefficient of variation
    amplitude_mad = np.median(
        np.abs(prominences - median_prominence)
    )

    robust_cv = (
        1.4826 * amplitude_mad / median_prominence
    )

    quality = 1 - robust_cv

    return float(np.clip(quality, 0, 1))


# ============================================
# 6. COMPLETE SQI CALCULATION
# ============================================

def calculate_sqi(
    original_signal,
    filtered_signal,
    outlier_mask,
    fs
):

    original_signal = np.asarray(
        original_signal,
        dtype=float
    )

    filtered_signal = np.asarray(
        filtered_signal,
        dtype=float
    )

    outlier_mask = np.asarray(
        outlier_mask,
        dtype=bool
    )

    if not (
        len(original_signal) ==
        len(filtered_signal) ==
        len(outlier_mask)
    ):
        raise ValueError("All input arrays must have equal lengths.")

    if not np.all(np.isfinite(filtered_signal)):
        raise ValueError("Filtered signal contains invalid values.")

    # Individual quality parameters
    missing_q, missing_pct = missing_data_quality(
        original_signal
    )

    spike_q, spike_pct = spike_quality(
        outlier_mask
    )

    flat_q, flat_pct = flatline_quality(
        original_signal
    )

    peak_q, peak_count, plausible_pct = peak_quality(
        filtered_signal, fs
    )

    amplitude_q = amplitude_quality(
        filtered_signal, fs
    )

    # Weighted quality score
    weights = {
        "missing": 0.25,
        "spikes": 0.20,
        "flatline": 0.15,
        "peaks": 0.20,
        "amplitude": 0.20
    }

    sqi = 100 * (
        weights["missing"] * missing_q +
        weights["spikes"] * spike_q +
        weights["flatline"] * flat_q +
        weights["peaks"] * peak_q +
        weights["amplitude"] * amplitude_q
    )

    # Provisional engineering categories
    if sqi >= 80:
        status = "HIGH"

    elif sqi >= 60:
        status = "MEDIUM"

    else:
        status = "LOW"

    return {
        "SQI": round(float(sqi), 2),
        "Status": status,
        "Missing Data (%)": round(missing_pct, 2),
        "Spike Percentage (%)": round(spike_pct, 2),
        "Flatline Percentage (%)": round(flat_pct, 2),
        "Peak Count": peak_count,
        "Plausible Interval (%)": round(plausible_pct, 2),
        "Amplitude Quality": round(amplitude_q * 100, 2)
    }


# ============================================
# 7. WINDOW-BASED SQI
# ============================================

def calculate_window_sqi(
    original_signal,
    filtered_signal,
    outlier_mask,
    fs,
    window_seconds=10
):

    window_size = int(fs * window_seconds)

    results = []

    for start in range(
        0,
        len(original_signal),
        window_size
    ):

        end = min(
            start + window_size,
            len(original_signal)
        )

        original_window = original_signal[start:end]

        filtered_window = filtered_signal[start:end]

        mask_window = outlier_mask[start:end]

        if len(original_window) < fs * 3:
            continue

        result = calculate_sqi(
            original_window,
            filtered_window,
            mask_window,
            fs
        )

        result["Start Time (s)"] = start / fs

        result["End Time (s)"] = end / fs

        results.append(result)

    return pd.DataFrame(results)
