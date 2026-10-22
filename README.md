# Vortex-induced vibration

<p align="center">
  <a href="https://doi.org/10.1016/j.marstruc.2019.01.005"><img src="https://img.shields.io/badge/paper-10.1016%2Fj.marstruc.2019.01.005-1F6FEB" alt="paper: 10.1016/j.marstruc.2019.01.005"></a>
  <a href="https://www.openfoam.com/"><img src="https://img.shields.io/badge/OpenFOAM-v2412-1C6EB4" alt="OpenFOAM: v2412"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="python: 3.10+"></a>
  <a href="https://github.com/EngFlavioMartins/vortex-induced-vibration/blob/HEAD/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-2E7D32" alt="license: Apache 2.0"></a>
  <a href="https://engflaviomartins.github.io/#work-viv"><img src="https://img.shields.io/badge/website-research%20page-15212B" alt="website: research page"></a>
</p>

**An elastically mounted cylinder shaking in its own wake, in OpenFOAM.**

<p align="center"><img src="docs/assets/animation.webp" width="560" alt="One oscillation of an elastically mounted brushed-metal cylinder shedding vortices, coloured by spanwise vorticity"></p>

One script writes a complete OpenFOAM case for a cylinder on a spring and damper, free to move across the flow, with the set-up of the papers below. The original simulations used ANSYS Fluent; this is a re-implementation for OpenFOAM v2412 (openfoam.com).

## Run it

```bash
git clone https://github.com/EngFlavioMartins/vortex-induced-vibration.git
cd vortex-induced-vibration
python run.py
```

`run.py` writes a two-dimensional case at reduced velocity V* = 7 to `runs/vstar7` and, if OpenFOAM is installed and loaded, runs it (about 20 minutes on 4 cores); otherwise it tells you the one command to run once OpenFOAM is there. The first time, it installs what it needs into a private `.venv` folder (a minute or so); after that it starts at once. All you need is Python 3.10 or newer (and OpenFOAM to run the case).

<details>
<summary>Prefer conda?</summary>

```bash
conda env create -f environment.yml
conda activate vortex-induced-vibration
python examples/quick_start.py
```

</details>

**Next:** Make other cases with `python src/make_case.py runs/my-case --vstar 6 --zeta 0.01` (`--two-d` for the fast 2D version). `python scripts/response.py runs/vstar7` reports the amplitude and frequency.

## Figure and animation

<p align="center"><img src="docs/assets/render.webp" width="560" alt="Vortex cores shed alternately behind an elastically mounted brushed-metal cylinder, coloured by spanwise vorticity"></p>

Vortex cores behind the moving cylinder, coloured by spanwise vorticity (teal clockwise, red anticlockwise). It comes from a coarse two-dimensional run (amplitude 0.66 D): treat it as qualitative, below the upper-branch response of the paper's three-dimensional simulations.

```bash
sh scripts/render/make_figure.sh runs/vstar7 16.669072          # the figure
python scripts/render/make_animation.py runs/vstar7-restart 17.86 19.6   # the animation at the top
```

Both need [ParaView](https://www.paraview.org/download/) and a reconstructed run (see `scripts/render/make_animation.py` for the frequent-output restart the animation uses); the figure also needs LaTeX.

## Cite

This code follows the set-up of the papers below. If you use it, please cite:

```bibtex
@article{martins2019viv3d,
  author  = {Martins, Flavio A. C. and Avila, J. P. J.},
  title   = {Three-Dimensional {CFD} Analysis of Damping Effects on Vortex-Induced Vibrations of {2DOF} Elastically-Mounted Circular Cylinders},
  journal = {Marine Structures},
  volume  = {65},
  pages   = {12--31},
  year    = {2019},
  doi     = {10.1016/j.marstruc.2019.01.005}
}

@article{martins2019vivre,
  author  = {Martins, Flavio A. C. and Avila, J. P. J.},
  title   = {Effects of the {Reynolds} Number and Structural Damping on Vortex-Induced Vibrations of an Elastically-Mounted Rigid Cylinder},
  journal = {International Journal of Mechanical Sciences},
  volume  = {156},
  pages   = {235--249},
  year    = {2019},
  doi     = {10.1016/j.ijmecsci.2019.03.024}
}
```

GitHub's **Cite this repository** button (from [CITATION.cff](CITATION.cff)) gives the same reference in other formats.

## Licence

[Apache 2.0](LICENSE): you are free to use, change and share this code, also commercially. If you pass it on, keep the [NOTICE](NOTICE) file with it; it says where the code comes from and how to cite it.
