"""Quick start for Vortex-induced vibration: write a two-dimensional VIV case (V* = 7) and run it if OpenFOAM is available.

Run from the repository root with:  python run.py
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "runs" / "vstar7"


def main():
    subprocess.check_call([sys.executable, str(ROOT / "src" / "make_case.py"), str(CASE), "--vstar", "7", "--two-d"])
    print(f"Case written to {CASE.relative_to(ROOT)}")
    if shutil.which("pimpleFoam") is None:
        print("OpenFOAM v2412 (openfoam.com) was not found on this computer, so the case was only prepared.")
        print("Install OpenFOAM (https://www.openfoam.com/download), load its environment, then run:")
        print("    cd runs/vstar7 && ./Allrun")
        return
    print("OpenFOAM found: running the case (this takes about 20 minutes on 4 cores) ...")
    subprocess.check_call(["sh", "./Allrun"], cwd=CASE)
    print("Done. Results are in", CASE.relative_to(ROOT))


if __name__ == "__main__":
    main()
