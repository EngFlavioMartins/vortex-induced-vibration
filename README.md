# Vortex-induced vibration

OpenFOAM case generator for vortex-induced vibration (VIV) of an elastically mounted rigid cylinder free to move in the cross-flow direction. It follows the set-up of

> F. A. C. Martins and J. P. J. Avila (2019). Three-dimensional CFD analysis of damping effects on vortex-induced vibrations of 2DOF elastically-mounted circular cylinders. *Marine Structures* 65, 12–31. [doi:10.1016/j.marstruc.2019.01.005](https://doi.org/10.1016/j.marstruc.2019.01.005)

and the companion study of Reynolds-number and damping effects:

> F. A. C. Martins and J. P. J. Avila (2019). Effects of the Reynolds number and structural damping on vortex-induced vibrations of an elastically-mounted rigid cylinder. *International Journal of Mechanical Sciences* 156, 235–249. [doi:10.1016/j.ijmecsci.2019.03.024](https://doi.org/10.1016/j.ijmecsci.2019.03.024)

The original simulations used ANSYS Fluent and are not available. This repository is a re-implementation in OpenFOAM v2412 (openfoam.com).

## Set-up

The defaults are taken from the Marine Structures paper:

- **Cylinder:** D = 0.05 m, span πD, mass ratio m* = 2.4, spring stiffness k = 29.15 N/m.
- **Natural frequency:** f<sub>n</sub> = 1 Hz in vacuum, 0.84 Hz in water with C<sub>A</sub> = 1.
- **Flow model:** URANS with k–ω SST.
- **Domain:** 32D × 24D, with the cylinder 12D from the inlet and symmetry on the far-field boundaries.
- **Time step:** T<sub>n,w</sub>/200.

The cylinder moves with OpenFOAM's `sixDoFRigidBodyMotion`. It is constrained to cross-flow translation and held by a linear spring and damper with c = 2ζ√(km). The mesh near the cylinder moves rigidly, and the deformation is absorbed between 1.5D and 10D from it.

The mesh is an O-grid made with `blockMesh`: 144 cells around the cylinder and about 18 600 cells in the plane. That is coarser than the paper's. `--two-d` gives one cell across the span; without it the case has 12 cells across the span with symmetry at both ends, as in the paper.

## Quick start

```bash
python src/make_case.py runs/vstar7 --vstar 7 --zeta 0.0125 --two-d
cd runs/vstar7 && ./Allrun        # with OpenFOAM v2412 loaded
python ../../scripts/response.py .    # cross-flow amplitude and frequency
```

## Repository guide

| Location | Purpose |
| --- | --- |
| `src/make_case.py` | Writes mesh, dictionaries and initial fields for a given V* and ζ |
| `scripts/response.py` | Cross-flow amplitude A*<sub>y</sub> and frequency ratio from the run log |
| `scripts/render/` | Scripts that make the website image (ParaView `pvpython`, cmcrameri, Pillow) |

## Licence

MIT; see [LICENSE](LICENSE).
