"""
mandelbrot_fractal_tool.py - prototype
IMD 3002 - Will Richards
Maya Python script: Mandelbrot Fractal Embedding Tool

Provides a GUI-driven tool to:
  - Validate a face selection (shared normal, contiguous, manifold-safe)
  - Render a Mandelbrot fractal outline onto valid face bounds
  - Display an "onion-sketch" overlay showing the effect before any actual transformations
  - Lay the foundation for future extrusion / embedding and colorization

Not yet implemented (stubs provided):
  - extrudePath()   -- extrude fractal geometry by z-value
  - embedPath()     -- embed fractal geometry by z-value
  - colorFractal()  -- apply gradient lambert material to affected faces

BUGS FIXED vs previous prototype
---------------------------------
1. extract_boundary_points() used  center.x / u_axis.x  (OpenMaya MPoint/MVector
   attribute access) — bounds values are now plain tuples so index access is used.
2. createOnion() used  normal.x / normal.y / normal.z  for the same reason —
   fixed to normal[0], normal[1], normal[2].
3. polyInfo faceToVertex parsing was fragile — replaced with
   cmds.polyListComponentConversion which is more reliable across Maya versions.
4. validSelection() polyInfo normal parsing now handles Maya's inconsistent
   whitespace / colon formatting by splitting on whitespace and taking the last
   three tokens instead of fixed indices.
"""

import maya.cmds as cmds
import math


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WINDOW_ID    = "mandelbrotFractalTool"
WINDOW_TITLE = "Mandelbrot Fractal Tool"

DEFAULT_MAX_ITER   = 64
DEFAULT_RESOLUTION = 48   # samples per axis when building the outline
DEFAULT_Z_VALUE    = 0.2  # default extrusion / embedding depth (world units)

ONION_GROUP = "mandelbrot_onion_grp"


# ---------------------------------------------------------------------------
# Pure-Python vector helpers  (no OpenMaya dependency)
# ---------------------------------------------------------------------------

def _vec_normalize(v):
    x, y, z = v
    mag = math.sqrt(x*x + y*y + z*z)
    if mag < 1e-10:
        raise ValueError("Cannot normalise a zero-length vector.")
    return (x/mag, y/mag, z/mag)

def _vec_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _vec_cross(a, b):
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )


# ===========================================================================
# SECTION 1 — SELECTION VALIDATION
# ===========================================================================

def _face_normal_world(mesh, face_idx):
    """
    Return the world-space face normal for *face_idx* on *mesh* as a
    normalised 3-tuple.

    cmds.polyInfo returns strings like:
        "FACE_NORMAL      5: 0.000000 1.000000 0.000000\n"
    Splitting on whitespace and taking the last three tokens is robust to
    the variable amounts of whitespace Maya uses.
    """
    info   = cmds.polyInfo("{}.f[{}]".format(mesh, face_idx), faceNormals=True)
    tokens = info[0].split()
    nx, ny, nz = float(tokens[-3]), float(tokens[-2]), float(tokens[-1])
    return _vec_normalize((nx, ny, nz))


def validSelection(faces):
    """
    Validate that *faces* form a usable surface for fractal projection.

    Checks
    ------
    - At least one polygon face must be selected.
    - All faces must belong to the same mesh.
    - All face normals must be approximately parallel (dot >= 0.98, ~11 deg).

    Returns (True, poly_faces, referenceNormal) on success.
    Raises RuntimeError with a human-readable message on failure.
    """
    if not faces:
        raise RuntimeError("No faces selected. Please select one or more mesh faces.")

    poly_faces = [f for f in faces if ".f[" in f]
    if not poly_faces:
        raise RuntimeError("Selection contains no polygon faces.")

    meshes = set(f.split(".f[")[0] for f in poly_faces)
    if len(meshes) > 1:
        raise RuntimeError(
            "Selected faces span multiple meshes: {}. "
            "Please select faces from a single mesh.".format(", ".join(sorted(meshes)))
        )

    mesh = list(meshes)[0]

    normals = []
    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        normals.append(_face_normal_world(mesh, idx))

    ref           = normals[0]
    DOT_THRESHOLD = 0.98  # ~11 degrees tolerance

    for i, n in enumerate(normals[1:], 1):
        dot = _vec_dot(ref, n)
        if dot < DOT_THRESHOLD:
            raise RuntimeError(
                "Face normals diverge too much (face index {} vs face 0, "
                "dot={:.3f}). Select only co-planar / parallel faces.".format(i, dot)
            )

    return True, poly_faces, ref


# ===========================================================================
# SECTION 2 — BOUNDS
# ===========================================================================

def _face_vertex_positions(mesh, face_idx):
    """
    Return a list of world-space (x, y, z) tuples for every vertex that
    belongs to *face_idx* on *mesh*.

    Uses cmds.polyListComponentConversion — more reliable than parsing
    the raw polyInfo faceToVertex string.
    """
    face_comp  = "{}.f[{}]".format(mesh, face_idx)
    vert_comps = cmds.polyListComponentConversion(face_comp, toVertex=True)
    vert_comps = cmds.ls(vert_comps, flatten=True)
    positions  = []
    for vc in vert_comps:
        pos = cmds.xform(vc, query=True, worldSpace=True, translation=True)
        positions.append(tuple(pos))
    return positions


def getBounds(faces):
    """
    Compute the world-space bounding box of *faces* projected onto the
    plane defined by the shared face normal.

    Returns
    -------
    dict with keys:
        mesh    : str
        normal  : (nx, ny, nz)      -- world-space face normal (unit vector)
        center  : (cx, cy, cz)      -- centroid of all selected-face verts
        u_axis  : (ux, uy, uz)      -- local X on the face plane (unit vector)
        v_axis  : (vx, vy, vz)      -- local Y on the face plane (unit vector)
        width   : float             -- extent along u_axis
        height  : float             -- extent along v_axis
        verts   : [(x,y,z), ...]    -- all unique corner vert positions
    """
    _valid, poly_faces, normal = validSelection(faces)

    mesh = poly_faces[0].split(".f[")[0]

    # Collect unique vertex world positions across all selected faces
    seen      = set()
    world_pts = []
    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        for pt in _face_vertex_positions(mesh, idx):
            key = (round(pt[0], 6), round(pt[1], 6), round(pt[2], 6))
            if key not in seen:
                seen.add(key)
                world_pts.append(pt)

    # Build a local UV frame on the face plane
    world_up = (0.0, 1.0, 0.0)
    if abs(_vec_dot(normal, world_up)) > 0.99:
        world_up = (1.0, 0.0, 0.0)
    u_axis = _vec_normalize(_vec_cross(world_up, normal))
    v_axis = _vec_normalize(_vec_cross(normal, u_axis))

    # Centroid
    n_pts = len(world_pts)
    cx = sum(p[0] for p in world_pts) / n_pts
    cy = sum(p[1] for p in world_pts) / n_pts
    cz = sum(p[2] for p in world_pts) / n_pts
    center = (cx, cy, cz)

    # Project verts onto UV plane to get 2-D extents
    us = [_vec_dot((p[0]-cx, p[1]-cy, p[2]-cz), u_axis) for p in world_pts]
    vs = [_vec_dot((p[0]-cx, p[1]-cy, p[2]-cz), v_axis) for p in world_pts]

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

    Returns a 2-D list  grid[row][col] = iteration_count  (0 to max_iter).
    """
    grid  = []
    x_min, x_max = -2.5,  1.0
    y_min, y_max = -1.25, 1.25

    for row in range(resolution):
        v        = y_min + (y_max - y_min) * row / (resolution - 1)
        grid_row = []
        for col in range(resolution):
            u = x_min + (x_max - x_min) * col / (resolution - 1)
            grid_row.append(mandelbrot_iter(u, v, max_iter))
        grid.append(grid_row)
    return grid


def extract_boundary_points(grid, max_iter, resolution, bounds):
    """
    Walk the Mandelbrot grid and collect world-space 3-D points that lie on
    the boundary between inside-set (iter == max_iter) and outside-set cells.

    A cell is a boundary cell if it is inside the set AND has at least one
    4-neighbour that is outside the set (or the cell is at the grid edge).

    Points are mapped from normalised UV space into world space using the
    coordinate frame stored in *bounds*.

    Returns a list of (x, y, z) tuples.
    """
    # FIX: bounds values are plain tuples -- use index access, not .x/.y/.z
    cx, cy, cz = bounds["center"]
    ux, uy, uz = bounds["u_axis"]
    vx, vy, vz = bounds["v_axis"]
    width       = bounds["width"]
    height      = bounds["height"]

    boundary = []
    for row in range(resolution):
        for col in range(resolution):
            if grid[row][col] < max_iter:
                continue  # outside the set -- skip

            is_boundary = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < resolution and 0 <= nc < resolution:
                    if grid[nr][nc] < max_iter:
                        is_boundary = True
                        break
                else:
                    is_boundary = True  # grid edge counts as boundary
                    break

            if not is_boundary:
                continue

            u_norm = col / (resolution - 1)  # [0, 1]
            v_norm = row / (resolution - 1)  # [0, 1]

            u_off = (u_norm - 0.5) * width
            v_off = (v_norm - 0.5) * height

            wx = cx + ux * u_off + vx * v_off
            wy = cy + uy * u_off + vy * v_off
            wz = cz + uz * u_off + vz * v_off

            boundary.append((wx, wy, wz))

    return boundary


# ===========================================================================
# SECTION 4 — RENDER PATH
# ===========================================================================

def renderPath(bounds, resolution=DEFAULT_RESOLUTION, max_iter=DEFAULT_MAX_ITER):
    """
    Compute the world-space boundary points of the Mandelbrot fractal as it
    would be projected onto the selected face bounds.

    Parameters
    ----------
    bounds     : dict returned by getBounds()
    resolution : int  -- grid sample density (higher = finer detail, slower)
    max_iter   : int  -- Mandelbrot iteration depth (higher = sharper edge)

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
    Place a locator at every Mandelbrot boundary point, offset by *z_value*
    along the face normal, previewing fractal shape and depth before any
    geometry is modified.

    All locators are grouped under ONION_GROUP and placed on a Template
    display layer so they appear ghosted over the mesh.

    Parameters
    ----------
    boundary_points : list of (x, y, z)  -- from renderPath()
    bounds          : dict               -- from getBounds()
    z_value         : float              -- preview offset along face normal
    """
    _delete_onion()

    if not boundary_points:
        cmds.warning("[Mandelbrot] No boundary points to display.")
        return

    # FIX: normal is a plain 3-tuple -- use index access, not .x / .y / .z
    nx, ny, nz = bounds["normal"]

    grp      = cmds.group(empty=True, name=ONION_GROUP)
    locators = []

    for (wx, wy, wz) in boundary_points:
        ox = wx + nx * z_value
        oy = wy + ny * z_value
        oz = wz + nz * z_value

        loc = cmds.spaceLocator()[0]
        cmds.move(ox, oy, oz, loc, absolute=True)
        cmds.scale(0.02, 0.02, 0.02, loc)
        locators.append(loc)

    if locators:
        cmds.parent(locators, grp)

    layer_name = "mandelbrot_onion_layer"
    if not cmds.objExists(layer_name):
        cmds.createDisplayLayer(name=layer_name, empty=True)
    cmds.editDisplayLayerMembers(layer_name, grp, noRecurse=True)
    cmds.setAttr("{}.displayType".format(layer_name), 1)  # 1 = Template (ghost)

    cmds.select(clear=True)
    print("[Mandelbrot] Onion sketch: {} points, z_offset={:.4f}.".format(
        len(boundary_points), z_value))
    return grp


# ===========================================================================
# SECTION 6 — FUTURE STUBS
# ===========================================================================

def extrudePath(boundary_points, bounds, z_value):
    """
    STUB -- Extrude Mandelbrot boundary geometry outward by z_value.

    Implementation plan
    -------------------
    1. Subdivide target face(s) to match the resolution grid density.
    2. Identify subdivided faces whose centres fall inside the Mandelbrot set.
    3. cmds.polyExtrudeFacet on those faces with localTranslate z = z_value.
    4. Return the affected face list for colorFractal().
    """
    raise NotImplementedError("extrudePath() is not yet implemented.")


def embedPath(boundary_points, bounds, z_value):
    """
    STUB -- Embed (push inward) Mandelbrot boundary geometry by z_value.

    Same pipeline as extrudePath() but z_value is negated before the
    polyExtrudeFacet call.
    """
    raise NotImplementedError("embedPath() is not yet implemented.")


def colorFractal(affected_faces, col1=(1, 0, 0), col2=(0, 1, 0)):
    """
    STUB -- Apply a gradient lambert material to *affected_faces*.

    Implementation plan
    -------------------
    1. cmds.shadingNode('lambert', asShader=True)
    2. Attach a ramp texture via place2dTexture -> ramp -> lambert.color.
    3. Set ramp entry colours to col1 / col2.
    4. cmds.sets / cmds.hyperShade to assign the shader to affected_faces.
    """
    raise NotImplementedError("colorFractal() is not yet implemented.")


# ===========================================================================
# SECTION 7 — GUI STATE
# ===========================================================================

class FractalToolState:
    """Mutable container for state shared across GUI callbacks."""
    bounds          = None   # dict  -- from getBounds()
    boundary_points = None   # list  -- from renderPath()
    valid           = False  # bool  -- did the last Check Selection pass?

_state = FractalToolState()


# ===========================================================================
# SECTION 8 — GUI CALLBACKS
# ===========================================================================

def _get_ui_values(widgets):
    """Read every GUI control and return a plain dict."""
    return {
        "resolution" : cmds.intSliderGrp  (widgets["resolution"], q=True, value=True),
        "max_iter"   : cmds.intSliderGrp  (widgets["max_iter"],   q=True, value=True),
        "z_value"    : cmds.floatSliderGrp(widgets["z_value"],    q=True, value=True),
        "color_on"   : cmds.checkBox      (widgets["color_on"],   q=True, value=True),
        "col1"       : cmds.colorSliderGrp(widgets["col1"],       q=True, rgbValue=True),
        "col2"       : cmds.colorSliderGrp(widgets["col2"],       q=True, rgbValue=True),
    }


def cb_check_selection(widgets, *_):
    """Validate selection -> compute bounds -> renderPath -> onion sketch."""
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
              label="Status: Valid selection -- computing fractal...",
              bgc=(0.5, 0.5, 0.2))
    cmds.refresh()

    pts = renderPath(bounds,
                     resolution=vals["resolution"],
                     max_iter=vals["max_iter"])

    _state.bounds          = bounds
    _state.boundary_points = pts
    _state.valid           = True

    createOnion(pts, bounds, z_value=vals["z_value"])

    cmds.text(widgets["status"], edit=True,
              label="Status: OK -- {} boundary pts | w={:.3f} h={:.3f}".format(
                  len(pts), bounds["width"], bounds["height"]),
              bgc=(0.2, 0.5, 0.2))


def cb_z_changed(widgets, *_):
    """Regenerate onion sketch whenever the z-slider moves."""
    if not _state.valid:
        return
    vals = _get_ui_values(widgets)
    createOnion(_state.boundary_points, _state.bounds, z_value=vals["z_value"])


def cb_extrude(widgets, *_):
    if not _state.valid:
        cmds.warning("[Mandelbrot] Run 'Check Selection' first.")
        return
    vals = _get_ui_values(widgets)
    try:
        extrudePath(_state.boundary_points, _state.bounds, vals["z_value"])
    except NotImplementedError as e:
        cmds.confirmDialog(title="Not Yet Implemented", message=str(e), button=["OK"])


def cb_embed(widgets, *_):
    if not _state.valid:
        cmds.warning("[Mandelbrot] Run 'Check Selection' first.")
        return
    vals = _get_ui_values(widgets)
    try:
        embedPath(_state.boundary_points, _state.bounds, -vals["z_value"])
    except NotImplementedError as e:
        cmds.confirmDialog(title="Not Yet Implemented", message=str(e), button=["OK"])


def cb_clear_onion(*_):
    _delete_onion()
    _state.valid           = False
    _state.bounds          = None
    _state.boundary_points = None


# ===========================================================================
# SECTION 9 — GUI CONSTRUCTION
# ===========================================================================

def build_gui():
    if cmds.window(WINDOW_ID, exists=True):
        cmds.deleteUI(WINDOW_ID)

    win = cmds.window(WINDOW_ID,
                      title=WINDOW_TITLE,
                      widthHeight=(340, 480),
                      sizeable=False,
                      resizeToFitChildren=True)

    widgets = {}

    cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=("both", 8))

    # Header
    cmds.separator(h=6, style="none")
    cmds.text(label="Mandelbrot Fractal Tool", font="boldLabelFont", align="center")
    cmds.text(label="IMD 3002 -- Will Richards", font="smallObliqueLabelFont", align="center")
    cmds.separator(h=8, style="in")

    # Fractal parameters
    cmds.frameLayout(label="Fractal Parameters", collapsable=True, collapse=False,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    widgets["resolution"] = cmds.intSliderGrp(
        label="Resolution  ", field=True,
        minValue=8, maxValue=128, value=DEFAULT_RESOLUTION,
        columnWidth=[(1, 90), (2, 50)],
        annotation="Grid samples per axis -- higher = finer fractal detail (slower)")
    widgets["max_iter"] = cmds.intSliderGrp(
        label="Max Iters  ", field=True,
        minValue=8, maxValue=256, value=DEFAULT_MAX_ITER,
        columnWidth=[(1, 90), (2, 50)],
        annotation="Mandelbrot iteration depth -- higher = sharper boundary (slower)")
    cmds.setParent("..")
    cmds.setParent("..")

    # Z-value / depth
    cmds.frameLayout(label="Extrusion / Embedding Depth", collapsable=True, collapse=False,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    widgets["z_value"] = cmds.floatSliderGrp(
        label="Z-Value  ", field=True,
        minValue=0.001, maxValue=2.0, value=DEFAULT_Z_VALUE, precision=3,
        columnWidth=[(1, 90), (2, 60)],
        annotation="Depth along face normal for extrusion / embedding",
        changeCommand=lambda *a: cb_z_changed(widgets, *a),
        dragCommand=lambda *a:   cb_z_changed(widgets, *a))
    cmds.setParent("..")
    cmds.setParent("..")

    # Color options (future -- collapsed by default)
    cmds.frameLayout(label="Color Options  (future)", collapsable=True, collapse=True,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    widgets["color_on"] = cmds.checkBox(
        label="Apply gradient color after extrude/embed",
        value=False,
        annotation="Enables colorFractal() -- not yet implemented")
    widgets["col1"] = cmds.colorSliderGrp(
        label="Color 1  ", rgb=(0.5, 0.5, 0.5),
        columnWidth=[(1, 70)],
        annotation="Gradient start color")
    widgets["col2"] = cmds.colorSliderGrp(
        label="Color 2  ", rgb=(0.5, 0.5, 0.5),
        columnWidth=[(1, 70)],
        annotation="Gradient end color")
    cmds.setParent("..")
    cmds.setParent("..")

    # Action buttons
    cmds.separator(h=6, style="in")
    cmds.frameLayout(label="Actions", collapsable=False, marginHeight=6, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    cmds.button(
        label="Check Selection + Preview (Onion Sketch)",
        height=36, bgc=(0.25, 0.45, 0.65),
        command=lambda *a: cb_check_selection(widgets, *a),
        annotation="Validate face selection, compute Mandelbrot boundary, show onion overlay")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(148, 148), columnOffset2=(0, 4))
    cmds.button(
        label="Extrude  (stub)",
        height=30, bgc=(0.35, 0.55, 0.35),
        command=lambda *a: cb_extrude(widgets, *a),
        annotation="Extrude Mandelbrot geometry outward -- not yet implemented")
    cmds.button(
        label="Embed  (stub)",
        height=30, bgc=(0.55, 0.40, 0.35),
        command=lambda *a: cb_embed(widgets, *a),
        annotation="Embed Mandelbrot geometry inward -- not yet implemented")
    cmds.setParent("..")

    cmds.button(
        label="Clear Onion Sketch",
        height=24, bgc=(0.35, 0.35, 0.35),
        command=cb_clear_onion,
        annotation="Remove the onion-sketch preview geometry from the scene")

    cmds.setParent("..")
    cmds.setParent("..")

    # Status bar
    cmds.separator(h=4, style="none")
    widgets["status"] = cmds.text(
        label="Status: Select faces on a mesh, then click Check Selection.",
        align="left", wordWrap=True,
        bgc=(0.22, 0.22, 0.22),
        font="smallPlainLabelFont",
        height=36)
    cmds.separator(h=6, style="none")
    cmds.setParent("..")

    cmds.showWindow(win)
    return win


# ===========================================================================
# SECTION 10 — ENTRY POINT
# ===========================================================================

def run():
    """Open the Mandelbrot Fractal Tool window."""
    build_gui()
    print("[Mandelbrot] Tool opened.")


# Run from the Maya Script Editor:
#   import mandelbrot_fractal_tool; mandelbrot_fractal_tool.run()
# or paste the entire file and press Run.
if __name__ == "__main__":
    run()