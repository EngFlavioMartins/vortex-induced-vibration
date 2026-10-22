"""Animation for the README: the vortex street behind the elastically mounted cylinder.

Needs a reconstructed run that writes often for about one oscillation period or more, e.g.
restart a run of examples/quick_start.py for two periods with  writeControl timeStep;
writeInterval 3;  in system/controlDict, then reconstructPar. Renders every written time
between the two given times with ParaView (render_animation.py), keeps the stretch that best
closes one oscillation period, so the loop is smooth, and writes docs/assets/animation.webp.
Run:  python scripts/render/make_animation.py <case> <first time> <last time>
(set PVPYTHON if ParaView is not found)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from gif import crop_union, pvpython, save_gif  # noqa: E402

if len(sys.argv) != 4:
    sys.exit(__doc__)
case = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([pvpython(), str(HERE / "render_animation.py"), str(case), tmp, sys.argv[2], sys.argv[3]],
                   check=True)
    frames = [np.asarray(Image.open(p).convert("RGB"), float) for p in sorted(Path(tmp).glob("frame_*.png"))]
# loop: end where the picture comes closest to the first frame again (one period or more)
first = frames[0]
gap = [np.abs(f - first).mean() for f in frames]
k = int(np.argmin(gap[len(frames) // 3:])) + len(frames) // 3
print(f"looping on {k} of {len(frames)} frames")
frames = crop_union([f.astype(np.uint8) for f in frames[:k]])
save_gif(frames, ROOT / "docs" / "assets" / "animation.webp", fps=15, width=720)
