"""Basic multi-pitch (chord) detection via spectral peak-picking with harmonic
suppression.

This is an approximation, not full polyphonic transcription: it works
reasonably for clean, simple voicings (open chords, power chords, two-note
double-stops) but will be less reliable on dense or heavily muted chords,
since overlapping harmonics between notes can mask or fake a peak.
"""

import numpy as np

MIN_FREQ = 70.0
MAX_FREQ = 2000.0
MAX_NOTES = 6
PEAK_RATIO_THRESHOLD = 0.15   # a peak must be at least this fraction of the strongest peak
DUPLICATE_TOLERANCE = 0.02    # 2% - collapse near-identical peaks from spectral leakage
HARMONIC_TOLERANCE = 0.025    # 2.5% - how close to an integer multiple counts as a harmonic


class ChordDetector:
    def __init__(self, sample_rate, min_freq=MIN_FREQ, max_freq=MAX_FREQ,
                 max_notes=MAX_NOTES, peak_ratio_threshold=PEAK_RATIO_THRESHOLD,
                 harmonic_tolerance=HARMONIC_TOLERANCE):
        self.sample_rate = sample_rate
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.max_notes = max_notes
        self.peak_ratio_threshold = peak_ratio_threshold
        self.harmonic_tolerance = harmonic_tolerance

    def detect(self, buf):
        """Return estimated fundamental frequencies (Hz), ascending, with
        harmonics of louder notes filtered out. Empty list if nothing usable
        was found."""
        buf = np.asarray(buf, dtype=np.float64)
        n = len(buf)
        if n < 512:
            return []

        window = np.hanning(n)
        n_fft = 1
        while n_fft < n * 4:
            n_fft *= 2

        spectrum = np.abs(np.fft.rfft(buf * window, n=n_fft))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / self.sample_rate)

        lo = np.searchsorted(freqs, self.min_freq)
        hi = np.searchsorted(freqs, self.max_freq)
        if hi - lo < 3:
            return []

        mags = spectrum[lo:hi]
        band_freqs = freqs[lo:hi]

        peak_idx = np.where((mags[1:-1] > mags[:-2]) & (mags[1:-1] > mags[2:]))[0] + 1
        if len(peak_idx) == 0:
            return []

        peak_mags = mags[peak_idx]
        top_mag = peak_mags.max()
        if top_mag <= 0:
            return []

        keep = peak_mags >= self.peak_ratio_threshold * top_mag
        peak_idx = peak_idx[keep]
        peak_mags = peak_mags[keep]
        if len(peak_idx) == 0:
            return []

        bin_width = band_freqs[1] - band_freqs[0]
        refined = []
        for i in peak_idx:
            if 0 < i < len(mags) - 1:
                y0, y1, y2 = mags[i - 1], mags[i], mags[i + 1]
                denom = y0 - 2 * y1 + y2
                p = 0.5 * (y0 - y2) / denom if denom != 0 else 0.0
            else:
                p = 0.0
            refined.append(band_freqs[i] + p * bin_width)

        order = np.argsort(peak_mags)[::-1]
        candidates = [(refined[i], peak_mags[i]) for i in order]

        fundamentals = []
        for freq, _mag in candidates:
            redundant = False
            for f0 in fundamentals:
                ratio = freq / f0
                if abs(ratio - 1.0) < DUPLICATE_TOLERANCE:
                    redundant = True
                    break
                harmonic_number = round(ratio)
                if harmonic_number >= 2:
                    expected = f0 * harmonic_number
                    if abs(freq - expected) / expected < self.harmonic_tolerance:
                        redundant = True
                        break
            if not redundant:
                fundamentals.append(freq)
            if len(fundamentals) >= self.max_notes:
                break

        return sorted(fundamentals)
