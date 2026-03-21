### mandelbrot_fractal_tool.py - prototype ###
### IMD 3002 - Will Richards ###

import maya.cmds as cmds
import math

# CONSTANTS

WINDOW_ID    = "mandelbrotFractalTool"
WINDOW_TITLE = "Mandelbrot Fractal Tool"

DEFAULT_MAX_ITER   = 64
DEFAULT_RESOLUTION = 48
DEFAULT_Z_VALUE    = 0.2

ONION_GROUP = "mandelbrot_onion_grp"

# VECTOR HELPERS

def _vec_normalize(v):
    x, y, z = v
    mag = math.sqrt(x*x + y*y + z*z)
    if mag < 1e-10:
        raise ValueError("Can't normalize a zero-length vector.")
    return (x/mag, y/mag, z/mag)

def _vec_dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _vec_cross(a, b):
    return (
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0],
    )

# 1- SELECTION VALIDATION

def _face_normal_world(mesh, face_idx):
    # Return world-space face normal as a normalised 3-tuple.
    data   = cmds.polyInfo("{}.f[{}]".format(mesh, face_idx), faceNormals=True)
    coords = data[0].split()
    nx, ny, nz = float(coords[-3]), float(coords[-2]), float(coords[-1])
    return _vec_normalize((nx, ny, nz))


def valid_selection(faces):
    """
    Validate that the selection is a usable surface for fractal projection.

    Checks:
    - >= 1 polygon face must be selected.
    - All faces must be in the same mesh.
    - All normals must be close to parallel

    Returns (True, poly_faces, referenceNormal) if succesful. 
    Has basic erro checking and raises said error on failure
    """
    if not faces:
        raise RuntimeError("No faces selected.")

    poly_faces = [f for f in faces if ".f[" in f]
    if not poly_faces:
        raise RuntimeError("Selection has no polygon faces.")

    meshes = set(f.split(".f[")[0] for f in poly_faces)
    if len(meshes) > 1:
        raise RuntimeError("Please select faces from a single mesh.")

    mesh = list(meshes)[0]

    normals = []
    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        normals.append(_face_normal_world(mesh, idx))

    ref = normals[0]
    DOT_THRESHOLD = 0.98  # tolerance is abt 11 degrees

    for i, n in enumerate(normals[1:], 1):
        dot = _vec_dot(ref, n)
        if dot < DOT_THRESHOLD:
            raise RuntimeError("Dot too wide, faces must be better aligned")

    return True, poly_faces, ref

# 2— BOUNDS CHECKING

def _face_vertex_positions(mesh, face_idx):
    # Return a list of world-space (x, y, z) for each vertex on mesh.
    face_comp  = "{}.f[{}]".format(mesh, face_idx)
    vert_comps = cmds.polyListComponentConversion(face_comp, toVertex=True)
    vert_comps = cmds.ls(vert_comps, flatten=True)
    positions  = []
    for vc in vert_comps:
        pos = cmds.xform(vc, query=True, worldSpace=True, translation=True)
        positions.append(tuple(pos))
    return positions


def get_bounds(faces):
    # Compute the bounding box of faces projected onto the plane defined by the shared face normal.
    _valid, poly_faces, normal = valid_selection(faces) # TODO may change valid selection return if error check is sufficient

    mesh = poly_faces[0].split(".f[")[0]

    # Collect unique vertex world positions across all selected faces
    seen  = set()
    world_pts = []
    for face_str in poly_faces:
        idx = int(face_str.split(".f[")[1].rstrip("]"))
        for pt in _face_vertex_positions(mesh, idx):
            key = (round(pt[0], 6), round(pt[1], 6), round(pt[2], 6))
            if key not in seen:
                seen.add(key)
                world_pts.append(pt)

    # Build a local UV frame on the face
    world_up = (0.0, 1.0, 0.0)
    if abs(_vec_dot(normal, world_up)) > 0.99:
        world_up = (1.0, 0.0, 0.0)
    u_axis = _vec_normalize(_vec_cross(world_up, normal))
    v_axis = _vec_normalize(_vec_cross(normal, u_axis))

    # get the centroid
    n_pts = len(world_pts)
    cx = sum(p[0] for p in world_pts) / n_pts
    cy = sum(p[1] for p in world_pts) / n_pts
    cz = sum(p[2] for p in world_pts) / n_pts
    center = (cx, cy, cz)

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

# 3 — MANDELBROT CORE

def mandelbrot_iter(cx, cy, max_iter):
    # Creates Mandlbrot iterations based on user input
    zx, zy = 0.0, 0.0
    for i in range(max_iter):
        zx2 = zx * zx
        zy2 = zy * zy
        if zx2 + zy2 > 4.0:
            return i
        zx, zy = zx2 - zy2 + cx, 2.0 * zx * zy + cy
    return max_iter


def build_mandelbrot_grid(resolution, max_iter=DEFAULT_MAX_ITER):
    # Creates grid for mandlebrot projection based on user input resolution
    grid  = []
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
    Walk through the Mandelbrot grid and check for inside / outside boundaries. Essentially a big edge detector

    A cell is a boundary cell if it is inside the set AND has at least one 4-neighbour that is outside the set.

    Points are mapped from UV to world using bounds coordinates.

    Returns list of (x, y, z) tuples.
    """

    # FIXME bounds values are plain tuples. refactor to use index access, not like with previous structs .x/.y/.z
    cx, cy, cz = bounds["center"]
    ux, uy, uz = bounds["u_axis"]
    vx, vy, vz = bounds["v_axis"]
    width       = bounds["width"]
    height      = bounds["height"]

    boundary = []
    for row in range(resolution):
        for col in range(resolution):
            if grid[row][col] < max_iter:
                continue

            is_boundary = False
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < resolution and 0 <= nc < resolution:
                    if grid[nr][nc] < max_iter:
                        is_boundary = True
                        break
                else:
                    is_boundary = True  # grid edge counts as a boundary
                    break

            if not is_boundary:
                continue

            u_norm = col / (resolution - 1)
            v_norm = row / (resolution - 1)

            u_off = (u_norm - 0.5) * width
            v_off = (v_norm - 0.5) * height

            wx = cx + ux * u_off + vx * v_off
            wy = cy + uy * u_off + vy * v_off
            wz = cz + uz * u_off + vz * v_off

            boundary.append((wx, wy, wz))

    return boundary

### 4 — RENDER PATH

def render_path(bounds, resolution=DEFAULT_RESOLUTION, max_iter=DEFAULT_MAX_ITER):
    grid   = build_mandelbrot_grid(resolution, max_iter)
    points = extract_boundary_points(grid, max_iter, resolution, bounds)
    return points

### 5 — ONION-SKETCH

def _delete_onion():
    if cmds.objExists(ONION_GROUP):
        cmds.delete(ONION_GROUP)


def createOnion(boundary_points, bounds, z_value=DEFAULT_Z_VALUE):
    # Instatntiate a locator at every boundary point, offset by nomral oriented z_value

    _delete_onion()

    if not boundary_points:
        cmds.warning("No boundary points to display for Mandlebrot set.")
        return

    nx, ny, nz = bounds["normal"]

    grp = cmds.group(empty=True, name=ONION_GROUP)
    locators = []

    for (wx, wy, wz) in boundary_points:
        ox = wx + nx * z_value
        oy = wy + ny * z_value
        oz = wz + nz * z_value

        loc = cmds.spaceLocator()[0]
        cmds.move(ox, oy, oz, loc, absolute=True)
        cmds.scale(0.02, 0.02, 0.02, loc) # FIXME as of submission, should probably parameterize this 
        locators.append(loc)

    if locators:
        cmds.parent(locators, grp)

    layer_name = "mandelbrot_onion_layer"
    if not cmds.objExists(layer_name):
        cmds.createDisplayLayer(name=layer_name, empty=True)
    cmds.editDisplayLayerMembers(layer_name, grp, noRecurse=True)
    cmds.setAttr("{}.displayType".format(layer_name), 1)

    cmds.select(clear=True)
    print("Onion sketch: {} points, z_offset={:.4f}.".format(
        len(boundary_points), z_value))
    return grp

# 6 — FUTURE METHODS

def extrudePath(boundary_points, bounds, z_value):
    raise NotImplementedError("extrudePath() is not yet implemented.")


def embedPath(boundary_points, bounds, z_value):
    raise NotImplementedError("embedPath() is not yet implemented.")


def colorFractal(affected_faces, col1=(1, 0, 0), col2=(0, 1, 0)):
    raise NotImplementedError("colorFractal() is not yet implemented.")

#7 — GUI STATE - Found this in a maya GUI demo, which I will link in the report TP-B

class FractalToolState:
    # container for state shared across GUI callbacks. 
    bounds          = None   # from get_bounds()
    boundary_points = None   # from render_path()
    valid           = False

_state = FractalToolState()

# 8 — GUI CALLBACKS

def _get_ui_values(widgets):
    return {
        "resolution" : cmds.intSliderGrp  (widgets["resolution"], q=True, value=True),
        "max_iter"   : cmds.intSliderGrp  (widgets["max_iter"],   q=True, value=True),
        "z_value"    : cmds.floatSliderGrp(widgets["z_value"],    q=True, value=True),
        "color_on"   : cmds.checkBox      (widgets["color_on"],   q=True, value=True),
        "col1"       : cmds.colorSliderGrp(widgets["col1"],       q=True, rgbValue=True),
        "col2"       : cmds.colorSliderGrp(widgets["col2"],       q=True, rgbValue=True),
    }


def cb_check_selection(widgets, *_): # _* is a neat little thing to ignore any passed vals by maya to ignore thrown type errors
    _state.valid           = False
    _state.bounds          = None
    _state.boundary_points = None

    sel = cmds.ls(selection=True, flatten=True)
    if not sel:
        cmds.warning("Mandelbrot Nothing selected.")
        return

    try:
        _valid, poly_faces, _normal = valid_selection(sel)
    except RuntimeError as e:
        cmds.warning("Mandelbrot {}".format(e))
        return

    try:
        bounds = get_bounds(poly_faces)
    except RuntimeError as e:
        cmds.warning("Mandelbrot {}".format(e))
        return

    vals = _get_ui_values(widgets)

    cmds.refresh()

    pts = render_path(bounds, resolution=vals["resolution"], max_iter=vals["max_iter"])

    _state.bounds          = bounds
    _state.boundary_points = pts
    _state.valid           = True

    createOnion(pts, bounds, z_value=vals["z_value"])

    cmds.text(widgets["status"], edit=True,
              label="Status: OK -- {} boundary pts | w={:.3f} h={:.3f}".format(
                  len(pts), bounds["width"], bounds["height"]),
              bgc=(0.2, 0.5, 0.2))


def cb_z_changed(widgets, *_):
    # callback for z-value change. Thought it would be nice but lowk a waste of resources
    if not _state.valid:
        return
    vals = _get_ui_values(widgets)
    createOnion(_state.boundary_points, _state.bounds, z_value=vals["z_value"])


def cb_extrude(widgets, *_): #TODO
    if not _state.valid:
        cmds.warning("[Mandelbrot] Run 'Check Selection' first.")
        return
    vals = _get_ui_values(widgets)
    try:
        extrudePath(_state.boundary_points, _state.bounds, vals["z_value"])
    except NotImplementedError as e:
        cmds.confirmDialog(title="Not Yet Implemented", message=str(e), button=["OK"])


def cb_embed(widgets, *_): #TODO
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

# 9 — GUI CALL

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
    cmds.frameLayout(label="Fractal Parameters", collapsable=True, collapse=False, marginHeight=4, marginWidth=4)
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

    # Depth
    cmds.frameLayout(label="Extrusion / Embedding Depth", collapsable=True, collapse=False,
                     marginHeight=4, marginWidth=4)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    widgets["z_value"] = cmds.floatSliderGrp(
        label="Z-Value  ", field=True,
        minValue=0.001, maxValue=2.0, value=DEFAULT_Z_VALUE, precision=3,
        columnWidth=[(1, 90), (2, 60)],
        annotation="Depth along face normal for extrusion / embedding",
        changeCommand=lambda *a: cb_z_changed(widgets, *a), #using lambdas to refresh depth value in real time.
        dragCommand=lambda *a:   cb_z_changed(widgets, *a))
    cmds.setParent("..")
    cmds.setParent("..")

    # Color options 
    cmds.frameLayout(label="Color Options  (future)", collapsable=True, collapse=True,
                     marginHeight=4, marginWidth=4)
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
        label="Extrude (stub)",
        height=30, bgc=(0.35, 0.55, 0.35),
        command=lambda *a: cb_extrude(widgets, *a),
        annotation="Extrude Mandelbrot geometry outward - pass")
    cmds.button(
        label="Embed (stub)",
        height=30, bgc=(0.55, 0.40, 0.35),
        command=lambda *a: cb_embed(widgets, *a),
        annotation="Embed Mandelbrot geometry inward - pass")
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

### Main

def run():
    """Open the Mandelbrot Fractal Tool window."""
    build_gui()
    print("Mandlebrot Tool opened successfully.")

if __name__ == "__main__":
    run()