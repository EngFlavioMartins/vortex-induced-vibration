"""ParaView (pvpython) animation frames of the vortex street behind the moving cylinder.

Usage: pvpython render_animation.py <case dir> <frame directory> [first time] [last time]
Same scene and camera as the still figure (render_wake.scene), one frame per written time
between the two times (default: all of them).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from render_wake import CAMERA, scene  # noqa: E402

case, out = Path(sys.argv[1]), Path(sys.argv[2])
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else float("-inf")
t1 = float(sys.argv[4]) if len(sys.argv) > 4 else float("inf")
width, height = 1440, 900
times = sorted(float(p.name) for p in case.iterdir()
               if p.is_dir() and p.name.replace(".", "", 1).isdigit() and t0 <= float(p.name) <= t1)

view, set_time = scene(case, width, height)
for key, value in CAMERA.items():
    setattr(view, key, value)
out.mkdir(parents=True, exist_ok=True)
for k, t in enumerate(times):
    set_time(t)
    style.save(view, out / f"frame_{k:03d}.png", width, height)
    print(k, end=" ", flush=True)
print()
