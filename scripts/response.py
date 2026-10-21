"""Cross-flow response of a run: amplitude A*_y and frequency ratio f_y / f_n,w.

Usage: python response.py <case dir> [--skip-periods 8]

Reads the cylinder position from log.pimpleFoam (sixDoFRigidBodyMotion report),
discards the first periods as transient, and reports the mean of the 10 %
largest peaks (as A*_y = Y/D) and the dominant frequency.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np

D = 0.05


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case", type=Path)
    p.add_argument("--skip-periods", type=float, default=8)
    a = p.parse_args()
    meta = json.loads((a.case / "case.json").read_text())
    t, y = [], []
    current = None
    for line in (a.case / "log.pimpleFoam").read_text().splitlines():
        if line.startswith("Time = "):
            current = float(line.split("=")[1])
        m = re.match(r"\s+Centre of mass: \(\S+ (\S+) \S+\)", line)
        if m and current is not None:
            if t and t[-1] == current:
                y[-1] = float(m.group(1))       # keep the last outer-corrector value
            else:
                t.append(current)
                y.append(float(m.group(1)))
    t, y = np.array(t), np.array(y) / D
    keep = t > a.skip_periods / meta["f_nw"]
    t, y = t[keep], y[keep] - y[keep].mean()
    peaks = np.sort(np.abs(y))[-max(1, len(y) // 10):]
    spec = np.abs(np.fft.rfft(y * np.hanning(len(y))))
    freq = np.fft.rfftfreq(len(y), d=np.mean(np.diff(t)))
    f_y = freq[np.argmax(spec[1:]) + 1]
    print(f"V* = {meta['vstar']}, zeta = {meta['zeta']}, Re = {meta['Re']:.0f}: "
          f"A*_y = {peaks.mean():.2f}, f_y/f_n,w = {f_y / meta['f_nw']:.2f} "
          f"(from t = {t[0]:.1f} to {t[-1]:.1f} s)")


if __name__ == "__main__":
    main()
