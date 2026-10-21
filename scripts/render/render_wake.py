"""ParaView (pvpython) render of the vortex wake behind the elastically mounted cylinder.

Usage: pvpython render_wake.py <case dir> <time> <output png> [width height]

The run is two-dimensional (one cell across the span pi*D), so the Q-criterion
iso-surfaces are uniform along the cylinder: they show the 2D wake across the
simulated span. Colour: spanwise vorticity omega_z D / U with Crameri's "vik"
(blue clockwise, red anticlockwise). A translucent plane at the back of the
span shows the same vorticity field (from 2D upstream of the cylinder to the outlet, 20D downstream).
"""
import json
import sys
from pathlib import Path

from paraview.simple import (CellDatatoPointData, Clip, ColorBy, Contour, ExtractBlock, GetActiveViewOrCreate,
                             GetColorTransferFunction, Gradient, OpenFOAMReader, Plane, ResampleWithDataset,
                             SaveScreenshot, Show)

case, time, out = Path(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3])
width, height = (int(a) for a in (sys.argv[4:6] if len(sys.argv) > 5 else (2400, 1600)))
HERE = Path(__file__).resolve().parent
D = 0.05
SPAN = 3.141592653589793 * D
U = json.loads((case / "case.json").read_text())["U"]
Q_LEVEL = 0.6 * (U / D) ** 2          # Q iso-level, in units of (U/D)^2
W_RANGE = 3.0                         # colour range of omega_z D / U
X_RANGE, Y_HALF = (-2 * D, 20 * D), 5 * D   # region shown: from 2D upstream to the outlet
(case / "case.foam").touch()

reader = OpenFOAMReader(FileName=str(case / "case.foam"))
reader.MeshRegions = ["internalMesh", "patch/cylinder"]
reader.CellArrays = ["U"]
reader.UpdatePipeline(time)

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [width, height]
view.ViewTime = time
view.OrientationAxesVisibility = 0
view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
view.EnableRayTracing = 1
view.BackEnd = "OSPRay raycaster"
view.SamplesPerPixel = 32
view.AmbientSamples = 8

fluid = CellDatatoPointData(Input=ExtractBlock(Input=reader, Selectors=["/Root/internalMesh"]))
grad = Gradient(Input=fluid)
grad.ScalarArray = ["POINTS", "U"]
grad.ComputeQCriterion = 1
grad.QCriterionArrayName = "Q"
grad.ComputeVorticity = 1
grad.VorticityArrayName = "omega"

lut = GetColorTransferFunction("omega")
lut.RGBPoints = json.loads((HERE / "vik.json").read_text())["vik"]
lut.ColorSpace = "RGB"
lut.VectorMode = "Component"
lut.VectorComponent = 2
lut.AutomaticRescaleRangeMode = "Never"


def colour(display, opacity=1.0):
    ColorBy(display, ("POINTS", "omega", "Z"))
    display.LookupTable = lut
    display.SetScalarBarVisibility(view, False)
    display.Opacity = opacity


# vortex cores
near = Clip(Input=grad, ClipType="Box", Crinkleclip=0)
near.ClipType.Position = [X_RANGE[0], -Y_HALF, -0.01]
near.ClipType.Length = [X_RANGE[1] - X_RANGE[0], 2 * Y_HALF, SPAN + 0.02]
near.Invert = 1
q = Contour(Input=near, ContourBy=["POINTS", "Q"], Isosurfaces=[Q_LEVEL], ComputeScalars=0)
q.PointMergeMethod = "Uniform Binning"
d = Show(q, view)
colour(d)
d.Specular, d.SpecularPower = 0.35, 30

# vorticity on the back of the span, faint
back = ResampleWithDataset(SourceDataArrays=grad, DestinationMesh=Plane(
    Origin=[X_RANGE[0], -Y_HALF, 0.002 * SPAN], Point1=[X_RANGE[1], -Y_HALF, 0.002 * SPAN],
    Point2=[X_RANGE[0], Y_HALF, 0.002 * SPAN], XResolution=900, YResolution=400))
back.CellLocator = "Static Cell Locator"
d = Show(back, view)
colour(d, 0.45)
d.Ambient, d.Diffuse = 0.4, 0.6

# cylinder
cyl = ExtractBlock(Input=reader, Selectors=["/Root/boundary/cylinder"])
d = Show(cyl, view)
d.ColorArrayName = ["POINTS", ""]
d.AmbientColor = d.DiffuseColor = [0.72, 0.74, 0.76]
d.Specular, d.SpecularPower = 0.6, 40

lut.RescaleTransferFunction(-W_RANGE * U / D, W_RANGE * U / D)

view.CameraPosition = [-0.62, 0.70, 1.50]
view.CameraFocalPoint = [0.45, 0.0, SPAN / 2]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
SaveScreenshot(str(out), view, ImageResolution=[width, height], TransparentBackground=0)
print(out)
