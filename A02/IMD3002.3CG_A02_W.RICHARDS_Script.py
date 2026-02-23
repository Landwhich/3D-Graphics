import maya.cmds as cmds
import random as rnd

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

# Curved Technic Triangle
cmds.frameLayout(collapsable=True, label="Technic Misc", width=475)
cmds.columnLayout()

cmds.colorSliderGrp('larmColour', label="Color", hsv=(3,0.9,.75))
cmds.button(label="Create Curved L-Liftarm", command=('makeCurvedL()'))

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
    
### Brick Size Globals: 

g_brickWidthUnit = 0.8
g_brickHeightUnit = 0.32
g_studRadUnit = 0.25
g_studHeightUnit = 0.2
g_holeRadUnit = 0.26
g_axleUnit = 0.1
g_axleHoleUnit = 0.11


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
    
def makeCurvedL():
    rgb = cmds.colorSliderGrp('larmColour', q=True, rgbValue=True)
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
            xAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_studRadUnit, d=(g_brickHeightUnit))[0]
            cmds.rotate(0, 0, 90)
            yAxle = cmds.polyCube(w=g_axleHoleUnit, h=g_studRadUnit, d=(g_brickHeightUnit))[0]
            cutter = cmds.polyCBoolOp(xAxle, yAxle, op=1, ch=False)[0]
            cmds.rotate(90, 0, 0)
            cmds.delete(ch=True)
        cmds.move(hole[1], 0, hole[3])
        cmds.polyCBoolOp(ns+':frame'+str(i), cutter, op=2, n='frame'+str(i+1))
        cmds.delete(ch=True)
        i += 1
        
    mat = cmds.shadingNode("lambert", asShader=True, name="larmMat")
    cmds.setAttr(ns+":larmMat.color", rgb[0], rgb[1], rgb[2], typ="double3")
        
    cmds.polyBevel( ns+':frame'+str(i)+'.e[166]', segments=4, offset=0.4 )
    cmds.polyBevel( ns+':frame'+str(i)+'.e[167]', segments=4, offset=0.4 )
    cmds.polyBevel( ns+':frame'+str(i)+'.e[166]', segments=4, offset=0.4 )
    cmds.select(ns+":*")

    # Material
    cmds.hyperShade(assign=(ns+":larmMat"))
    cmds.delete(ch=True)
    cmds.namespace(removeNamespace=":"+ns, mergeNamespaceWithParent=True)