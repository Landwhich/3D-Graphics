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

#Standard Brick
cmds.frameLayout(collapsable=True, label="Standard Brick", width=475, height=140)
cmds.columnLayout()
cmds.intSliderGrp('brickHeight', l="Height", f=True, min=1, max=20, value=3)
cmds.intSliderGrp('brickWidth', l="Width (Bumps)", f=True, min=1, max=20, value=2)
cmds.intSliderGrp('brickDepth', l="Depth (Bumps)", f=True, min=1, max=20, value=8)
cmds.colorSliderGrp('brickColour', label="Color", hsv=(256, 1, 1))

cmds.columnLayout()
cmds.button(label="Get Bricked", command=('basicBrick()'))
cmds.setParent('..')
cmds.setParent('..')

#Sloped Brick
cmds.frameLayout(collapsable=True, label="Sloped Brick", width=475, height=160)
cmds.columnLayout()
cmds.intSliderGrp('slopedWidth', l="Width (Bumps)", f=True, min=1, max=20, v=4)
cmds.intSliderGrp('slopedDepth', l="Depth (Bumps)", f=True, min=2, max=4, v=2)
cmds.colorSliderGrp('slopedColour', l="Colour", hsv=(12,1,1))

cmds.columnLayout()
cmds.button(label="Make Sloped Brick", command=('slopedBrick()'))
cmds.setParent( '..' )

cmds.setParent( '..' )
cmds.setParent( '..' )

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

    brickSizeX = brickWidth * 0.8
    brickSizeZ = brickDepth * 0.8
    brickSizeY = brickHeight * 0.32

    cmds.polyCube(h=brickSizeY, w=brickSizeX, d=brickSizeZ)
    cmds.move((brickSizeY / 2.0), moveY=True)
    for i in range(brickWidth):
        for j in range(brickDepth):
            cmds.polyCylinder(r=0.25, h=0.20)
            cmds.move((brickSizeY + 0.10), moveY=True, a=True)
            cmds.move(((i * 0.8) - (brickSizeX/2.0) + 0.4), moveX=True, a=True)
            cmds.move(((j * 0.8) - (brickSizeZ/2.0) + 0.4), moveZ=True, a=True)

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

    brickSizeX = brickWidth * 0.8
    brickSizeZ = brickDepth * 0.8
    brickSizeY = brickHeight * 0.32

    cmds.polyCube(h=brickSizeY, w=brickSizeX, d=brickSizeZ, sz=brickDepth)
    cmds.move((brickSizeY / 2.0), y=True, a=True)
    for i in range(brickWidth):
        cmds.polyCylinder(r=0.25, h=0.20)
        cmds.move((brickSizeY + 0.10), moveY=True, a=True)
        cmds.move(((i * 0.8) - (brickSizeX/2.0) + 0.4), moveX=True, a=True)
        cmds.move((0 - (brickSizeZ/2.0) + 0.4), moveZ=True)

    myShader = cmds.shadingNode('lambert', asShader=True, name="brckMat")
    cmds.setAttr(ns+":brckMat.color", rgb[0], rgb[1], rgb[2], typ='double3')

    cmds.polyUnite((ns+":*"), n=ns, ch=False)
    cmds.delete(ch=True)

    cmds.hyperShade(assign=(ns+":brckMat"))

    cmds.select((ns+":"+ns+".e[1]"), r=True)
    cmds.move(0, -0.8, 0, r=True)

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