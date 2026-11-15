"""Thin adapter around the team's original preprocessing/SQI/heart-rate modules.

No clinical model is trained here. Thresholds, quality score and classification
are provisional engineering rules for a hackathon research prototype.
"""
from __future__ import annotations
from time import perf_counter
from uuid import uuid4
import numpy as np
from data_store import DatasetError, Recording
from processing.preprocessing import preprocess_signal
from processing.signal_quality import calculate_sqi
from processing.heart_rate import extract_heart_rate

LOW_BPM = 50.0  # Demonstration-only thresholds, not medical advice.
HIGH_BPM = 120.0
PLOT_CAP = 1500


def compact_series(t, raw, cleaned, reference, max_points=PLOT_CAP):
    step = max(1, int(np.ceil(len(t) / max_points)))
    def series(a):
        if a is None:
            return None
        return [round(float(v), 5) if np.isfinite(v) else None for v in a[::step]]
    return {'time_s': [round(float(v), 4) for v in t[::step]],
            'raw': series(raw), 'filtered': series(cleaned),
            'reference': series(reference), 'decimation_step': step}


def analyze(rec: Recording, start_s: float, duration_s: float,
            noise_percent: float=0, noise_seed: int=42) -> dict:
    t0 = perf_counter()
    relative_time = rec.time - rec.time[0]
    start = int(np.searchsorted(relative_time, start_s, side='left'))
    end = int(np.searchsorted(relative_time, start_s+duration_s, side='left'))
    if end > len(rec.ppg):end = len(rec.ppg)
    if start >= len(rec.ppg) or end-start < int(3*rec.fs):
        raise DatasetError('Selected interval must contain at least 3 seconds of recording.')

    # Filtering has transient responses at its boundaries. Supply context but
    # only return and score the requested window. Never splice filtered data
    # across a gap or invent values for missing samples.
    margin = max(int(3*rec.fs), 50)
    left = max(0,start-margin)
    right = min(len(rec.ppg),end+margin)
    src = rec.ppg[left:right].copy()
    time = rec.time[start:end]
    window = src[start-left:end-left].copy()
    reference = window.copy() if noise_percent > 0 else None

    if noise_percent > 0:
        # Fixed seed makes the experiment reproducible. This is synthetic
        # white noise, NOT a faithful model of all motion artifacts.
        rng = np.random.default_rng(noise_seed)
        valid_std = np.nanstd(window)
        sigma = max(float(valid_std), 0.01) * (noise_percent / 100.0) * 2.0
        window += rng.normal(0, sigma, len(window))
        src[start-left:end-left] = window

    expected_dt = 1.0 / rec.fs
    observed_dt = np.diff(time)
    gap_count = int(np.sum(observed_dt > expected_dt*1.5))
    missing_count = int(np.sum(~np.isfinite(window)))
    unprocessable = bool(gap_count or missing_count or not np.all(np.isfinite(src)))
    warnings = ['Research demonstration only: thresholds and SQI are not medically validated.']
    if rec.source.startswith('Bundled'):
        warnings.append('BIDMC represents terrestrial patients, not astronauts.')
    if noise_percent:
        warnings.append('Noise is algorithmically injected; this is not an independent sensor recording.')
    if gap_count:
        warnings.append(f'{gap_count} timestamp gap(s) in selected window; no interpolation performed.')
    if missing_count:
        warnings.append(f'{missing_count} invalid waveform sample(s); no interpolation performed.')

    filtered = None
    sqi = None
    raw_peaks = []
    filtered_peaks = []
    raw_hr = None
    derived_hr = None
    if not unprocessable:
        try:
            processed, outliers = preprocess_signal(src,rec.fs)
            filtered = processed[start-left:end-left]
            mask = outliers[start-left:end-left]
            sqi = calculate_sqi(window, filtered, mask, rec.fs)
            raw_result = extract_heart_rate(window,rec.fs)
            proc_result = extract_heart_rate(filtered,rec.fs)
            raw_hr = raw_result['heart_rate']
            derived_hr = proc_result['heart_rate']
            raw_peaks = [round(float(time[i]),4) for i in raw_result['peaks'] if i<len(time)]
            filtered_peaks = [round(float(time[i]),4) for i in proc_result['peaks'] if i<len(time)]
        except (ValueError, FloatingPointError) as exc:
            warnings.append('Processing could not safely evaluate this interval: '+str(exc))

    def safe_hr(v):
        return round(float(v),2) if v is not None and np.isfinite(v) else None
    raw_hr = safe_hr(raw_hr)
    derived_hr = safe_hr(derived_hr)

    if sqi is None:
        quality = {'score': 0.0, 'status': 'LOW', 'missing_percent': round(100*missing_count/len(window),2),
                   'spike_percent': None, 'flatline_percent': None, 'peak_count': None,
                   'plausible_intervals_percent': None, 'amplitude_quality_percent': None}
        decision = 'DEFER'
        explanation = 'The selected signal window is not usable; no alert can be supported from this measurement.'
    else:
        quality = {'score':sqi['SQI'], 'status':sqi['Status'],
                   'missing_percent':sqi['Missing Data (%)'],
                   'spike_percent':sqi['Spike Percentage (%)'],
                   'flatline_percent':sqi['Flatline Percentage (%)'],
                   'peak_count':sqi['Peak Count'],
                   'plausible_intervals_percent':sqi['Plausible Interval (%)'],
                   'amplitude_quality_percent':sqi['Amplitude Quality']}
        if derived_hr is None or sqi['Status']=='LOW':
            decision = 'DEFER'
            explanation = 'Low confidence or no usable pulse-rate estimate: repeat or review the measurement.'
        elif sqi['Status']=='MEDIUM':
            decision = 'QUALIFY'
            explanation = 'Measurement has limitations. Review before using its derived rate for an alert.'
        elif derived_hr < LOW_BPM or derived_hr > HIGH_BPM:
            decision = 'ISSUE'
            explanation = 'Quality checks passed and derived rate crossed a demonstration-only threshold.'
        else:
            decision = 'NO_ALERT'
            explanation = 'Quality checks passed; no demonstration threshold was crossed.'

    conventional = ('NO_MEASUREMENT' if raw_hr is None else
                    'ALERT' if raw_hr<LOW_BPM or raw_hr>HIGH_BPM else 'NO_ALERT')
    # A controlled ablation: same filtered rate, but without quality gating.
    filtered_only = ('NO_MEASUREMENT' if derived_hr is None else
                     'ALERT' if derived_hr<LOW_BPM or derived_hr>HIGH_BPM else 'NO_ALERT')
    if noise_percent and reference is not None and np.all(np.isfinite(reference)):
        ref_hr = safe_hr(extract_heart_rate(reference,rec.fs)['heart_rate'])
    else:
        ref_hr = None
    out = {
        'analysis_id':'analysis_'+uuid4().hex[:12],
        'recording_id':rec.id,
        'source': rec.source,
        'channel':'PLETH',
        'window':{'start_s':round(float(time[0]-rec.time[0]),3),
                  'end_s':round(float(time[-1]-rec.time[0]),3),
                  'samples':len(time),'sampling_rate_hz':round(rec.fs,4),
                  'timestamp_gaps':gap_count},
        'processing':{'method':'Existing team Hampel + Butterworth bandpass (0.5-5 Hz)',
                      'noise_percent':noise_percent,'noise_seed':noise_seed,
                      'filter_mode':'zero-phase offline; NOT streaming real-time'},
        'quality':quality,
        'measurements':{'raw_pulse_bpm':raw_hr,'filtered_pulse_bpm':derived_hr,
                        'reference_pulse_bpm':ref_hr,
                        'bpm_difference':round(derived_hr-raw_hr,2) if raw_hr is not None and derived_hr is not None else None,
                        'reference_type':'unmodified-signal algorithm estimate (NOT clinical ground truth)' if ref_hr is not None else None},
        'decision':{'status':decision,'conventional':conventional,'filtered_only':filtered_only,
                    'explanation':explanation,
                    'thresholds_bpm':{'low':LOW_BPM,'high':HIGH_BPM,'type':'illustrative, not clinical'}},
        'waveform':compact_series(time,window,filtered,reference),
        'peaks':{'raw_s':raw_peaks[:200], 'filtered_s':filtered_peaks[:200]},
        'warnings':warnings,
        'processing_ms':round((perf_counter()-t0)*1000,2),
    }
    return out


def evaluate(rec: Recording,start_s:float,duration_s:float,noise_seed:int):
    # Compare decisions under controlled synthetic noise. This experiment does
    # not measure clinical false positive rates or actual astronaut accuracy.
    runs=[]
    for intensity in [0,25,60]:
        result=analyze(rec,start_s,duration_s,intensity,noise_seed)
        runs.append({'noise_percent':intensity,'raw_bpm':result['measurements']['raw_pulse_bpm'],
                     'filtered_bpm':result['measurements']['filtered_pulse_bpm'],
                     'reference_estimate_bpm':result['measurements']['reference_pulse_bpm'],
                     'quality_score':result['quality']['score'],
                     'quality_status':result['quality']['status'],
                     'conventional':result['decision']['conventional'],
                     'filtered_only':result['decision']['filtered_only'],
                     'signaltrust':result['decision']['status'],
                     'processing_ms':result['processing_ms']})
    return {'recording_id':rec.id,'experiment':'Reproducible synthetic Gaussian noise sweep',
            'seed':noise_seed,'results':runs,
            'limitations':['Reference is an estimate from the unmodified PPG; not independent labeled truth.',
                           'No claim of clinical sensitivity, specificity, or astronaut health outcomes.']}
