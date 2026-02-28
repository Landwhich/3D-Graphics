import maya.cmds as cmds
import random as rnd
import math

#UI Shenanigins

if 'myWin' in globals():
    if cmds.window(myWin, exists=True):
        cmds.deleteUI(myWin, window=True)

myWin = cmds.window(title="Lego Bricks", menuBar=True)

cmds.menu(label="Basic Options")
cmds.menuItem(label="New Scene", command=('cmds.file(new=True, force=True)'))
cmds.menuItem(label="Delete Selected", command=('cmds.delete()'))

cmds.columnLayout(adjustableColumn=True)

# Axle Pieces
cmds.frameLayout(collapsable=True, label="Technic Axles", width=475)
cmds.columnLayout()
cmds.optionMenu('axleLengthMenu', label="Axle Length")
for i in [2,3,4,5,6,7,8,9,10,11,12]:
    cmds.menuItem(label=str(i) + "L")
cmds.colorSliderGrp('axleColour', label="Color", hsv=(200,0,0.2))
cmds.button(label="Create Axle", command=('makeAxle()'))

cmds.setParent('..')
cmds.setParent('..')

# Technic Pins
cmds.frameLayout(collapsable=True, label="Technic Pins", width=475)
cmds.columnLayout()
cmds.optionMenu('pinLengthMenu', label="Pin Length")
for i in [2,3]:
    cmds.menuItem(label=str(i) + "L")
cmds.colorSliderGrp('pinColour', label="Color", hsv=(200,0,0.2))
cmds.button(label="Create Pin", command=('makePin()'))

cmds.setParent('..')
cmds.setParent('..')

# Holed Technic Pieces
cmds.frameLayout(collapsable=True, label="Holed Technic Pieces", width=475)
cmds.columnLayout()
cmds.optionMenu('holedLengthMenu', label="no of Studs for standard pieces")
for i in [2,3,4,5,6,7,8,9,10,11,12,13]:
    cmds.menuItem(label=str(i) + "L")
cmds.colorSliderGrp('holedTechnicColour', label="Color", hsv=(3,0.9,0.9))
cmds.intSliderGrp('angleLenA', l="Angled Arm A Length", f=True, min=2, max=10, v=5)
cmds.intSliderGrp('angleLenB', l="Angled Arm B Length", f=True, min=2, max=10, v=3)
cmds.optionMenu('angleDeg', label="no of Studs for standard pieces")
for i in [90, 135]:
    cmds.menuItem(label=str(i))

cmds.button(label="Create Angled Liftarm", command=('makeAngledLiftarm()'))
cmds.button(label="Create Holed Piece", command=('makeHoledTechnic()'))
cmds.button(label="Create Technic Brick", command=('makeTechnicBrick()'))

cmds.setParent('..')
cmds.setParent('..')

# Thin Technic Misc
cmds.frameLayout(collapsable=True, label="Thin Technic Misc", width=475)
cmds.columnLayout()

cmds.colorSliderGrp('technicColor', label="Color", hsv=(3,0.9,.75))
cmds.button(label="Create Curved L-Liftarm", command=('makeCurvedL()'))
cmds.button(label="Create 2X1 Axle Connector", command=('makeAxle2X1Con()'))

cmds.setParent('..')
cmds.setParent('..')

#Weheels
cmds.frameLayout(collapsable=True, label="Thin Technic Misc", width=475)
cmds.columnLayout()
cmds.button(label="Create Technic Tire + Rim", command="makeTechnicTire()")
cmds.setParent('..')
cmds.setParent('..')

#Standard Brick
cmds.frameLayout(collapsable=True, label="Standard Brick", width=475)
cmds.columnLayout()
cmds.intSliderGrp('brickHeight', l="Height", f=True, min=1, max=20, value=3)
cmds.intSliderGrp('brickWidth', l="Width (Bumps)", f=True, min=1, max=20, value=2)
cmds.intSliderGrp('brickDepth', l="Depth (Bumps)", f=True, min=1, max=20, value=8)
cmds.colorSliderGrp('brickColour', label="Color", hsv=(256, 1, 1))

cmds.columnLayout()
cmds.button(label="Get Bricked", command=('basicBrick()'))
cmds.button(label="skinny Brick", command=('makeThinBrick()'))

cmds.setParent('..')
cmds.setParent('..')
cmds.setParent('..')

#Sloped Brick
cmds.frameLayout(collapsable=True, label="Sloped Brick", width=475)
cmds.columnLayout()
cmds.intSliderGrp('slopedWidth', l="Width (Bumps)", f=True, min=1, max=20, v=4)
cmds.intSliderGrp('slopedDepth', l="Depth (Bumps)", f=True, min=2, max=4, v=2)
cmds.colorSliderGrp('slopedColour', l="Colour", hsv=(12,1,1))

cmds.columnLayout()
cmds.button(label="Make Sloped Brick", command=('slopedBrick()'))

cmds.setParent('..')
cmds.setParent('..')

cmds.showWindow(myWin)

### Brick Size Globals: 

g_brickWidthUnit = 0.8
g_brickHeightUnit = 0.32
g_studRadUnit = 0.25
g_studHeightUnit = 0.2
g_holeRadUnit = 0.26
g_axleUnit = 0.10
g_axleHoleUnit = 0.12

def basicBrick():
    brickHeight = cmds.intSliderGrp('brickHeight', q=True, v=True)
    brickWidth = cmds.intSliderGrp('brickWidth', q=True, v=True)
    brickDepth = cmds.intSliderGrp('brickDepth', q=True, v=True)
    rgb = cmds.colorSliderGrp('brickColour', q=True, rgbValue=True)
    ns = "Brick" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    brickSizeX = brickWidth * g_brickWidthUnit
    brickSizeZ = brickDepth * g_brickWidthUnit
    brickSizeY = brickHeight * g_brickHeightUnit

    cmds.polyCube(h=brickSizeY, w=brickSizeX, d=brickSizeZ)
    cmds.move((brickSizeY / 2.0), moveY=True)
    for i in range(brickWidth):
        for j in range(brickDepth):
            cmds.polyCylinder(r=g_studRadUnit, h=g_studHeightUnit)
            cmds.move((brickSizeY + 0.10), moveY=True, a=True)
            cmds.move(((i * g_brickWidthUnit) - (brickSizeX/2.0) + 0.4), moveX=True, a=True)
            cmds.move(((j * g_brickWidthUnit) - (brickSizeZ/2.0) + 0.4), moveZ=True, a=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.polyUnite((ns+":*"), n=ns, ch=False)
    cmds.delete(ch=True)

    cmds.hyperShade(assign=(ns+":brckMat"))
    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)
    
def slopedBrick():
    brickHeight = 3
    brickWidth = cmds.intSliderGrp('slopedWidth', q=True, v=True)
    brickDepth = cmds.intSliderGrp('slopedDepth', q=True, v=True)
    rgb = cmds.colorSliderGrp('slopedColour', q=True, rgbValue=True)
    ns = "Brick" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    brickSizeX = brickWidth * g_brickWidthUnit
    brickSizeZ = brickDepth * g_brickWidthUnit
    brickSizeY = brickHeight * g_brickHeightUnit

    cmds.polyCube(h=brickSizeY, w=brickSizeX, d=brickSizeZ, sz=brickDepth)
    cmds.move((brickSizeY / 2.0), y=True, a=True)
    for i in range(brickWidth):
        cmds.polyCylinder(r=g_studRadUnit, h=g_studHeightUnit)
        cmds.move((brickSizeY + 0.10), moveY=True, a=True)
        cmds.move(((i * g_brickWidthUnit) - (brickSizeX/2.0) + 0.4), moveX=True, a=True)
        cmds.move((0 - (brickSizeZ/2.0) + 0.4), moveZ=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.polyUnite((ns+":*"), n=ns, ch=False)
    cmds.delete(ch=True)

    cmds.hyperShade(assign=(ns+":brckMat"))

    cmds.select((ns+":"+ns+".e[1]"), r=True)
    cmds.move(0, -g_brickWidthUnit, 0, r=True)

    if brickDepth == 4:
        tV = cmds.xform((ns + ":" + ns + ".vtx[8]"), q=True, t=True)
        cmds.select((ns + ":" + ns + ".vtx[6]"), r=True)
        cmds.move(tV[0], tV[1], tV[2], a=True)
        tV = cmds.xform((ns + ":" + ns + ".vtx[9]"), q=True, t=True)
        cmds.select((ns + ":" + ns + ".vtx[7]"), r=True)
        cmds.move(tV[0], tV[1], tV[2], a=True)

    if brickDepth >= 3:
        tV = cmds.xform((ns + ":" + ns + ".vtx[6]"), q=True, t=True)
        cmds.select((ns + ":" + ns + ".vtx[4]"), r=True)
        cmds.move(tV[0], tV[1], tV[2], a=True)
        tV = cmds.xform((ns + ":" + ns + ".vtx[7]"), q=True, t=True)
        cmds.select((ns + ":" + ns + ".vtx[5]"), r=True)
        cmds.move(tV[0], tV[1], tV[2], a=True)
        cmds.select( clear=True )

    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)
    
def makeThinBrick():
    brickWidth = cmds.intSliderGrp('brickWidth', q=True, v=True)
    brickDepth = cmds.intSliderGrp('brickDepth', q=True, v=True)
    rgb = cmds.colorSliderGrp('brickColour', q=True, rgbValue=True)
    ns = "ThinBrick" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    brickSizeX = brickWidth * g_brickWidthUnit
    brickSizeZ = brickDepth * g_brickWidthUnit
    brickSizeY = g_brickHeightUnit

    cmds.polyCube(h=brickSizeY, w=brickSizeX, d=brickSizeZ)
    cmds.move((brickSizeY / 2.0), moveY=True)
    for i in range(brickWidth):
        for j in range(brickDepth):
            cmds.polyCylinder(r=g_studRadUnit, h=g_studHeightUnit)
            cmds.move((brickSizeY + 0.10), moveY=True, a=True)
            cmds.move(((i * g_brickWidthUnit) - (brickSizeX/2.0) + 0.4), moveX=True, a=True)
            cmds.move(((j * g_brickWidthUnit) - (brickSizeZ/2.0) + 0.4), moveZ=True, a=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.polyUnite((ns+":*"), n=ns, ch=False)
    cmds.delete(ch=True)

    cmds.hyperShade(assign=(ns+":brckMat"))
    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)

def makeAxle():
    axleLength = int(cmds.optionMenu('axleLengthMenu', q=True, v=True).replace("L",""))
    rgb = cmds.colorSliderGrp('axleColour', q=True, rgbValue=True)
    ns = "Axle" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    axleLength *= g_brickWidthUnit

    for axis in ["X", "Y"]:
        cmds.polyCube(w=g_axleUnit, h=g_studRadUnit, d=(axleLength - g_studRadUnit))[0] #all axles have a weird offset in them (not a full block)
        cmds.move(axleLength/2.0, moveZ=True)
        if axis == "X":
            cmds.rotate(0, 0, 90)

    cmds.shadingNode('lambert', asShader=True, name="axleMat")
    cmds.setAttr(ns+":axleMat.color", rgb[0], rgb[1], rgb[2], typ='double3')
    cmds.polyUnite((ns+":*"), n=ns, ch=False)
    cmds.delete(ch=True)
    cmds.hyperShade(assign=(ns+":axleMat"))

    cmds.namespace(removeNamespace=":"+ns, mergeNamespaceWithParent=True)
    
def makePin():
    pinLength = int(cmds.optionMenu('pinLengthMenu', q=True, v=True).replace("L",""))
    rgb = cmds.colorSliderGrp('pinColour', q=True, rgbValue=True)
    ns = "Pin" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=':')
    pinLength *= g_brickWidthUnit

    cmds.polyCylinder(r=g_studRadUnit, h=(pinLength - g_studRadUnit), n=(ns+':base'))[0]
    cmds.polyCylinder(r=g_studRadUnit * 0.8, h=(pinLength + g_studRadUnit), n=(ns+':cutter'))[0]
    cmds.polyCBoolOp(ns+':base', ns+':cutter', op=2, ch=False, n=(ns+':pin'))
    cmds.delete(ch=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name=(ns+':pinMat'))
    cmds.setAttr(ns+':pinMat.color', rgb[0], rgb[1], rgb[2], typ='double3')
    cmds.delete(ch=True)

    cmds.select(ns+':pin')
    cmds.hyperShade(assign=(ns+':pinMat'))

    cmds.namespace(removeNamespace=':'+ns, mergeNamespaceWithParent=True)
    
def makeCurvedL():
    rgb = cmds.colorSliderGrp('technicColor', q=True, rgbValue=True)
    ns = "LArm" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    base = cmds.polyCube(w=g_brickWidthUnit * 3, h=g_brickHeightUnit, d=g_brickWidthUnit * 3)[0]
    cutter = cmds.polyCylinder(r=g_brickWidthUnit * 3, h=g_brickHeightUnit, sa=40)
    cmds.move(g_brickWidthUnit * 3/2.0, 0, g_brickWidthUnit * 3/2.0)
    cmds.polyCBoolOp(base, cutter, op=3, n='frame')  # subtract
    copy = cmds.duplicate(ns+':frame')
    cmds.scale(0.45, 10, 0.45)
    cmds.move(-0.125*g_brickWidthUnit, 0, -0.125*g_brickWidthUnit)
    cmds.polyCBoolOp(ns+':frame', copy, op=2, n='frame')
    
    # Add holes
    holes = [ 
    # using index 0 for type
        (0, g_brickWidthUnit, 0, 0),
        (0, 0, 0, g_brickWidthUnit),
        (1, -g_brickWidthUnit, 0,  g_brickWidthUnit),
        (1,  g_brickWidthUnit, 0, -g_brickWidthUnit),
        (1,  g_brickWidthUnit, 0,  g_brickWidthUnit)
    ]
    i = 2
    for hole in holes:
        if hole[0] == 0:
            cutter = cmds.polyCylinder(r=g_holeRadUnit, h=g_brickHeightUnit)[0]
        else:
            xAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_holeRadUnit, d=(g_brickHeightUnit))[0]
            cmds.rotate(0, 0, 90)
            yAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_holeRadUnit, d=(g_brickHeightUnit))[0]
            cutter = cmds.polyCBoolOp(xAxle, yAxle, op=1, ch=False)[0]
            cmds.rotate(90, 0, 0)
            cmds.delete(ch=True)
        cmds.move(hole[1], 0, hole[3])
        cmds.polyCBoolOp(ns+':frame'+str(i), cutter, op=2, n='frame'+str(i+1))
        cmds.delete(ch=True)
        i += 1
        
    mat = cmds.shadingNode("lambert", asShader=True, name="larmMat")
    cmds.setAttr(ns+":larmMat.color", rgb[0], rgb[1], rgb[2], typ="double3")
        
    cmds.polyBevel( 
        ns+':frame'+str(i)+'.e[166]', 
        ns+':frame'+str(i)+'.e[168]', 
        ns+':frame'+str(i)+'.e[170]', 
        segments=4, offset=0.35 )
    #cmds.polyBevel( ns+':frame'+str(i)+'.e[167]', segments=4, offset=0.35 )
    #cmds.polyBevel( ns+':frame'+str(i)+'.e[166]', segments=4, offset=0.35 )
    cmds.select(ns+":*")

    # Material
    cmds.hyperShade(assign=(ns+":larmMat"))
    cmds.delete(ch=True)
    cmds.namespace(removeNamespace=":"+ns, mergeNamespaceWithParent=True)
    
def makeAxle2X1Con():
    rgb = cmds.colorSliderGrp('technicColor', q=True, rgbValue=True)
    ns = "axleSplice" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)
    
    xAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_holeRadUnit, d=(g_brickHeightUnit))[0]
    cmds.rotate(0, 0, 90)
    yAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_holeRadUnit, d=(g_brickHeightUnit))[0]
    cutter1 = cmds.polyCBoolOp(xAxle, yAxle, op=1, ch=False)[0]
    cmds.rotate(90, 0, 0)
    cmds.move(0, 0, g_brickWidthUnit / 2)
    cutter2 = cmds.duplicate(cutter1)
    cmds.move(0, 0, -g_brickWidthUnit / 2)
    
    base = cmds.polyCube(h=g_brickHeightUnit, w=g_brickWidthUnit, d=(2 * g_brickWidthUnit))
    
    cmds.polyCBoolOp(base, cutter1, cutter2, op=2, ch=False, n='base')[0]
    
    cmds.polyBevel( ns+':base.e[20]', ns+':base.e[22]', ns+':base.e[42]', ns+':base.e[74]', segments=4, offset=0.35 )

    myShader = cmds.shadingNode('lambert', asShader=True, name="axleSpliceMat")
    cmds.setAttr(ns+":axleSpliceMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.select(ns+":*")
    cmds.hyperShade(assign=(ns+":axleSpliceMat"))
    cmds.delete(ch=True)
    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)
    
def makeHoledTechnic():

    size = int(cmds.optionMenu('holedLengthMenu', q=True, v=True).replace("L",""))
    rgb = cmds.colorSliderGrp('holedTechnicColour', q=True, rgbValue=True)
    ns = "HoledTechnic" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    holedLength = g_brickWidthUnit * size

    cmds.polyCube(h=g_brickWidthUnit*0.9, w=g_brickWidthUnit, d=holedLength, n='base')
    cmds.move((holedLength / 2.0), moveZ=True)
    cmds.polyBevel(ns+':base.e[0]', ns+':base.e[1]', ns+':base.e[2]', ns+':base.e[3]', segments=4, offset=0.3)
    for i in range(size):
        cmds.polyCylinder(r=g_holeRadUnit, h=g_brickWidthUnit)
        cmds.rotate(0,0,90)
        cmds.move((i * g_brickWidthUnit) + (g_brickWidthUnit/2.0), moveZ=True, a=True)
    cmds.polyCBoolOp(ns+':base', ns+':pCylinder*', op=2, ch=False, n='piece')[0]
    
    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.delete(ch=True)
    cmds.select(ns+':*')
    cmds.hyperShade(assign=(ns+":brckMat"))
    
    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)

def makeTechnicBrick():

    size = int(cmds.optionMenu('holedLengthMenu', q=True, v=True).replace("L",""))
    rgb = cmds.colorSliderGrp('holedTechnicColour', q=True, rgbValue=True)
    ns = "HoledTechnic" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    length = g_brickWidthUnit * size
    height = g_brickHeightUnit * 3

    cmds.polyCube(h=height, w=g_brickWidthUnit, d=length, n='base')
    cmds.move((length / 2.0), moveZ=True)
    for i in range(size):
        cmds.polyCylinder(r=g_studRadUnit, h=g_studHeightUnit, n="stud")
        cmds.move(
            0,
            (height/2.0 + 0.10), 
            (i * g_brickWidthUnit + g_brickWidthUnit * 0.5),
        )
        if not i: continue
        cmds.polyCylinder(r=g_studRadUnit, h=g_brickWidthUnit)
        cmds.rotate(0, 0, 90)
        cmds.move(0, 0, g_brickWidthUnit * i)

    cmds.polyCBoolOp(ns+':base', ns+':pCylinder*', op=2, ch=False, n='piece')[0]
    
    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.delete(ch=True)
    cmds.select(ns+':*')
    cmds.hyperShade(assign=(ns+":brckMat"))
    cmds.polyUnite(ch=False)
    
    cmds.namespace(removeNamespace=":"+ns,mergeNamespaceWithParent=True)

def makeTechnicTire():
    ns = "TechnicTire" + str(rnd.randint(1000, 9999))

    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    tireOuterR = g_brickWidthUnit * 1.5
    tireInnerR = g_brickWidthUnit * 0.85
    tireWidth  = g_brickWidthUnit * 1.2
    treadH     = g_brickWidthUnit * 0.28
    treadW     = g_brickWidthUnit * 0.28
    numTreads  = 16

    outer = cmds.polyCylinder(r=tireOuterR, h=tireWidth, sa=32, sh=1, sc=0, n='tireOuter')[0]
    cmds.rotate(90, 0, 0)
    cmds.makeIdentity(apply=True)

    cmds.polyBevel(ns+':tireOuter.e[0:31]', segments=2, offset=0.12, worldSpace=True)
    cmds.polyBevel(ns+':tireOuter.e[32:63]', segments=2, offset=0.12, worldSpace=True)
    cmds.delete(ch=True)

    inner = cmds.polyCylinder(r=tireInnerR, h=tireWidth * 1.1, sa=32, sh=1, sc=0, n='tireInner')[0]
    cmds.rotate(90, 0, 0)
    cmds.makeIdentity(apply=True)

    cmds.polyCBoolOp(ns+':tireOuter', ns+':tireInner', op=2, ch=False, n='tireTube')
    cmds.delete(ch=True)

    treadObjs = []
    for i in range(numTreads):
        angle = (360.0 / numTreads) * i
        rad = math.radians(angle)
        # centre of cube inner face on tireOuterR
        x = math.sin(rad) * (tireOuterR + treadH / 2.0)
        y = math.cos(rad) * (tireOuterR + treadH / 2.0)

        tread = cmds.polyCube(w=treadH, h=treadW, d=tireWidth * 0.6, n='tread'+str(i))[0]
        cmds.move(x, y, 0, a=True)
        cmds.rotate(0, 0, -angle)
        cmds.makeIdentity(apply=True)
        treadObjs.append(ns+':tread'+str(i))

    allParts = [ns+':tireTube'] + treadObjs
    cmds.polyUnite(*allParts, ch=False, n='tireFull')
    cmds.delete(ch=True)

    cmds.polyCylinder(r=tireInnerR * 0.93, h=tireWidth * 0.55, sa=16, sh=1, sc=0, n='rimOuter')[0]
    cmds.rotate(90, 0, 0)
    cmds.makeIdentity(apply=True)

    cmds.polyBevel(ns+':rimOuter.e[0:15]', segments=2, offset=0.1, worldSpace=True)
    cmds.polyBevel(ns+':rimOuter.e[16:31]', segments=2, offset=0.1, worldSpace=True)
    cmds.delete(ch=True)

    crossSpan = g_axleHoleUnit * 2.5
    crossThk  = g_axleHoleUnit

    xBar = cmds.polyCube(w=crossThk, h=crossSpan, d=tireWidth, n='crossX')[0]
    cmds.makeIdentity(apply=True)
    yBar = cmds.polyCube(w=crossSpan, h=crossThk, d=tireWidth, n='crossY')[0]
    cmds.makeIdentity(apply=True)

    cross = cmds.polyCBoolOp(ns+':crossX', ns+':crossY', op=1, ch=False, n='crossHole')[0]
    cmds.delete(ch=True)

    cmds.polyCBoolOp(ns+':rimOuter', ns+':crossHole', op=2, ch=False, n='rim')
    cmds.delete(ch=True)

    tireMat = cmds.shadingNode('lambert', asShader=True, name='tireMat')
    cmds.setAttr(ns+':tireMat.color', 0.05, 0.05, 0.05, typ='double3')

    rimMat = cmds.shadingNode('lambert', asShader=True, name='rimMat')
    cmds.setAttr(ns+':rimMat.color', 0.75, 0.75, 0.75, typ='double3')

    cmds.select(ns+':tireFull')
    cmds.hyperShade(assign=(ns+':tireMat'))
    cmds.select(ns+':rim')
    cmds.hyperShade(assign=(ns+':rimMat'))
    cmds.delete(ch=True)
    cmds.namespace(removeNamespace=':'+ns, mergeNamespaceWithParent=True)

def makeAngledLiftarm():
    import math
    lenA = cmds.intSliderGrp('angleLenA', q=True, v=True)
    lenB = cmds.intSliderGrp('angleLenB', q=True, v=True)
    deg  = int(cmds.optionMenu('angleDeg', q=True, v=True))
    rgb  = cmds.colorSliderGrp('holedTechnicColour', q=True, rgbValue=True)
    ns   = "AngledLiftarm" + str(rnd.randint(1000, 9999))
    cmds.select(clear=True)
    cmds.namespace(add=ns)
    cmds.namespace(set=ns)

    armW      = g_brickWidthUnit * 0.9
    armH      = g_brickWidthUnit * 0.9
    lengthA   = g_brickWidthUnit * lenA
    lengthB   = g_brickWidthUnit * lenB
    rotY      = 180 - deg

    junctionZ = lengthA - (g_brickWidthUnit / 2.0)

    bodyLenA = junctionZ
    cmds.polyCube(h=armH, w=armW, d=bodyLenA, n='armA')
    cmds.polyBevel(ns+':armA.e[0]', ns+':armA.e[1]',
                   ns+':armA.e[2]', ns+':armA.e[3]', segments=3, offset=0.28)
    cmds.delete(ch=True)
    cmds.rotate(0, 0, 90, ns+':armA', a=True)
    cmds.makeIdentity(ns+':armA', apply=True, t=True, r=True, s=True)
    cmds.move(0, 0, bodyLenA / 2.0, ns+':armA', a=True)

    startB = junctionZ - (g_brickWidthUnit / 2.0)
    cmds.polyCube(h=armH, w=armW, d=lengthB, n='armB')
    cmds.polyBevel(ns+':armB.e[0]', ns+':armB.e[1]',
                   ns+':armB.e[2]', ns+':armB.e[3]', segments=3, offset=0.28)
    cmds.delete(ch=True)
    cmds.rotate(0, 0, 90, ns+':armB', a=True)
    cmds.makeIdentity(ns+':armB', apply=True, t=True, r=True, s=True)
    cmds.move(0, 0, startB + lengthB / 2.0, ns+':armB', a=True)
    cmds.rotate(0, rotY, 0, ns+':armB', pivot=(0, 0, junctionZ), a=True)

    cmds.polyUnite(ns+':armA', ns+':armB', ch=False, n='armFull')
    cmds.delete(ch=True)
    cmds.makeIdentity(ns+':armFull', apply=True, t=True, r=True, s=True)

    cutters = []

    for i in range(lenA):
        zPos  = (i * g_brickWidthUnit) + (g_brickWidthUnit / 2.0)
        hName = 'holeA' + str(i)
        cmds.polyCylinder(r=g_holeRadUnit, h=armH * 2.0, sa=12, sh=1, sc=0, n=hName)
        cmds.move(0, 0, zPos, ns+':'+hName, a=True)
        cmds.makeIdentity(ns+':'+hName, apply=True, t=True, r=True, s=True)
        cutters.append(ns+':'+hName)

    for i in range(1, lenB):
        localZ   = i * g_brickWidthUnit
        hxOffset = math.sin(math.radians(rotY)) * localZ
        hzOffset = math.cos(math.radians(rotY)) * localZ
        hName    = 'holeB' + str(i)
        cmds.polyCylinder(r=g_holeRadUnit, h=armH * 2.0, sa=12, sh=1, sc=0, n=hName)
        cmds.rotate(0, rotY, 0, ns+':'+hName, a=True)
        cmds.move(hxOffset, 0, junctionZ + hzOffset, ns+':'+hName, a=True)
        cmds.makeIdentity(ns+':'+hName, apply=True, t=True, r=True, s=True)
        cutters.append(ns+':'+hName)

    cmds.polyCBoolOp(ns+':armFull', *cutters, op=2, ch=False, n='liftarm')
    cmds.delete(ch=True)
    cmds.xform(ns+':liftarm', centerPivots=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name='angledMat')
    cmds.setAttr(ns+':angledMat.color', rgb[0], rgb[1], rgb[2], typ='double3')
    cmds.select(ns+':liftarm')
    cmds.hyperShade(assign=(ns+':angledMat'))
    cmds.delete(ch=True)
    cmds.namespace(removeNamespace=':'+ns, mergeNamespaceWithParent=True)