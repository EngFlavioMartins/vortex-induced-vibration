"""Write an OpenFOAM (v2412, openfoam.com) case for vortex-induced vibration of an
elastically mounted rigid cylinder free to move in the cross-flow direction.

Set-up after Martins & Avila (2019), Marine Structures 65, 12-31,
doi:10.1016/j.marstruc.2019.01.005: D = 0.05 m, span L = pi*D, mass ratio
m* = 2.4, k = 29.15 N/m (f_n = 1 Hz in vacuum, 0.84 Hz in water with C_A = 1),
URANS with k-omega SST, domain 32D x 24D x pi*D with the cylinder 12D from the
inlet, symmetry on the far-field and spanwise boundaries, time step T_n/200.
The mesh is coarser than the paper's (an O-grid from blockMesh, 12 cells
across the span), and the body motion uses OpenFOAM's sixDoFRigidBodyMotion
with a linear spring-damper instead of the paper's Fluent implementation.

Usage: python make_case.py <case dir> [--vstar 7] [--zeta 0.0125] [--periods 15] [--two-d]
"""
import argparse
import math
from pathlib import Path

D, RHO, NU = 0.05, 998.2, 1.0e-6
SPAN = math.pi * D
M_STAR, K, C_A = 2.4, 29.15, 1.0
HEADER = "FoamFile {{ version 2.0; format ascii; class {cls}; object {obj}; }}\n\n"


def write(path, cls, obj, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER.format(cls=cls, obj=obj) + body)


def block_mesh(n_tan=36, n_rad=34, n_up=30, n_down=90, n_side=30, n_z=12, span_type="symmetry"):
    r, a = D / 2, 2 * D                                # cylinder radius, half-side of the O-grid square
    xs, ys = [-12 * D, -a, a, 20 * D], [-12 * D, -a, a, 12 * D]
    pts = [(x, y) for y in ys for x in xs]               # 16 square points, index 4*j + i
    s = r / math.sqrt(2)
    pts += [(-s, -s), (s, -s), (s, s), (-s, s)]          # circle points 16..19
    nv = len(pts)
    verts = "\n".join(f"    ({x:.8g} {y:.8g} {z:.8g})" for z in (0, SPAN) for x, y in pts)
    S = lambda i, j: 4 * j + i
    hexes = []

    def hexa(q, n1, n2, g1, g2):
        hexes.append(f"    hex ({' '.join(map(str, q))} {' '.join(str(v + nv) for v in q)}) "
                     f"({n1} {n2} {n_z}) simpleGrading ({g1} {g2} 1)")

    # O-grid around the cylinder: direction 1 tangential, direction 2 from the square to the wall
    g_wall = 0.04
    hexa([S(1, 1), S(2, 1), 17, 16], n_tan, n_rad, 1, g_wall)
    hexa([S(2, 1), S(2, 2), 18, 17], n_tan, n_rad, 1, g_wall)
    hexa([S(2, 2), S(1, 2), 19, 18], n_tan, n_rad, 1, g_wall)
    hexa([S(1, 2), S(1, 1), 16, 19], n_tan, n_rad, 1, g_wall)
    # outer blocks
    nx, gx = [n_up, n_tan, n_down], [0.12, 1, 6]
    ny, gy = [n_side, n_tan, n_side], [0.12, 1, 1 / 0.12]
    for j in range(3):
        for i in range(3):
            if (i, j) != (1, 1):
                hexa([S(i, j), S(i + 1, j), S(i + 1, j + 1), S(i, j + 1)], nx[i], ny[j], gx[i], gy[j])
    arcs = []
    for z in (0, nv):
        for a_, b_, (mx, my) in ((16, 17, (0, -r)), (17, 18, (r, 0)), (18, 19, (0, r)), (19, 16, (-r, 0))):
            arcs.append(f"    arc {a_ + z} {b_ + z} ({mx} {my} {SPAN if z else 0})")
    face = lambda q, up=False: "(" + " ".join(str(v + (nv if up else 0)) for v in q) + ")"
    side = lambda a_, b_: f"({a_} {b_} {b_ + nv} {a_ + nv})"
    boundary = f"""
    inlet    {{ type patch; faces ({side(S(0, 1), S(0, 0))} {side(S(0, 2), S(0, 1))} {side(S(0, 3), S(0, 2))}); }}
    outlet   {{ type patch; faces ({side(S(3, 0), S(3, 1))} {side(S(3, 1), S(3, 2))} {side(S(3, 2), S(3, 3))}); }}
    bottom   {{ type symmetry; faces ({side(S(0, 0), S(1, 0))} {side(S(1, 0), S(2, 0))} {side(S(2, 0), S(3, 0))}); }}
    top      {{ type symmetry; faces ({side(S(1, 3), S(0, 3))} {side(S(2, 3), S(1, 3))} {side(S(3, 3), S(2, 3))}); }}
    cylinder {{ type wall; faces ({side(17, 16)} {side(18, 17)} {side(19, 18)} {side(16, 19)}); }}
    front    {{ type {span_type}; faces ({' '.join(face(h, True) for h in _quads(S))}); }}
    back     {{ type {span_type}; faces ({' '.join(face(h[::-1]) for h in _quads(S))}); }}
"""
    return f"""scale 1;

vertices
(
{verts}
);

blocks
(
{chr(10).join(hexes)}
);

edges
(
{chr(10).join(arcs)}
);

boundary
({boundary});
"""


def _quads(S):
    quads = [[S(1, 1), S(2, 1), 17, 16], [S(2, 1), S(2, 2), 18, 17], [S(2, 2), S(1, 2), 19, 18], [S(1, 2), S(1, 1), 16, 19]]
    quads += [[S(i, j), S(i + 1, j), S(i + 1, j + 1), S(i, j + 1)] for j in range(3) for i in range(3) if (i, j) != (1, 1)]
    return quads


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case", type=Path)
    p.add_argument("--vstar", type=float, default=7.0)
    p.add_argument("--zeta", type=float, default=0.0125)
    p.add_argument("--periods", type=float, default=15)
    p.add_argument("--keep", type=int, default=8, help="number of written times kept (purgeWrite)")
    p.add_argument("--two-d", action="store_true", help="one cell across the span (empty front/back)")
    a = p.parse_args()

    mass = M_STAR * RHO * math.pi * D**2 * SPAN / 4
    f_n = math.sqrt(K / mass) / (2 * math.pi)
    f_nw = f_n * math.sqrt(M_STAR / (M_STAR + C_A))
    U = a.vstar * f_nw * D
    damping = 2 * a.zeta * math.sqrt(K * mass)
    dt = 1 / f_nw / 200
    end = a.periods / f_nw
    k_in = 1.5 * (0.01 * U) ** 2
    omega_in = math.sqrt(k_in) / (0.09**0.25 * 0.1 * D)
    zc = SPAN / 2
    c = a.case
    print(f"m = {mass:.3f} kg, f_n = {f_n:.3f} Hz, f_n,w = {f_nw:.3f} Hz, U = {U:.4f} m/s, "
          f"Re = {U * D / NU:.0f}, c = {damping:.4f} N s/m, dt = {dt:.5f} s, end = {end:.2f} s")

    write(c / "system/blockMeshDict", "dictionary", "blockMeshDict",
          block_mesh(n_z=1, span_type="empty") if a.two_d else block_mesh())
    write(c / "system/controlDict", "dictionary", "controlDict", f"""application pimpleFoam;
startFrom latestTime; startTime 0; stopAt endTime; endTime {end:.6g};
deltaT {dt:.6g}; writeControl adjustable; writeInterval {round(4 / f_nw / 16, 4)};
purgeWrite {a.keep}; writeFormat binary; writePrecision 8; timeFormat general; timePrecision 6;
runTimeModifiable yes; adjustTimeStep no;

functions
{{
    forces
    {{
        type forceCoeffs; libs (forces); writeControl timeStep; writeInterval 1;
        patches (cylinder); rho rhoInf; rhoInf {RHO}; CofR (0 0 {zc});
        liftDir (0 1 0); dragDir (1 0 0); pitchAxis (0 0 1);
        magUInf {U:.6g}; lRef {D}; Aref {D * SPAN:.6g};
    }}
}}
""")
    write(c / "system/fvSchemes", "dictionary", "fvSchemes", """ddtSchemes { default backward; }
gradSchemes { default Gauss linear; grad(U) cellLimited Gauss linear 1; }
divSchemes
{
    default none;
    div(phi,U) Gauss linearUpwind grad(U);
    div(phi,k) Gauss limitedLinear 1;
    div(phi,omega) Gauss limitedLinear 1;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
""")
    write(c / "system/fvSolution", "dictionary", "fvSolution", """solvers
{
    "(p|pcorr)" { solver PCG; preconditioner DIC; tolerance 1e-6; relTol 0.05; }
    "(p|pcorr)Final" { $p; relTol 0; }
    "(U|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0.1; }
    "(U|k|omega)Final" { $U; relTol 0; }
}
PIMPLE
{
    momentumPredictor yes; nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 1;
    correctPhi yes; moveMeshOuterCorrectors yes;
}
relaxationFactors { equations { ".*" 1; } }
""")
    write(c / "system/decomposeParDict", "dictionary", "decomposeParDict",
          "numberOfSubdomains 4;\nmethod scotch;\n")
    write(c / "constant/transportProperties", "dictionary", "transportProperties",
          f"transportModel Newtonian;\nnu {NU};\n")
    write(c / "constant/turbulenceProperties", "dictionary", "turbulenceProperties",
          "simulationType RAS;\nRAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }\n")
    write(c / "constant/dynamicMeshDict", "dictionary", "dynamicMeshDict", f"""dynamicFvMesh dynamicMotionSolverFvMesh;
motionSolverLibs (sixDoFRigidBodyMotion);
motionSolver sixDoFRigidBodyMotion;

sixDoFRigidBodyMotionCoeffs
{{
    patches (cylinder);
    innerDistance {1.5 * D};          // rigid ring around the cylinder
    outerDistance {10 * D};           // mesh deformation absorbed between the two
    centreOfMass (0 0 {zc:.8g});
    mass {mass:.8g};
    momentOfInertia (1 1 1);
    rho rhoInf;
    rhoInf {RHO};
    velocity (0 0.02 0);              // small kick to start the shedding
    report on;
    accelerationRelaxation 0.7;
    solver {{ type Newmark; }}

    constraints
    {{
        crossFlowOnly {{ sixDoFRigidBodyMotionConstraint line; direction (0 1 0); }}
        noRotation    {{ sixDoFRigidBodyMotionConstraint orientation; }}
    }}
    restraints
    {{
        springDamper
        {{
            sixDoFRigidBodyMotionRestraint linearSpring;
            anchor (0 0 {zc:.8g});
            refAttachmentPt (0 0 {zc:.8g});
            stiffness {K};
            damping {damping:.8g};
            restLength 0;
        }}
    }}
}}
""")
    sym = '    "(top|bottom|front|back)" { type symmetry; }\n'
    if a.two_d:
        sym = '    "(top|bottom)" { type symmetry; }\n    "(front|back)" { type empty; }\n'
    write(c / "0.orig/U", "volVectorField", "U", f"""dimensions [0 1 -1 0 0 0 0];
internalField uniform ({U:.6g} 0 0);
boundaryField
{{
    inlet {{ type fixedValue; value $internalField; }}
    outlet {{ type inletOutlet; inletValue uniform (0 0 0); value $internalField; }}
    cylinder {{ type movingWallVelocity; value uniform (0 0 0); }}
{sym}}}
""")
    write(c / "0.orig/p", "volScalarField", "p", f"""dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    inlet {{ type zeroGradient; }}
    outlet {{ type fixedValue; value uniform 0; }}
    cylinder {{ type zeroGradient; }}
{sym}}}
""")
    for name, dims, val, wall in (("k", "[0 2 -2 0 0 0 0]", k_in, "kqRWallFunction"),
                                  ("omega", "[0 0 -1 0 0 0 0]", omega_in, "omegaWallFunction")):
        write(c / f"0.orig/{name}", "volScalarField", name, f"""dimensions {dims};
internalField uniform {val:.6g};
boundaryField
{{
    inlet {{ type fixedValue; value $internalField; }}
    outlet {{ type inletOutlet; inletValue $internalField; value $internalField; }}
    cylinder {{ type {wall}; value $internalField; }}
{sym}}}
""")
    write(c / "0.orig/nut", "volScalarField", "nut", f"""dimensions [0 2 -1 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    inlet {{ type calculated; value uniform 0; }}
    outlet {{ type calculated; value uniform 0; }}
    cylinder {{ type nutUSpaldingWallFunction; value uniform 0; }}
{sym}}}
""")
    write(c / "0.orig/pointDisplacement", "pointVectorField", "pointDisplacement", f"""dimensions [0 1 0 0 0 0 0];
internalField uniform (0 0 0);
boundaryField
{{
    "(inlet|outlet)" {{ type fixedValue; value uniform (0 0 0); }}
    cylinder {{ type calculated; value uniform (0 0 0); }}
{sym}}}
""")
    import json
    (c / "case.json").write_text(json.dumps({"vstar": a.vstar, "zeta": a.zeta, "U": U, "Re": U * D / NU,
                                             "mass": mass, "f_nw": f_nw, "damping": damping}, indent=1))
    (c / "Allrun").write_text("""#!/bin/sh
cd "${0%/*}" || exit 1
. ${WM_PROJECT_DIR:?}/bin/tools/RunFunctions
rm -rf 0 && cp -r 0.orig 0
runApplication blockMesh
runApplication checkMesh
runApplication decomposePar
runParallel pimpleFoam
""")
    (c / "Allrun").chmod(0o755)


if __name__ == "__main__":
    main()
