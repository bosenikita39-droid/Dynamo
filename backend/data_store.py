"""Bounded ephemeral datasets for a DB-free local demonstration."""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import RLock
import re
import pandas as pd
import numpy as np

SAMPLE = Path(__file__).parent / 'sample_data' / 'bidmc_signals.csv'
MAX_CSV_BYTES = 8 * 1024 * 1024
MAX_SAMPLES = 200_000
MAX_UPLOADS = 5


class DatasetError(ValueError):
    pass


@dataclass(frozen=True)
class Recording:
    id: str
    name: str
    time: np.ndarray
    ppg: np.ndarray
    fs: float
    source: str

    def meta(self):
        return {
            'id': self.id,
            'name': self.name,
            'source': self.source,
            'channel': 'PLETH',
            'samples': len(self.ppg),
            'sampling_rate_hz': round(self.fs, 4),
            'duration_s': round(float(self.time[-1] - self.time[0]), 3),
            'limitations': 'Terrestrial patient data; not validated for astronaut medical use.',
        }


def parse_csv(blob: bytes, record_id: str, name: str, source: str) -> Recording:
    if not blob or len(blob) > MAX_CSV_BYTES:
        raise DatasetError('CSV must be nonempty and at most 8 MiB.')
    try:
        df = pd.read_csv(BytesIO(blob), encoding='utf-8-sig', low_memory=False)
    except (pd.errors.ParserError, UnicodeError, ValueError) as e:
        raise DatasetError('Unable to read a valid UTF-8 CSV file.') from e
    df.columns = df.columns.str.strip()
    if df.columns.duplicated().any():
        raise DatasetError('Duplicate CSV column names are not supported.')
    time_name = next((k for k in ('Time [s]', 'time_s', 'time') if k in df.columns), None)
    if time_name is None or 'PLETH' not in df:
        raise DatasetError('CSV requires Time [s] (or time_s/time) and PLETH columns.')
    if not 375 <= len(df) <= MAX_SAMPLES:
        raise DatasetError('CSV requires between 375 and 200,000 samples.')
    time = pd.to_numeric(df[time_name], errors='coerce').to_numpy(dtype=float)
    ppg = pd.to_numeric(df['PLETH'], errors='coerce').to_numpy(dtype=float)
    if not np.all(np.isfinite(time)) or np.any(np.diff(time) < 0):
        raise DatasetError('Timestamps must be finite and non-decreasing.')
    # The supplied BIDMC CSV rounds timestamps after 100 seconds, creating
    # apparent duplicates even though the waveform was sampled at 125 Hz.
    # Infer sampling rate from the early high-precision segment, then recover
    # a nominal sample clock ONLY when every timestamp agrees within 6 ms.
    diffs = np.diff(time[:min(len(time), 2000)])
    positive = diffs[diffs > 0]
    if len(positive) == 0:
        raise DatasetError('Cannot infer sampling frequency from timestamps.')
    median_dt = float(np.median(positive))
    fs = round(1.0 / median_dt, 4)
    if not 20 <= fs <= 1000:
        raise DatasetError('Sampling frequency must be 20-1000 Hz for this PPG prototype.')
    nominal = time[0] + np.arange(len(time), dtype=float) / fs
    if np.max(np.abs(nominal - time)) <= 0.006:
        time = nominal
    elif np.any(np.diff(time) == 0):
        raise DatasetError('Ambiguous duplicate timestamps: unable to recover a valid sample clock.')
    elif np.quantile(np.diff(time), .25) < median_dt * .75:
        raise DatasetError('Irregular cadence is not supported; preserve gaps as missing PPG values.')
    # True timestamp gaps remain visible to the downstream window integrity check.
    if np.isinf(ppg).any():
        raise DatasetError('Infinite PPG amplitudes are not allowed.')
    time.setflags(write=False)
    ppg.setflags(write=False)
    return Recording(id=record_id, name=name, time=time, ppg=ppg, fs=fs, source=source)


class RecordingStore:
    def __init__(self):
        self.lock = RLock()
        self.recordings = {'bidmc_01': parse_csv(SAMPLE.read_bytes(),'bidmc_01','BIDMC recording 01','Bundled public terrestrial clinical recording')}
        self.upload_order = []

    def list(self):
        with self.lock:
            return [rec.meta() for rec in self.recordings.values()]

    def get(self, record_id):
        with self.lock:
            return self.recordings.get(record_id)

    def upload(self, blob: bytes, name: str):
        from uuid import uuid4
        safe_name = re.sub(r'[^\w.\- ]','_',name)[:80] or 'uploaded.csv'
        record_id = 'upload_' + uuid4().hex[:12]
        item = parse_csv(blob, record_id, safe_name, 'Uploaded local CSV (ephemeral)')
        with self.lock:
            if len(self.upload_order) >= MAX_UPLOADS:
                oldest = self.upload_order.pop(0)
                self.recordings.pop(oldest, None)
            self.recordings[record_id] = item
            self.upload_order.append(record_id)
        return item
