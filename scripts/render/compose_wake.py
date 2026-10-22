"""Add the LaTeX overlay (one short signed colour bar) to the cylinder wake render.

Usage: python compose_wake.py <raw png> <output stem>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from overlay import compose  # noqa: E402

W_RANGE = 4.0           # same as render_wake.py
raw, stem = Path(sys.argv[1]), Path(sys.argv[2])
compose([(raw, None)], stem,
        bar=dict(name="signed_dark", vmin=-W_RANGE, vmax=W_RANGE, title=r"$\omega_z D/U$",
                 ticks=[(0.0, f"$-${W_RANGE:.0f}"), (0.5, "0"), (1.0, f"{W_RANGE:.0f}")]))
