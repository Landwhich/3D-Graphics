import maya.cmds as cmds
import math

# ---- UI

WINDOW_NAME = "A01Window"

if cmds.window(WINDOW_NAME, exists=True):
    cmds.deleteUI(WINDOW_NAME)

cmds.window(WINDOW_NAME, title="Don't Cross Me", widthHeight=(500, 300))
cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

cmds.text(label="click sphere -> then cube (or box drag both)", align="left")
cmds.button(label="Check Intersections", height=40, command='findIntersect()')

outputScroll = cmds.scrollField(editable=False, wordWrap=True, height=200)

cmds.showWindow(WINDOW_NAME)


# --- Math funcs

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def cross(a, b):
    return [
        a[1]*b[2] - a[2]*b[1],
        a[2]*b[0] - a[0]*b[2],
        a[0]*b[1] - a[1]*b[0]
    ]

def subtract(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

def add(a, b):
    return [a[0]+b[0], a[1]+b[1], a[2]+b[2]]

def multiply(v, s):
    return [v[0]*s, v[1]*s, v[2]*s]

def magnitude(v):
    return math.sqrt(dot(v, v))

def normalize(v):
    mag = magnitude(v)
    if mag == 0:
        return [0, 0, 0]
    return [v[0]/mag, v[1]/mag, v[2]/mag]

def distance(a, b):
    return magnitude(subtract(a, b))


# --- Geometry funcs

def triangleNormal(a, b, c):
    return normalize(cross(subtract(b, a), subtract(c, a)))

def pointInTriangle(p, a, b, c):
    # better than rasterizer project right side dot test. better computationally due to caching
    v0 = subtract(c, a)
    v1 = subtract(b, a)
    v2 = subtract(p, a)

    d00 = dot(v0, v0)
    d01 = dot(v0, v1)
    d11 = dot(v1, v1)
    d20 = dot(v2, v0)
    d21 = dot(v2, v1)

    denom = d00 * d11 - d01 * d01
    if denom == 0:
        return False

    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1 - v - w

    return (u >= 0 and v >= 0 and w >= 0)

def rayPlaneIntersection(rayOrigin, rayDir, p0, normal):
    denom = dot(normal, rayDir)
    if abs(denom) < 1e-6:
        return None

    t = dot(subtract(p0, rayOrigin), normal) / denom
    if t < 0:
        return None

    return add(rayOrigin, multiply(rayDir, t))


# --- main()

def findIntersect():
    cmds.scrollField(outputScroll, clear=True)

    selection = cmds.ls(selection=True, transforms=True)
    if len(selection) != 2:
        cmds.warning("Select exactly two objects.")
        return

    #sphere, then cube
    sphere, target = selection

    sphereCenter = cmds.xform(sphere, q=True, ws=True, rp=True)

    #Get sphere vertices
    sphereShape = cmds.listRelatives(sphere, shapes=True)[0]
    sphereVerts = cmds.ls(f"{sphereShape}.vtx[*]", flatten=True)

    # cube
    targetShape = cmds.listRelatives(target, shapes=True)[0]
    faces = cmds.polyEvaluate(targetShape, face=True)

    # intersections = []
    index = 1

    for vtx in sphereVerts:
        vtxPos = cmds.pointPosition(vtx, world=True)
        rayDir = normalize(subtract(vtxPos, sphereCenter))

        closestHit = None
        closestDist = float("inf")
        hitData = None

        for f in range(faces):
            verts = cmds.polyInfo(f"{targetShape}.f[{f}]", faceToVertex=True)[0].split()[2:]
            verts = [int(v) for v in verts]
            
            pts = [cmds.pointPosition(f"{targetShape}.vtx[{i}]", world=True) for i in verts]
            
            triangles = [
                (pts[0], pts[1], pts[2]),
                (pts[0], pts[2], pts[3])
            ]
            
            for tri in triangles:
                normal = triangleNormal(tri[0], tri[1], tri[2])
                hit = rayPlaneIntersection(sphereCenter, rayDir, tri[0], normal)
            
                if hit and pointInTriangle(hit, tri[0], tri[1], tri[2]):
                    d = distance(sphereCenter, hit)
                    if d < closestDist:
                        closestDist = d
                        closestHit = hit
                        hitData = (tri, normal)


        if closestHit:
            cmds.polyCube(w=0.1, h=0.1, d=0.1)
            cmds.xform(ws=True, t=closestHit)

            tri, normal = hitData
            facetArea = 0.5 * magnitude(cross(subtract(tri[1], tri[0]), subtract(tri[2], tri[0])))
            angle = math.degrees(math.acos(abs(dot(rayDir, [0,1,0]))))

            msg = (
                f"  {index}) Intersection @ ({closestHit[0]:.2f}, {closestHit[1]:.2f}, {closestHit[2]:.2f})\n"
                f"  Line: {sphereCenter} -> {vtxPos}\n"
                f"  Facet Area: {facetArea:.2f}\n"
                f"  Distance to Vertex: {closestDist:.2f}\n"
                f"  Normal: {[round(n,2) for n in normal]}\n"
                f"  Angle to Grid: {angle:.2f}degrees\n\n"
            )

            cmds.scrollField(outputScroll, edit=True, insertText=msg)
            index += 1
