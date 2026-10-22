"""ParaView (pvpython) render of the cylinder vortex wake in the OpenONDA style.

Usage: pvpython render_wake.py <case dir> <time> <output png> [width height]

Black background. Q-criterion iso-surfaces (vortex cores) and a plane behind
the span are coloured by spanwise vorticity omega_z D/U with signed_dark:
blue clockwise, red anticlockwise, zero fading into the black. The cylinder
is brushed metal. The run is two-dimensional, so the cores are uniform along
the span. render_animation.py uses scene() for its frames.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from paraview.simple import (Calculator, CellDatatoPointData, Clip, Contour, Cylinder, Disk, ExtractBlock, Transform,  # noqa: E402
                             Gradient, OpenFOAMReader, Plane, ResampleWithDataset, Show)

D, SPAN = 0.05, 3.141592653589793 * 0.05
W_RANGE = 4.0                                   # colour range of omega_z D / U
Q_LEVEL = 0.6                                   # Q iso-level in units of (U/D)^2
X_RANGE, Y_HALF = (-2 * D, 20 * D), 5 * D
CAMERA = dict(CameraPosition=[-0.40, 0.42, 1.04], CameraFocalPoint=[0.40, -0.03, SPAN / 2], CameraViewUp=[0, 1, 0],
              CameraViewAngle=30)


def scene(case, width, height):
    """Build the wake scene; returns the view and set_time(t), which moves the scene to time t
    (the cylinder, and the clip that keeps its boundary layer out, follow its motion)."""
    U = json.loads((case / "case.json").read_text())["U"]
    (case / "case.foam").touch()
    reader = OpenFOAMReader(FileName=str(case / "case.foam"))
    reader.MeshRegions = ["internalMesh", "patch/cylinder"]
    reader.CellArrays = ["U"]
    view = style.setup_view(width, height)

    fluid = CellDatatoPointData(Input=ExtractBlock(Input=reader, Selectors=["/Root/internalMesh"]))
    grad = Gradient(Input=fluid)
    grad.ScalarArray = ["POINTS", "U"]
    grad.ComputeQCriterion = 1
    grad.QCriterionArrayName = "Q"
    grad.ComputeVorticity = 1
    grad.VorticityArrayName = "omega"
    nondim = Calculator(Input=grad, ResultArrayName="wz", Function=f"omega_Z*{D / U}")
    qn = Calculator(Input=nondim, ResultArrayName="qn", Function=f"Q*{(D / U) ** 2}")

    lut = style.lut("wz", "signed_dark", -W_RANGE, W_RANGE)

    near = Clip(Input=qn, ClipType="Box", Crinkleclip=0)
    near.ClipType.Position = [X_RANGE[0], -Y_HALF, -0.01]
    near.ClipType.Length = [X_RANGE[1] - X_RANGE[0], 2 * Y_HALF, SPAN + 0.02]
    near.Invert = 1
    # leave out the boundary-layer sheath within 1.1 D of the cylinder axis, so the cylinder shows
    cyl = ExtractBlock(Input=reader, Selectors=["/Root/boundary/cylinder"])
    away = Clip(Input=near, ClipType="Cylinder", Crinkleclip=0)
    away.ClipType.Axis = [0, 0, 1]
    away.ClipType.Radius = 1.1 * D
    away.Invert = 0
    cores = Contour(Input=away, ContourBy=["POINTS", "qn"], Isosurfaces=[Q_LEVEL], ComputeScalars=0)
    cores.PointMergeMethod = "Uniform Binning"
    d = Show(cores, view)
    style.mapped(d, "wz", lut, roughness=0.3)

    plane = Plane(Origin=[X_RANGE[0], -Y_HALF, 0.002 * SPAN], Point1=[X_RANGE[1], -Y_HALF, 0.002 * SPAN],
                  Point2=[X_RANGE[0], Y_HALF, 0.002 * SPAN], XResolution=900, YResolution=400)
    back = ResampleWithDataset(SourceDataArrays=nondim, DestinationMesh=plane)
    back.CellLocator = "Static Cell Locator"
    d = Show(back, view)
    style.mapped(d, "wz", lut)
    d.Interpolation = "Flat"
    d.Ambient, d.Diffuse = 1.0, 0.0                 # unlit: the field glows
    d.Opacity = 0.85

    # the cylinder patch has no end caps; draw a closed solid at the same position and size
    solid = Transform(Input=Cylinder(Radius=D / 2, Height=SPAN, Resolution=160, Capping=0))
    solid.Transform.Rotate = [90.0, 0.0, 0.0]                    # source axis y -> span axis z
    style.metal(solid, view, mapping="cylinder")
    caps = []
    for z in (0.0, SPAN):                                        # end caps: untextured, same metal
        cap = Transform(Input=Disk(InnerRadius=0.0, OuterRadius=D / 2, CircumferentialResolution=160))
        d = Show(cap, view)
        style.solid(d, [0.80, 0.81, 0.83], roughness=0.35)
        d.Metallic = 0.2
        caps.append((cap, z))
    lut.RescaleTransferFunction(-W_RANGE, W_RANGE)

    def set_time(time):
        view.ViewTime = time
        cyl.UpdatePipeline(time)
        b = cyl.GetDataInformation().GetBounds()
        centre = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2]
        away.ClipType.Center = centre + [0.0]
        solid.Transform.Translate = centre + [SPAN / 2]
        for cap, z in caps:
            cap.Transform.Translate = centre + [z]

    return view, set_time


if __name__ == "__main__":
    case, time, out = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
    width, height = (int(a) for a in (sys.argv[4:6] if len(sys.argv) > 5 else (3600, 2250)))
    view, set_time = scene(case, width, height)
    set_time(time)
    for key, value in CAMERA.items():
        setattr(view, key, value)
    style.save(view, out, width, height)
    print(out)
