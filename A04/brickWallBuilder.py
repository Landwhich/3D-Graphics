import maya.cmds as cmds
import random

def generate_surface(surface_type, params):
    cmds.undoInfo(openChunk=True)
    try:
        if surface_type == 'Wall':
            _generate_wall(params)
        elif surface_type in ('Floor', 'Ceiling'):
            _generate_floor_ceiling(surface_type, params)
    finally:
        cmds.undoInfo(closeChunk=True)

def _generate_wall(p):
    wall_w    = p['wall_width']
    wall_h    = p['wall_height']
    b_len     = p['brick_length']
    b_height  = p['brick_height']
    b_depth   = p['brick_depth']
    mortar    = p['mortar']
    var       = p['variation']
    depth_var = p['depth_variation']
    bevel_sz  = p['bevel_size']
    grp_name  = p['group_name']

    bricks = []
    row    = 0
    y      = mortar / 2.0

    while y + b_height <= wall_h + 0.001:
        offset = ((b_len + mortar) / 2.0) if (row % 2 == 1) else 0.0
        x = -offset + mortar / 2.0

        while True:
            current_len = b_len
            if x < 0:
                current_len = b_len + x
                x = 0
            if x + current_len > wall_w:
                current_len = wall_w - x

            if current_len < mortar:
                x += b_len + mortar
                continue

            vx  = random.uniform(-var, var)
            vy  = random.uniform(-var, var)
            vz  = random.uniform(0, var * 2)
            vsx = random.uniform(1 - var * 0.05, 1 + var * 0.05)
            vsy = random.uniform(1 - var * 0.05, 1 + var * 0.05)

            actual_depth = b_depth + random.uniform(-depth_var, depth_var)
            actual_depth = max(actual_depth, mortar)

            bx = x + current_len / 2.0 + vx
            by = y + b_height / 2.0    + vy
            bz = actual_depth / 2.0    + vz

            cube = cmds.polyCube(
                w = current_len * vsx,
                h = b_height    * vsy,
                d = actual_depth,
                sx=1, sy=1, sz=1,
                name='brick_#'
            )[0]

            cmds.move(bx, by, bz, cube)

            if bevel_sz > 0.0:
                _bevel_brick(cube, bevel_sz)

            bricks.append(cube)

            x += current_len + mortar
            if x >= wall_w - 0.001:
                break

        y  += b_height + mortar
        row += 1

    _finalize(bricks, grp_name, 'Wall')


def _generate_floor_ceiling(surface_type, p):
    surf_w    = p['floor_width']
    surf_d    = p['floor_depth']
    b_len     = p['brick_length']
    b_wid     = p['brick_width'] 
    b_thick   = p['brick_depth'] 
    mortar    = p['mortar']
    var       = p['variation']
    depth_var = p['depth_variation']
    bevel_sz  = p['bevel_size']
    grp_name  = p['group_name']

    bricks = []
    row    = 0
    z      = mortar / 2.0

    while z + b_wid <= surf_d + 0.001:
        offset = ((b_len + mortar) / 2.0) if (row % 2 == 1) else 0.0
        x = -offset + mortar / 2.0

        while True:
            current_len = b_len
            if x < 0:
                current_len = b_len + x
                x = 0
            if x + current_len > surf_w:
                current_len = surf_w - x

            if current_len < mortar:
                x += b_len + mortar
                continue

            vx  = random.uniform(-var, var)
            vz  = random.uniform(-var, var)
            vy  = random.uniform(0, var * 2)
            vsx = random.uniform(1 - var * 0.05, 1 + var * 0.05)
            vsz = random.uniform(1 - var * 0.05, 1 + var * 0.05)

            actual_thick = b_thick + random.uniform(-depth_var, depth_var)
            actual_thick = max(actual_thick, mortar)

            bx = x + current_len / 2.0 + vx
            bz = z + b_wid / 2.0       + vz
            by = actual_thick / 2.0    + vy

            if surface_type == 'Ceiling':
                by = -by

            cube = cmds.polyCube(
                w = current_len * vsx,
                h = actual_thick,
                d = b_wid    * vsz,
                sx=1, sy=1, sz=1,
                name='brick_#'
            )[0]

            cmds.move(bx, by, bz, cube)

            if bevel_sz > 0.0:
                _bevel_brick(cube, bevel_sz)

            bricks.append(cube)

            x += current_len + mortar
            if x >= surf_w - 0.001:
                break

        z  += b_wid + mortar
        row += 1

    grp = _finalize(bricks, grp_name, surface_type)

    if surface_type == 'Ceiling' and grp:
        cmds.move(0, p.get('wall_height', 4.0), 0, grp, relative=True)


def _bevel_brick(cube, bevel_sz):
    try:
        cmds.polyBevel3(
            cube,
            fraction=0.0, 
            offsetAsFraction=False,
            offset=bevel_sz,
            segments=1,
            worldSpace=True,
            smoothingAngle=30,
            fillNgons=True,
            mergeVertices=True,
            mergeVertexTolerance=0.0001,
            chamfer=True,
            name='brickBevel_#'
        )
    except Exception as e:
        cmds.warning(f'[BrickGen] Bevel skipped on {cube}: {e}')


def _finalize(bricks, grp_name, surface_type):
    if not bricks:
        cmds.warning('No bricks were generated. Check your dimensions.')
        return None

    grp = cmds.group(bricks, name=grp_name + '_' + surface_type + '_#')
    cmds.xform(grp, centerPivots=True)

    total_poly = sum(
        cmds.polyEvaluate(b, face=True) for b in bricks
    )
    print(
        f'[BrickGen] Generated {len(bricks)} bricks '
        f'({total_poly} polygons) → group: {grp}'
    )
    cmds.select(grp)
    return grp

WINDOW_ID = 'brickGenWindow'

def build_gui():
    if cmds.window(WINDOW_ID, exists=True):
        cmds.deleteUI(WINDOW_ID)

    win = cmds.window(
        WINDOW_ID,
        title='Brick / Stone Surface Generator',
        widthHeight=(400, 620),
        sizeable=True,
        menuBar=False
    )

    cmds.scrollLayout(horizontalScrollBarThickness=0)
    main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    cmds.separator(height=8, style='none')

    cmds.frameLayout(
        label=' Surface Type',
        collapsable=False,
        marginHeight=6,
        marginWidth=8
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    surface_type_ctrl = cmds.optionMenu(
        label='Type',
        changeCommand=lambda val: _on_type_change(val, dim_frames)
    )
    cmds.menuItem(label='Wall')
    cmds.menuItem(label='Floor')
    cmds.menuItem(label='Ceiling')

    cmds.setParent('..')
    cmds.setParent('..')

    dim_frames = {}

    dim_frames['Wall'] = cmds.frameLayout(
        label=' Wall Dimensions  (metres)',
        collapsable=False,
        marginHeight=6,
        marginWidth=8,
        visible=True
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    wall_w_ctrl = _float_field('Wall Width  (X)',  default=4.0, minv=0.1)
    wall_h_ctrl = _float_field('Wall Height (Y)',  default=3.0, minv=0.1)
    cmds.setParent('..')
    cmds.setParent('..')

    dim_frames['Floor'] = cmds.frameLayout(
        label=' Floor Dimensions  (metres)',
        collapsable=False,
        marginHeight=6,
        marginWidth=8,
        visible=False
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    floor_w_ctrl = _float_field('Floor Width  (X)', default=4.0, minv=0.1)
    floor_d_ctrl = _float_field('Floor Depth  (Z)', default=4.0, minv=0.1)
    cmds.setParent('..')
    cmds.setParent('..')

    dim_frames['Ceiling'] = cmds.frameLayout(
        label=' Ceiling Dimensions  (metres)',
        collapsable=False,
        marginHeight=6,
        marginWidth=8,
        visible=False
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    ceil_w_ctrl  = _float_field('Ceiling Width  (X)',  default=4.0, minv=0.1)
    ceil_d_ctrl  = _float_field('Ceiling Depth  (Z)',  default=4.0, minv=0.1)
    ceil_ht_ctrl = _float_field('Room Height    (Y)',  default=3.0, minv=0.1,
                                annotation='Ceiling will be placed at this height')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.separator(height=4, style='none')

    cmds.frameLayout(
        label=' Brick Size  (metres)',
        collapsable=False,
        marginHeight=6,
        marginWidth=8
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    brick_len_ctrl   = _float_field('Brick Length (X)',   default=0.215, minv=0.01)
    brick_h_ctrl     = _float_field('Brick Height (Y)',   default=0.065, minv=0.01,
                                    annotation='Used for Wall only')
    brick_w_ctrl     = _float_field('Brick Width  (Z)',   default=0.1025, minv=0.01,
                                    annotation='Used for Floor / Ceiling only')
    brick_depth_ctrl = _float_field('Brick Depth  (extrusion)', default=0.1025, minv=0.005)
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.frameLayout(
        label=' Mortar & Variation',
        collapsable=False,
        marginHeight=6,
        marginWidth=8
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    mortar_ctrl   = _float_field('Mortar Width',  default=0.01,  minv=0.001, maxv=0.1)
    var_ctrl      = _float_field('Pos/Scale Variation  (0 = none)',
                                 default=0.003, minv=0.0, maxv=0.05,
                                 annotation='Random positional and size jitter per brick')
    depth_var_ctrl = _float_field('Depth Variation  (0 = none)',
                                  default=0.02, minv=0.0, maxv=0.05,
                                  annotation='Random extrusion depth variation per brick — '
                                             'independent of Pos/Scale variation')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.frameLayout(
        label=' Bevel',
        collapsable=False,
        marginHeight=6,
        marginWidth=8
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    bevel_ctrl = _float_field('Bevel Size  (0 = none)',
                              default=0.006, minv=0.0, maxv=0.02,
                              annotation='Chamfer size applied to all brick edges. '
                                         '0.002–0.005 m is realistic for stone.')
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.frameLayout(
        label=' Output',
        collapsable=False,
        marginHeight=6,
        marginWidth=8
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    grp_ctrl = cmds.textFieldGrp(
        label='Group Name',
        text='brickSurface',
        columnWidth2=(120, 200)
    )
    cmds.setParent('..')
    cmds.setParent('..')

    cmds.separator(height=8, style='in')

    cmds.button(
        label='Generate Surface',
        height=40,
        backgroundColor=(0.2, 0.55, 0.2),
        command=lambda _: _on_generate(
            surface_type_ctrl,
            wall_w_ctrl, wall_h_ctrl,
            floor_w_ctrl, floor_d_ctrl,
            ceil_w_ctrl, ceil_d_ctrl, ceil_ht_ctrl,
            brick_len_ctrl, brick_h_ctrl, brick_w_ctrl, brick_depth_ctrl,
            mortar_ctrl, var_ctrl, depth_var_ctrl, bevel_ctrl, grp_ctrl
        )
    )

    cmds.separator(height=4, style='none')

    cmds.text(
        label=(
            'Running bond pattern  |  Per-brick pos/scale + depth variation\n'
            'Chamfer bevel on all edges  |  All bricks grouped under one node'
        ),
        font='smallPlainLabelFont',
        align='center'
    )
    cmds.separator(height=8, style='none')

    cmds.showWindow(win)

def _float_field(label, default=1.0, minv=0.0, maxv=1000.0, annotation=''):
    ctrl = cmds.floatFieldGrp(
        label=label,
        value1=default,
        precision=4,
        columnWidth2=(160, 120),
        annotation=annotation if annotation else label
    )
    return ctrl


def _on_type_change(val, dim_frames):
    for key, frame in dim_frames.items():
        cmds.frameLayout(frame, edit=True, visible=(key == val))


def _on_generate(
    surface_type_ctrl,
    wall_w_ctrl, wall_h_ctrl,
    floor_w_ctrl, floor_d_ctrl,
    ceil_w_ctrl, ceil_d_ctrl, ceil_ht_ctrl,
    brick_len_ctrl, brick_h_ctrl, brick_w_ctrl, brick_depth_ctrl,
    mortar_ctrl, var_ctrl, depth_var_ctrl, bevel_ctrl, grp_ctrl
):
    stype = cmds.optionMenu(surface_type_ctrl, query=True, value=True)

    params = {
        'brick_length':    cmds.floatFieldGrp(brick_len_ctrl,   query=True, value1=True),
        'brick_height':    cmds.floatFieldGrp(brick_h_ctrl,     query=True, value1=True),
        'brick_width':     cmds.floatFieldGrp(brick_w_ctrl,     query=True, value1=True),
        'brick_depth':     cmds.floatFieldGrp(brick_depth_ctrl, query=True, value1=True),
        'mortar':          cmds.floatFieldGrp(mortar_ctrl,      query=True, value1=True),
        'variation':       cmds.floatFieldGrp(var_ctrl,         query=True, value1=True),
        'depth_variation': cmds.floatFieldGrp(depth_var_ctrl,   query=True, value1=True),
        'bevel_size':      cmds.floatFieldGrp(bevel_ctrl,       query=True, value1=True),
        'group_name':      cmds.textFieldGrp(grp_ctrl,          query=True, text=True),
    }

    if stype == 'Wall':
        params['wall_width']  = cmds.floatFieldGrp(wall_w_ctrl, query=True, value1=True)
        params['wall_height'] = cmds.floatFieldGrp(wall_h_ctrl, query=True, value1=True)

    elif stype == 'Floor':
        params['floor_width'] = cmds.floatFieldGrp(floor_w_ctrl, query=True, value1=True)
        params['floor_depth'] = cmds.floatFieldGrp(floor_d_ctrl, query=True, value1=True)

    elif stype == 'Ceiling':
        params['floor_width']  = cmds.floatFieldGrp(ceil_w_ctrl,  query=True, value1=True)
        params['floor_depth']  = cmds.floatFieldGrp(ceil_d_ctrl,  query=True, value1=True)
        params['wall_height']  = cmds.floatFieldGrp(ceil_ht_ctrl, query=True, value1=True)

    generate_surface(stype, params)

build_gui()