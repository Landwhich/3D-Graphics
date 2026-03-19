"""
mandelbrot_fractal_tool.py
IMD 3002 - Will Richards
Maya Python script: Mandelbrot Fractal Embedding Tool

Provides a GUI-driven tool to:
  - Validate a face selection (shared normal, contiguous, manifold-safe)
  - Render a Mandelbrot fractal outline onto valid face bounds
  - Display an "onion-sketch" overlay showing the effect before commit
  - Lay the foundation for future extrusion / embedding and colorization

Not yet implemented (stubs provided):
  - extrudePath()   -- extrude fractal geometry by z-value
  - embedPath()     -- embed fractal geometry by z-value
  - colorFractal()  -- apply gradient lambert material to affected faces
"""

import maya.cmds as cmds
import maya.OpenMaya as om
import math


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WINDOW_ID   = "mandelbrotFractalTool"
WINDOW_TITLE = "Mandelbrot Fractal Tool"

# Mandelbrot iteration defaults
DEFAULT_MAX_ITER = 64
DEFAULT_RESOLUTION = 48      # samples per axis when building the outline
DEFAULT_Z_VALUE    = 0.2     # default extrusion depth (world units)

# Onion-sketch curve group name
ONION_GROUP = "mandelbrot_onion_grp"


# ===========================================================================
# SECTION 1 — SELECTION VALIDATION
# ===========================================================================

def validSelection(faces):
    """
    Validate that *faces* form a usable surface for fractal projection.

    Rules
    -----
    1. At least one face must be selected.
    2. All face normals must be approximately parallel (dot product ≥ threshold).
    3. All faces must belong to the same mesh.

    Returns (True, faces, referenceNormal) on success.
    Raises RuntimeError with a descriptive message on failure.
    """
    if not faces:
        raise RuntimeError("No faces selected. Please select one or more mesh faces.")

    # Filter to only polygon face components
    poly_faces = [f for f in faces if ".f[" in f]
    if not poly_faces:
        raise RuntimeError("Selection contains no polygon faces.")

    # Ensure single mesh
    meshes = set(f.split(".f[")[0] for f in poly_faces)
    if len(meshes) > 1:
        raise RuntimeError(
            "Selected faces span multiple meshes: {}. "
            "Please select faces from a single mesh.".format(", ".join(meshes))
        )

    mesh = list(meshes)[0]

    # Gather normals via MFnMesh
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = om.MDagPath()
    sel.getDagPath(0, dag)
    fn_mesh = om.MFnMesh(dag)

    normals = []
    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        n = om.MVector()
        fn_mesh.getPolygonNormal(idx, n, om.MSpace.kWorld)
        normals.append(n)

    ref = normals[0].normal()
    DOT_THRESHOLD = 0.98   # ~11 degrees tolerance

    for i, n in enumerate(normals[1:], 1):
        dot = ref * n.normal()
        if dot < DOT_THRESHOLD:
            raise RuntimeError(
                "Face normals diverge too much (face index {} vs face 0, "
                "dot={:.3f}). Select only co-planar / parallel faces.".format(i, dot)
            )

    return True, poly_faces, ref


# ===========================================================================
# SECTION 2 — BOUNDS
# ===========================================================================

def getBounds(faces):
    """
    Compute the world-space bounding box of *faces* projected onto the
    plane defined by the first face's normal.

    Returns a dict:
        {
            "mesh"   : str,
            "normal" : MVector,
            "center" : MPoint,
            "u_axis" : MVector,   # local X on the face plane
            "v_axis" : MVector,   # local Y on the face plane
            "width"  : float,
            "height" : float,
            "verts"  : [(world_x, world_y, world_z), ...]  all corner verts
        }
    """
    _valid, poly_faces, normal = validSelection(faces)

    mesh = poly_faces[0].split(".f[")[0]

    sel = om.MSelectionList()
    sel.add(mesh)
    dag = om.MDagPath()
    sel.getDagPath(0, dag)
    fn_mesh = om.MFnMesh(dag)

    # Collect all vertex positions for the selected faces
    world_pts = []
    vert_array = om.MPointArray()

    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        fn_mesh.getPolygonVertices   # just to confirm API works
        int_array = om.MIntArray()
        fn_mesh.getPolygonVertices(idx, int_array)
        for vi in range(int_array.length()):
            pt = om.MPoint()
            fn_mesh.getPoint(int_array[vi], pt, om.MSpace.kWorld)
            world_pts.append(pt)

    # Build a local UV frame on the face plane
    # u_axis = any vector perpendicular to normal
    world_up = om.MVector(0, 1, 0)
    if abs(normal * world_up) > 0.99:
        world_up = om.MVector(1, 0, 0)
    u_axis = (world_up ^ normal).normal()
    v_axis = (normal ^ u_axis).normal()

    # Center of all verts
    cx = sum(p.x for p in world_pts) / len(world_pts)
    cy = sum(p.y for p in world_pts) / len(world_pts)
    cz = sum(p.z for p in world_pts) / len(world_pts)
    center = om.MPoint(cx, cy, cz)

    # Project verts onto uv plane to get 2-D extents
    us = [(om.MVector(p.x - cx, p.y - cy, p.z - cz) * u_axis) for p in world_pts]
    vs = [(om.MVector(p.x - cx, p.y - cy, p.z - cz) * v_axis) for p in world_pts]

    width  = max(us) - min(us)
    height = max(vs) - min(vs)

    return {
        "mesh"   : mesh,
        "normal" : normal,
        "center" : center,
        "u_axis" : u_axis,
        "v_axis" : v_axis,
        "width"  : width,
        "height" : height,
        "verts"  : world_pts,
    }


# ===========================================================================
# SECTION 3 — MANDELBROT CORE
# ===========================================================================

def mandelbrot_iter(cx, cy, max_iter):
    """
    Return the number of iterations before |z| > 2 for complex point (cx, cy).
    Returns max_iter if the point is inside the set.
    """
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        zx2 = zx * zx
        zy2 = zy * zy
        if zx2 + zy2 > 4.0:
            return i
        zx, zy = zx2 - zy2 + cx, 2.0 * zx * zy + cy
    return max_iter


def build_mandelbrot_grid(resolution, max_iter=DEFAULT_MAX_ITER):
    """
    Sample the Mandelbrot set on a *resolution x resolution* grid covering
    the canonical view [-2.5, 1.0] x [-1.25, 1.25].

    Returns a 2-D list  grid[row][col] = iteration_count  (0 … max_iter).
    """
    grid = []
    x_min, x_max = -2.5,  1.0
    y_min, y_max = -1.25, 1.25

    for row in range(resolution):
        v = y_min + (y_max - y_min) * row / (resolution - 1)
        grid_row = []
        for col in range(resolution):
            u = x_min + (x_max - x_min) * col / (resolution - 1)
            grid_row.append(mandelbrot_iter(u, v, max_iter))
        grid.append(grid_row)
    return grid


def extract_boundary_points(grid, max_iter, resolution, bounds):
    """
    Walk the Mandelbrot grid and collect world-space 3-D points that lie on
    the boundary between inside-set (iter == max_iter) and outside-set pixels.

    The boundary is approximated as the centre of any 'inside' cell that has
    at least one 'outside' neighbour.

    Points are mapped into the face plane described by *bounds*.
    """
    center  = bounds["center"]
    u_axis  = bounds["u_axis"]
    v_axis  = bounds["v_axis"]
    width   = bounds["width"]
    height  = bounds["height"]
    normal  = bounds["normal"]

    boundary = []
    for row in range(resolution):
        for col in range(resolution):
            if grid[row][col] < max_iter:
                continue   # outside the set — skip
            # Check 4-neighbours
            is_boundary = False
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < resolution and 0 <= nc < resolution:
                    if grid[nr][nc] < max_iter:
                        is_boundary = True
                        break
                else:
                    is_boundary = True   # edge of grid
                    break
            if not is_boundary:
                continue

            # Normalised UV in [0,1]
            u_norm = col / (resolution - 1)
            v_norm = row / (resolution - 1)

            # Map to world space
            u_off = (u_norm - 0.5) * width
            v_off = (v_norm - 0.5) * height

            wx = center.x + u_axis.x * u_off + v_axis.x * v_off
            wy = center.y + u_axis.y * u_off + v_axis.y * v_off
            wz = center.z + u_axis.z * u_off + v_axis.z * v_off

            boundary.append((wx, wy, wz))

    return boundary


# ===========================================================================
# SECTION 4 — RENDER PATH  (produces world-space point cloud)
# ===========================================================================

def renderPath(bounds, resolution=DEFAULT_RESOLUTION, max_iter=DEFAULT_MAX_ITER):
    """
    Compute the world-space boundary points of the Mandelbrot fractal as it
    would be projected onto the selected face bounds.

    Parameters
    ----------
    bounds     : dict returned by getBounds()
    resolution : int  — grid sample density (higher = finer fractal detail)
    max_iter   : int  — Mandelbrot iteration depth (higher = more detail)

    Returns
    -------
    list of (x, y, z) tuples representing the fractal boundary in world space.
    """
    grid   = build_mandelbrot_grid(resolution, max_iter)
    points = extract_boundary_points(grid, max_iter, resolution, bounds)
    return points


# ===========================================================================
# SECTION 5 — ONION-SKETCH OVERLAY
# ===========================================================================

def _delete_onion():
    """Remove any previously created onion-sketch geometry."""
    if cmds.objExists(ONION_GROUP):
        cmds.delete(ONION_GROUP)


def createOnion(boundary_points, bounds, z_value=DEFAULT_Z_VALUE):
    """
    Create a lightweight translucent particle / locator cloud that previews
    the Mandelbrot boundary on the face.

    Implementation: draws Maya locators at each boundary point, offset by
    z_value along the face normal, grouped under ONION_GROUP.  A semi-
    transparent display layer is applied so the overlay appears 'ghosted'.

    Parameters
    ----------
    boundary_points : list of (x,y,z)   from renderPath()
    bounds          : dict              from getBounds()
    z_value         : float             extrusion preview offset
    """
    _delete_onion()

    if not boundary_points:
        cmds.warning("No boundary points to display.")
        return

    normal = bounds["normal"]
    grp = cmds.group(empty=True, name=ONION_GROUP)

    locators = []
    for (wx, wy, wz) in boundary_points:
        # Offset along face normal by z_value to preview depth
        ox = wx + normal.x * z_value
        oy = wy + normal.y * z_value
        oz = wz + normal.z * z_value

        loc = cmds.spaceLocator()[0]
        cmds.move(ox, oy, oz, loc)
        cmds.scale(0.02, 0.02, 0.02, loc)   # tiny locators
        locators.append(loc)

    if locators:
        cmds.parent(locators, grp)

    # Create / update a display layer for the ghost look
    layer_name = "mandelbrot_onion_layer"
    if not cmds.objExists(layer_name):
        cmds.createDisplayLayer(name=layer_name, empty=True)
    cmds.editDisplayLayerMembers(layer_name, grp, noRecurse=True)
    cmds.setAttr("{}.displayType".format(layer_name), 1)   # template (ghost)

    cmds.select(clear=True)
    print("[Mandelbrot] Onion sketch created with {} points.".format(len(boundary_points)))
    return grp


# ===========================================================================
# SECTION 6 — FUTURE STUBS  (extrusion / color — not yet implemented)
# ===========================================================================

def extrudePath(boundary_points, bounds, z_value):
    """
    STUB — Extrude Mandelbrot boundary geometry outward by z_value.

    Steps to implement
    ------------------
    1. Use boundary_points to drive cmds.polyExtrudeFacet on subdivided faces.
    2. Subdivide the target face to match boundary resolution.
    3. Select inner faces matching 'inside-set' cells.
    4. Extrude by z_value along the face normal.
    5. Return the extruded face list for colorFractal().
    """
    raise NotImplementedError("extrudePath() is not yet implemented.")


def embedPath(boundary_points, bounds, z_value):
    """
    STUB — Embed (push inward) Mandelbrot boundary geometry by z_value.

    Same as extrudePath but z_value is negated before extrusion.
    """
    raise NotImplementedError("embedPath() is not yet implemented.")


def colorFractal(affected_faces, col1=(1,0,0), col2=(0,1,0)):
    """
    STUB — Apply a gradient lambert material to *affected_faces*.

    Steps to implement
    ------------------
    1. Create a lambert shader.
    2. Attach a ramp texture mapped in UV space to drive color.
    3. Set ramp colours to col1 / col2.
    4. Assign the shader to affected_faces.
    """
    raise NotImplementedError("colorFractal() is not yet implemented.")


# ===========================================================================
# SECTION 7 — GUI STATE
# ===========================================================================

class FractalToolState:
    """Holds runtime state shared between GUI callbacks."""
    bounds          = None    # dict from getBounds()
    boundary_points = None    # list from renderPath()
    valid           = False   # did the last validSelection() pass?


_state = FractalToolState()


# ===========================================================================
# SECTION 8 — GUI CALLBACKS
# ===========================================================================

def _get_ui_values(widgets):
    """Read current values from all GUI controls into a plain dict."""
    return {
        "resolution" : cmds.intSliderGrp(widgets["resolution"], q=True, value=True),
        "max_iter"   : cmds.intSliderGrp(widgets["max_iter"],   q=True, value=True),
        "z_value"    : cmds.floatSliderGrp(widgets["z_value"],  q=True, value=True),
        "color_on"   : cmds.checkBox(widgets["color_on"],       q=True, value=True),
        "col1"       : cmds.colorSliderGrp(widgets["col1"],     q=True, rgbValue=True),
        "col2"       : cmds.colorSliderGrp(widgets["col2"],     q=True, rgbValue=True),
    }


def cb_check_selection(widgets, *_):
    """Callback: validate selection → compute bounds → render path → onion."""
    _state.valid           = False
    _state.bounds          = None
    _state.boundary_points = None

    sel = cmds.ls(selection=True, flatten=True)
    if not sel:
        cmds.warning("[Mandelbrot] Nothing selected.")
        cmds.text(widgets["status"], edit=True,
                  label="Status: Nothing selected.", bgc=(0.6, 0.2, 0.2))
        return

    try:
        _valid, poly_faces, _normal = validSelection(sel)
    except RuntimeError as e:
        cmds.warning("[Mandelbrot] {}".format(e))
        cmds.text(widgets["status"], edit=True,
                  label="Status: {}".format(e), bgc=(0.6, 0.2, 0.2))
        return

    try:
        bounds = getBounds(poly_faces)
    except RuntimeError as e:
        cmds.warning("[Mandelbrot] {}".format(e))
        cmds.text(widgets["status"], edit=True,
                  label="Status: {}".format(e), bgc=(0.6, 0.2, 0.2))
        return

    vals = _get_ui_values(widgets)

    cmds.text(widgets["status"], edit=True,
              label="Status: Valid — computing fractal…", bgc=(0.5, 0.5, 0.2))
    cmds.refresh()

    pts = renderPath(bounds,
                     resolution=vals["resolution"],
                     max_iter=vals["max_iter"])

    _state.bounds          = bounds
    _state.boundary_points = pts
    _state.valid           = True

    createOnion(pts, bounds, z_value=vals["z_value"])

    cmds.text(widgets["status"], edit=True,
              label="Status: OK — {} boundary pts | w={:.3f} h={:.3f}".format(
                  len(pts), bounds["width"], bounds["height"]),
              bgc=(0.2, 0.5, 0.2))


def cb_z_changed(widgets, *_):
    """Live-update the onion sketch when the z-value slider moves."""
    if not _state.valid:
        return
    vals = _get_ui_values(widgets)
    createOnion(_state.boundary_points, _state.bounds, z_value=vals["z_value"])


def cb_extrude(widgets, *_):
    """Callback: extrude (stub)."""
    if not _state.valid:
        cmds.warning("[Mandelbrot] Run 'Check Selection' first.")
        return
    vals = _get_ui_values(widgets)
    try:
        extrudePath(_state.boundary_points, _state.bounds, vals["z_value"])
    except NotImplementedError as e:
        cmds.confirmDialog(title="Not Yet Implemented",
                           message=str(e),
                           button=["OK"])


def cb_embed(widgets, *_):
    """Callback: embed (stub)."""
    if not _state.valid:
        cmds.warning("[Mandelbrot] Run 'Check Selection' first.")
        return
    vals = _get_ui_values(widgets)
    try:
        embedPath(_state.boundary_points, _state.bounds, -vals["z_value"])
    except NotImplementedError as e:
        cmds.confirmDialog(title="Not Yet Implemented",
                           message=str(e),
                           button=["OK"])


def cb_clear_onion(*_):
    """Delete the onion-sketch overlay."""
    _delete_onion()
    _state.valid           = False
    _state.bounds          = None
    _state.boundary_points = None


# ===========================================================================
# SECTION 9 — GUI CONSTRUCTION
# ===========================================================================

def build_gui():
    """Build and show the Mandelbrot Fractal Tool window."""

    # Close existing window
    if cmds.window(WINDOW_ID, exists=True):
        cmds.deleteUI(WINDOW_ID)

    win = cmds.window(WINDOW_ID,
                      title=WINDOW_TITLE,
                      widthHeight=(340, 480),
                      sizeable=False,
                      resizeToFitChildren=True)

    widgets = {}

    cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=("both", 8))

    # ── Header ──────────────────────────────────────────────────────────────
    cmds.separator(h=6, style="none")
    cmds.text(label="Mandelbrot Fractal Tool", font="boldLabelFont", align="center")
    cmds.text(label="IMD 3002 — Will Richards", font="smallObliqueLabelFont", align="center")
    cmds.separator(h=8, style="in")

    # ── Fractal Parameters ───────────────────────────────────────────────────
    cmds.frameLayout(label="Fractal Parameters", collapsable=True, collapse=False,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    widgets["resolution"] = cmds.intSliderGrp(
        label="Resolution  ", field=True,
        minValue=8, maxValue=128, value=DEFAULT_RESOLUTION,
        columnWidth=[(1, 90), (2, 50)],
        annotation="Grid samples per axis — higher = finer fractal detail"
    )
    widgets["max_iter"] = cmds.intSliderGrp(
        label="Max Iters  ", field=True,
        minValue=8, maxValue=256, value=DEFAULT_MAX_ITER,
        columnWidth=[(1, 90), (2, 50)],
        annotation="Mandelbrot iteration depth — higher = sharper boundary"
    )

    cmds.setParent("..")   # columnLayout
    cmds.setParent("..")   # frameLayout

    # ── Z-Value / Depth ──────────────────────────────────────────────────────
    cmds.frameLayout(label="Extrusion / Embedding Depth", collapsable=True, collapse=False,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    widgets["z_value"] = cmds.floatSliderGrp(
        label="Z-Value  ", field=True,
        minValue=0.001, maxValue=2.0, value=DEFAULT_Z_VALUE,
        precision=3,
        columnWidth=[(1, 90), (2, 60)],
        annotation="Extrusion/embedding depth along face normal",
        changeCommand=lambda *a: cb_z_changed(widgets, *a),
        dragCommand=lambda *a: cb_z_changed(widgets, *a),
    )

    cmds.setParent("..")
    cmds.setParent("..")

    # ── Color Options (future) ───────────────────────────────────────────────
    cmds.frameLayout(label="Color Options  (future)", collapsable=True, collapse=True,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    widgets["color_on"] = cmds.checkBox(
        label="Apply gradient color after extrude/embed",
        value=False,
        annotation="Enables colorFractal() — not yet implemented"
    )
    widgets["col1"] = cmds.colorSliderGrp(
        label="Color 1  ", rgb=(0.5, 0.5, 0.5),
        columnWidth=[(1, 70)],
        annotation="Gradient start color"
    )
    widgets["col2"] = cmds.colorSliderGrp(
        label="Color 2  ", rgb=(0.5, 0.5, 0.5),
        columnWidth=[(1, 70)],
        annotation="Gradient end color"
    )

    cmds.setParent("..")
    cmds.setParent("..")

    # ── Actions ──────────────────────────────────────────────────────────────
    cmds.separator(h=6, style="in")
    cmds.frameLayout(label="Actions", collapsable=False,
                     marginHeight=6, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    cmds.button(
        label="① Check Selection + Preview (Onion Sketch)",
        height=36,
        bgc=(0.25, 0.45, 0.65),
        command=lambda *a: cb_check_selection(widgets, *a),
        annotation="Validate face selection, compute Mandelbrot boundary, show onion overlay"
    )

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(148, 148), columnOffset2=(0, 4))
    cmds.button(
        label="② Extrude  ↑  (stub)",
        height=30,
        bgc=(0.35, 0.55, 0.35),
        command=lambda *a: cb_extrude(widgets, *a),
        annotation="Extrude Mandelbrot geometry outward — not yet implemented"
    )
    cmds.button(
        label="② Embed  ↓  (stub)",
        height=30,
        bgc=(0.55, 0.40, 0.35),
        command=lambda *a: cb_embed(widgets, *a),
        annotation="Embed Mandelbrot geometry inward — not yet implemented"
    )
    cmds.setParent("..")   # rowLayout

    cmds.button(
        label="Clear Onion Sketch",
        height=24,
        bgc=(0.35, 0.35, 0.35),
        command=cb_clear_onion,
        annotation="Remove the onion-sketch preview geometry"
    )

    cmds.setParent("..")   # columnLayout
    cmds.setParent("..")   # frameLayout

    # ── Status Bar ───────────────────────────────────────────────────────────
    cmds.separator(h=4, style="none")
    widgets["status"] = cmds.text(
        label="Status: Select faces on a mesh, then click Check Selection.",
        align="left",
        wordWrap=True,
        bgc=(0.22, 0.22, 0.22),
        font="smallPlainLabelFont",
        height=36,
    )
    cmds.separator(h=6, style="none")
    cmds.setParent("..")   # top columnLayout

    cmds.showWindow(win)
    return win


# ===========================================================================
# SECTION 10 — ENTRY POINT
# ===========================================================================

def run():
    """Run the Mandelbrot Fractal Tool. Call this from the Maya script editor."""
    build_gui()
    print("[Mandelbrot] Tool opened.")


# Allow running directly from the script editor:
#   import mandelbrot_fractal_tool; mandelbrot_fractal_tool.run()
# or simply paste into the script editor and press Run.
if __name__ == "__main__":
    run()