"""Monophonic fundamental-frequency detection using the YIN algorithm."""

import numpy as np


class YinPitchDetector:
    def __init__(self, sample_rate, threshold=0.1, fmin=70.0, fmax=1000.0):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.tau_min = max(2, int(sample_rate / fmax))
        self.tau_max = int(sample_rate / fmin)

    def detect(self, buf):
        """Return the estimated fundamental frequency in Hz, or None if
        no clear pitch was found in the buffer."""
        buf = np.asarray(buf, dtype=np.float64)
        tau_max = self.tau_max
        w = len(buf) - tau_max
        if w <= 0:
            return None

        diff = np.zeros(tau_max)
        for tau in range(1, tau_max):
            diff[tau] = np.sum((buf[:w] - buf[tau:tau + w]) ** 2)

        cmnd = np.ones(tau_max)
        running_sum = 0.0
        for tau in range(1, tau_max):
            running_sum += diff[tau]
            cmnd[tau] = diff[tau] * tau / running_sum if running_sum > 0 else 1.0

        tau = -1
        for t in range(self.tau_min, tau_max - 1):
            if cmnd[t] < self.threshold:
                while t + 1 < tau_max and cmnd[t + 1] < cmnd[t]:
                    t += 1
                tau = t
                break

        if tau == -1:
            return None

        if 0 < tau < tau_max - 1:
            s0, s1, s2 = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
            denom = 2 * s1 - s2 - s0
            better_tau = tau + (s2 - s0) / (2 * denom) if denom != 0 else tau
        else:
            better_tau = tau

        if better_tau <= 0:
            return None

        return self.sample_rate / better_tau
