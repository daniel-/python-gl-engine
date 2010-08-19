#!BPY
# coding: utf-8
""" 
Name: 'My XML (.xml)...'
Blender: 243
Group: 'Export'
Tooltip: 'Export to mx XML file format (.xml).'
"""

__author__ = ["Daniel Beßler"]
__url__ = ("blenderartists.org", "www.blender.org", "www.gametutorials.com")
__version__ = "0.1a"
__bpydoc__ = """\

My XML Exporter

This script Exports a XML file.
"""

from math import pi

import Blender
from Blender import NMesh
from Blender import Image
from array import array
import string
import os,sys
from Blender.Draw import *
from Blender.BGL import *
from Blender.Mathutils import *

from PIL import Image
import numpy

print dir(Blender)
print dir(Blender.Image)
print Blender.Image.Get.__doc__


DEFAULT_OUT_DIR = "/home/daniel/"
outFile = None

def setOutFile(name):
    global outFile
    if outFile!=None:
        outFile.close()
    outFile = open(DEFAULT_OUT_DIR + name, 'w')

def printXML(xml):
    global outFile
    print >>outFile, xml

def pointbymatrix(p, m):
    return [p[0] * m[0][0] + p[1] * m[1][0] + p[2] * m[2][0] + m[3][0],
			p[0] * m[0][1] + p[1] * m[1][1] + p[2] * m[2][1] + m[3][1],
			p[0] * m[0][2] + p[1] * m[1][2] + p[2] * m[2][2] + m[3][2]]

numCreatedTextures = 0
loadedImages = []

def createTextureImage(evalTex, imageName, size=(512,512), useAlpha=False):
    if imageName in loadedImages:
        return
    loadedImages.append(imageName)
    
    print "evaluating texture %s" % imageName
    
    w,h=size
    img = numpy.empty((w,h),numpy.uint32)
    img.shape=h,w
    
    scaleCord = 2.0
    for x in range(w):
        xf = (0.5 - float(x)/float(w)) * scaleCord
        for y in range(h):
            yf = -(0.5 - float(y)/float(h)) * scaleCord
            # evaluate color of texture
            (r,g,b,a) = map( lambda x: long(255.0*x), evalTex((yf, xf, 0)) )
            
            if useAlpha:
                # FIXME: semi transparenz not working?
                color = r | g | b | a
            elif r==0L and g==0L and b==0L:
                # black/white texture
                ir = a
                ig = a<<8
                ib = a<<16
                color = ir | ig | ib | 255<<24
            else:
                # colored texture
                # TODO: what todo with intensity here?
                g = g<<8
                b = b<<16
                color = r | g | b | 255<<24
                
            img[x,y] = color
    
    # render to file... yippieh
    image = Image.frombuffer("RGBA", (w,h), img, 'raw', "RGBA", 0, 1)
    image.save(imageName)

def mesh2XML(oname, mesh, matrix):
    vertices = {}
    normals = {}
    uvcos = {}
    faces = {}
    materialNames = []
    
    # remember used materials
    for material in mesh.materials:
        materialNames.append(material.name)

    if len(materialNames) == 0:
        print "WARNING: skipping mesh without material."
        return
    
    useUVCOS = False
    for edge in mesh.edges:
        # vertex coordinates
        vertices[edge.v1.index] = pointbymatrix(edge.v1.co, matrix)
        vertices[edge.v2.index] = pointbymatrix(edge.v2.co, matrix)
        # normal coordinates
        normals[edge.v1.index] = tuple(edge.v1.no)
        normals[edge.v2.index] = tuple(edge.v2.no)
        # the vertex texture 'sticky' coordinates
        uvcos[edge.v1.index] = tuple(edge.v1.uvco)
        if tuple(edge.v1.uvco) != (0.0, 0.0):
            useUVCOS = True
        uvcos[edge.v2.index] = tuple(edge.v2.uvco)
        if tuple(edge.v2.uvco) != (0.0, 0.0):
            useUVCOS = True

    print "INFO:   mesh has %d vertices." % len(vertices)   

    faceIndex = 0
    for face in mesh.faces:
        indexes = []
        # image used as texture
        faceImage = face.image
        # list of vertex colors
        vertexColors = face.col
        # uv coordinates
        textureCord = face.uv

        # TODO: face option
        #if(face.smooth != 0): f.smooth_lit = 1
        #if(face.mode & Blender.NMesh.FaceModes.TWOSIDE): f.double_sided = 1

        def processFace(f, (i,j,k)):
            faces[f] = {}
            try:
                faces[f]['material'] = materialNames[face.materialIndex]
            except:
                print "WARNING: skipping face with invalid material index %d." % face.materialIndex
                return
            if faceImage!=None:
                (w,h) = faceImage.getSize()
                
                imageName = faceImage.getName()
                imageName = imageName[:imageName.rfind('.')] + ".png"
                
                faces[f]['image'] = imageName
                
                # dump image
                def evalImage((x,y,_)):
                    (x,y) = int(0.5*(x+1.0)*w), int(0.5*(y+1.0)*h)-1
                    return faceImage.getPixelF(x, y)
                createTextureImage(evalImage, imageName, size=(w,h), useAlpha=True)
                
            faces[f]['indexes'] = [face.v[i].index, face.v[j].index, face.v[k].index]
            if vertexColors!=[]:
                faces[f]['vertexColors'] = [
                        (vertexColors[i].r, vertexColors[i].g, vertexColors[i].b, vertexColors[i].a),
                        (vertexColors[j].r, vertexColors[j].g, vertexColors[j].b, vertexColors[j].a),
                        (vertexColors[k].r, vertexColors[k].g, vertexColors[k].b, vertexColors[k].a) ]
            if textureCord!=[]:
                faces[f]['uv'] = [textureCord[i], textureCord[j], textureCord[k]]
        
        # list of face vertices
        processFace(faceIndex, (0,1,2))
        if len(face) == 4:
            # split quad faces into triangle faces
            faceIndex += 1
            processFace(faceIndex, (0,2,3))
        faceIndex += 1

    segmentMaterial = None
    segmentImage = None    
    
    # write to file
    printXML ('<segment id="%s" type="vertexArray">' % oname)
    printXML ('    <vertices>')
    for i in vertices.keys():
        if useUVCOS:
            printXML ('        <v index="%i" co="%s" no="%s" uvco="%s" />' % \
                (i, str(vertices[i]), str(normals[i]), str(uvcos[i])))
        else:
            printXML ('        <v index="%i" co="%s" no="%s" />' % \
                (i, str(vertices[i]), str(normals[i])))
    printXML ('    </vertices>')
    # TODO: support quad faces.
    #       tangent calculation currently only works for plane faces,
    #       if any polygon qaud is allowed, the tangent calculation must honor this.
    printXML ('    <faces type="triangles" >')
    for faceIndex in faces.keys():
        printXML ('        <face id="%i">' % faceIndex)
        face = faces[faceIndex]
        for key in face.keys():
            if key=="material":
                if segmentMaterial==None:
                    segmentMaterial = face[key]
                elif segmentMaterial != face[key]:
                    print "WARNING: segment has different materials defined (%s and %s), this is not supported." % (segmentMaterial, face[key])
            elif key=="image":
                if segmentImage==None:
                    segmentImage = face[key]
                elif segmentImage != face[key]:
                    print "WARNING: segment has different images defined (%s and %s), this is not supported." % (segmentMaterial, face[key])
            elif key=="indexes":
                printXML ('            <i val="%s" />' % str(tuple(face[key])))
            elif key=="vertexColors":
                printXML ('            <col val="%s" />' % str(face[key]))
            elif key=="uv":
                printXML ('            <uv val="%s" />' % str(face[key]))
            else:
                print "unknown face key " + key
        printXML ('        </face>')
    printXML ('    </faces>')
    printXML ('</segment>')
    
    return (segmentMaterial, segmentImage)

def materialToXML(material):
    global numCreatedTextures
    
    textures = []
    alpha = material.alpha
    # amount of ambient color
    amb = material.amb
    # diffuse light
    diffuse = (
        (material.ref+material.emit)*material.R,
        (material.ref+material.emit)*material.G,
        (material.ref+material.emit)*material.B, 1.0)
    # specular light
    specular = (
        material.spec*material.specR,
        material.spec*material.specG,
        material.spec*material.specB, 1.0)
    hard = material.hard

    for texture in material.textures:
        if texture==None: continue
        
        textureMap = {}
        
        if texture.tex.type == Blender.Texture.Types.IMAGE:
            if texture.tex.image==None:
                textureMap['image'] = None
            else:
                imageName = texture.tex.image.getName()
                # force png output
                imageName = imageName[:imageName.rfind('.')] + ".png"
                
                textureMap['image'] = imageName
                createTextureImage(texture.tex.evaluate, imageName)
        else:
            # there are some blender generated textures: noise,magic,.. export them too!
            texName = "texture%d.png" % numCreatedTextures
            textureMap['image'] = texName
            createTextureImage(texture.tex.evaluate, texName)
            numCreatedTextures += 1
        
        # amount texture affects color values
        textureMap['colfac'] = texture.colfac
        # invert texture values
        textureMap['neg'] = texture.neg
        # texture color (TODO only used for noRGB ??)
        textureMap['col'] = texture.col
        # texture color (TODO only used for noRGB ??)
        textureMap['rgbCol'] = texture.tex.rgbCol
        # use this texture as blending value for next texture
        textureMap['stencil'] = texture.stencil
        # With this option, an RGB texture (affects color) is used as an Intensity texture (affects a value)
        textureMap['noRGB'] = texture.noRGB
        # texture affects cord of next texture (only for warp mode)
        textureMap['warpfac'] = texture.warpfac
        # generate mipmaps
        textureMap['mipmaps'] = texture.tex.mipmap
        # texture brightness
        textureMap['brightness'] = texture.tex.brightness
        # texture contrast
        textureMap['contrast'] = texture.tex.contrast
        # texture effects normals with this factor (only for nor mode)
        textureMap['norfac'] = texture.norfac
        # amount the texture displaces the surface (only for disp mode)
        textureMap['dispfac'] = texture.dispfac
        # used for no RGB
        # texture.dvar
        # texture.varfac
        # TODO: not sure howto use colorbands
        # print texture.tex.colorband
        
        # texture blending modes
        blendMode = texture.blendmode
        if blendMode == Blender.Texture.BlendModes.MIX:
            textureMap['blendMode'] = "mix"
        elif blendMode == Blender.Texture.BlendModes.MULTIPLY:
            textureMap['blendMode'] = "mul"
        elif blendMode == Blender.Texture.BlendModes.ADD:
            textureMap['blendMode'] = "add"
        elif blendMode == Blender.Texture.BlendModes.SUBSTRACT:
            textureMap['blendMode'] = "sub"
        elif blendMode == Blender.Texture.BlendModes.DIVIDE:
            textureMap['blendMode'] = "div"
        elif blendMode == Blender.Texture.BlendModes.DIFFERENCE:
            textureMap['blendMode'] = "diff"
        elif blendMode == Blender.Texture.BlendModes.LIGHTEN:
            textureMap['blendMode'] = "light" # choose the lighter pixel color
        elif blendMode == Blender.Texture.BlendModes.DARKEN:
            textureMap['blendMode'] = "dark" # choose the darker pixel color
        elif blendMode == Blender.Texture.BlendModes.SCREEN:
            textureMap['blendMode'] = "screen"
        elif blendMode == Blender.Texture.BlendModes.OVERLAY:
            textureMap['blendMode'] = "overlay"
        elif blendMode == Blender.Texture.BlendModes.HUE:
            textureMap['blendMode'] = "hue"
        elif blendMode == Blender.Texture.BlendModes.SATURATION:
            textureMap['blendMode'] = "sat"
        elif blendMode == Blender.Texture.BlendModes.VALUE:
            textureMap['blendMode'] = "val"
        elif blendMode == Blender.Texture.BlendModes.COLOR:
            textureMap['blendMode'] = "col"
        else:
            print "WARNING: unknown blend mode " + str(blendMode) + "."
        
        # The different aspects of a material that a texture influences are controlled by mapTo. 
        mapTo = texture.mapto
        textureMap['mapTo'] = []
        if mapTo & Blender.Texture.MapTo.COL:
            textureMap['mapTo'].append("col")
        if mapTo & Blender.Texture.MapTo.NOR:
            if texture.mtNor==1:
                textureMap['mapTo'].append("nor")
            else:
                textureMap['mapTo'].append("-nor")
        if mapTo & Blender.Texture.MapTo.ALPHA:
            if texture.mtAlpha==1:
                textureMap['mapTo'].append("alpha")
            else:
                textureMap['mapTo'].append("-alpha")
        if mapTo & Blender.Texture.MapTo.CSP:
            textureMap['mapTo'].append("csp")
        if mapTo & Blender.Texture.MapTo.CMIR:
            textureMap['mapTo'].append("cmir")
        if mapTo & Blender.Texture.MapTo.REF:
            if texture.mtRef==1:
                textureMap['mapTo'].append("ref")
            else:
                textureMap['mapTo'].append("-ref")
        if mapTo & Blender.Texture.MapTo.SPEC:
            if texture.mtSpec==1:
                textureMap['mapTo'].append("spec")
            else:
                textureMap['mapTo'].append("-spec")
        if mapTo &Blender.Texture.MapTo.HARD:
            if texture.mtHard==1:
                textureMap['mapTo'].append("hard")
            else:
                textureMap['mapTo'].append("-hard")
        if mapTo & Blender.Texture.MapTo.EMIT:
            if texture.mtEmit==1:
                textureMap['mapTo'].append("emit")
            else:
                textureMap['mapTo'].append("-emit")
        if mapTo & Blender.Texture.MapTo.RAYMIR:
            if texture.mtRayMir==1:
                textureMap['mapTo'].append("raymir")
            else:
                textureMap['mapTo'].append("-raymir")
        if mapTo & Blender.Texture.MapTo.DISP:
            if texture.mtDisp==1:
                textureMap['mapTo'].append("disp")
            else:
                textureMap['mapTo'].append("-disp")
        if mapTo & Blender.Texture.MapTo.TRANSLU:
            if texture.mtTranslu==1:
                textureMap['mapTo'].append("translu")
            else:
                textureMap['mapTo'].append("-translu")
        if mapTo & Blender.Texture.MapTo.AMB:
            if texture.mtAmb==1:
                textureMap['mapTo'].append("amb")
            else:
                textureMap['mapTo'].append("-amb")
        if mapTo & Blender.Texture.MapTo.WARP:
            textureMap['mapTo'].append("warp")
        
        # 2D to 3D Mapping
        mapping = texture.mapping
        if mapping == Blender.Texture.Mappings.FLAT:
            textureMap['mapping'] = "flat"
        elif mapping == Blender.Texture.Mappings.CUBE:
            textureMap['mapping'] = "cube"
        elif mapping == Blender.Texture.Mappings.TUBE:
            textureMap['mapping'] = "tube"
        elif mapping == Blender.Texture.Mappings.SPHERE:
            textureMap['mapping'] = "sphere"
        else:
            print "WARNING: unknown mapping mode " + str(mapping) + "."
        
        # Textures need mapping coordinates, to determine how they are applied to geometry. The mapping specifies how the texture will ultimately wrap  itself to the object. For example, a 2D image texture could be configured to wrap itself around a cylindrical shaped object. 
        mapInputMode = texture.texco
        if mapInputMode == Blender.Texture.TexCo.GLOB:
            textureMap['mapInput'] = "glob"
            # The scene's Global 3D coordinates. This is also usefull for animations; if you move the object, the texture moves across it. It can be useful for letting objects appear or disappear at a certain position in space. 
        elif mapInputMode == Blender.Texture.TexCo.OBJECT:
            textureMap['mapInput'] = "object"
            # Uses a child Object's texture space as source of coordinates. The Object name must be specified in the text button on the right. Often used with Empty objects, this is an easy way to place a small image as a logo or decal at a given point on the object (see the example below). This object can also be animated, to move a texture around or through a surface 
        elif mapInputMode == Blender.Texture.TexCo.UV:
            textureMap['mapInput'] = "uv"
            # Each vertex of a mesh has its own UV co-ordinates which can be unwrapped and laid flat like a skin
        elif mapInputMode == Blender.Texture.TexCo.ORCO:
            textureMap['mapInput'] = "orco"
            # "Original Co-ordinates" - The object's local texture space. This is the default option for mapping textures. 
        elif mapInputMode == Blender.Texture.TexCo.STICK:
            textureMap['mapInput'] = "stick"
            # Uses a mesh's sticky coordinates, which are a form of per-vertex UV co-ordinates. If you have made Sticky co-ordinates first (F9  Mesh Panel, Sticky Button), the texture can be rendered in camera view (so called "Camera Mapping"). 
        elif mapInputMode == Blender.Texture.TexCo.WIN:
            textureMap['mapInput'] = "win"
            # The rendered image window coordinates. This is well suited to blending two objects. 
        elif mapInputMode == Blender.Texture.TexCo.NOR:
            textureMap['mapInput'] = "nor"
            # Uses the direction of the surface's normal vector as coordinates. This is very useful when creating certain special effects that depend on viewing angle 
        elif mapInputMode == Blender.Texture.TexCo.REFL:
            textureMap['mapInput'] = "refl"
            # Uses the direction of the reflection vector as coordinates. This is useful for adding reflection maps - you will need this input when Environment Mapping.
        else:
            print "WARNING: unknown map input mode " + str(mapInputMode) + "."
        
        textures.append(textureMap)
    
    # write to file
    printXML ('<material id="%s">' % material.name)
    printXML ('    <diffuse val="%s" />' % str(diffuse))
    printXML ('    <specular val="%s" />' % str(specular))
    printXML ('    <ambient val="%s" />' % str(amb))
    printXML ('    <shininess val="%s" />' % str(hard))
    for m in textures:
        textureStr = 'col="%s" ' % str(m['col'])
        textureStr += 'stencil="%s" ' % str(m['stencil'])
        textureStr += 'blendMode="%s" ' % str(m['blendMode'])
        textureStr += 'mapping="%s" ' % str(m['mapping'])
        textureStr += 'mapTo="%s" ' % str(m['mapTo'])
        textureStr += 'mapInput="%s" ' % str(m['mapInput'])
        textureStr += 'image="%s" ' % str(m['image'])
        textureStr += 'rgbCol="%s" ' % str(m['rgbCol'])
        textureStr += 'noRGB="%s" ' % str(m['noRGB'])
        textureStr += 'colfac="%s" ' % str(m['colfac'])
        textureStr += 'norfac="%s" ' % str(m['norfac'])
        textureStr += 'warpfac="%s" ' % str(m['warpfac'])
        textureStr += 'dispfac="%s" ' % str(m['dispfac'])
        textureStr += 'mipmaps="%s" ' % str(m['mipmaps'])
        textureStr += 'brightness="%s" ' % str(m['brightness'])
        textureStr += 'contrast="%s" ' % str(m['contrast'])
        textureStr += 'neg="%s" ' % str(m['neg'])
        
        printXML ('    <texture %s />' % textureStr)
    printXML ('</material>\n')
    

# gui vars
outdir = Create('')

def initGUI():
    # event constants
    exportevt = 1
    outevt = 2
    mnameevt = 3  
    
    def gui():
        global outdir
        glClearColor(0.5,0.5,0.5, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glRasterPos2i(40, 70)

        Text("Export objects to XML format ")
        Button("Start export!", exportevt, 40, 40, 150, 19)
        glColor3f(1,1,1)
        outdir = String("Output Dir: ",outevt,40,110,400,19,DEFAULT_OUT_DIR,220)
            
    def event(evt, val):
        if (evt == ESCKEY and not val): Exit()

    def bevent(evt):
        if (evt ==  exportevt): doExport()

    Register(gui, event, bevent)


def doExport():
    print "\n************* EXPORT START **************\n"

    segmentData = []
    
    Blender.Redraw() # Needed for GetRawFromObject
    
    # create the path if it doesn't exist
    if (not os.path.exists(outdir.val)):
        os.mkdir(outdir.val)

    """
    # from blend2soya
	if self.animation:
		for obj in objs:
			data = obj.getData()
			if (type(data) is Blender.Types.ArmatureType):
				scene     = Blender.Scene.getCurrent()
				#armature  = Blender.Armature.Get()[0]
				armature  = obj
				animation = Blender.Armature.NLA.GetActions()[self.animation]
				
				animation.setActive(armature)

				scene.getRenderingContext().currentFrame(int(self.animation_time))
				scene.makeCurrent()
    """
    
    # blender objects to xml
    print "INFO: exporting objects..."
    setOutFile('segments.xml')
    printXML ('<segments>')
    for o in Blender.Object.Get():
        oName = str(o.getName())
        
        # TODO support different draw modes
        drawMode = o.getDrawMode()
        # TODO: mode constants
        if drawMode==0:
            drawMode = "textured"
        else:
            print "WARNING: unknown draw mode '%s'." % str(drawMode)
        
        # transformation matrix
        matR = [[o.mat[0][0], o.mat[0][1], o.mat[0][2], o.mat[0][3]],
                [o.mat[1][0], o.mat[1][1], o.mat[1][2], o.mat[1][3]],
                [o.mat[2][0], o.mat[2][1], o.mat[2][2], o.mat[2][3]],
                [o.mat[3][0], o.mat[3][1], o.mat[3][2], o.mat[3][3]]]
        
        otype = o.getType()
        if otype == "Lamp" or otype == "Camera":
            continue
        elif otype == "Armature":
            print "WARNING: armatures/bones not supported."
        elif otype == "Mesh":
            print "INFO: exporting mesh '%s'." % oName
            # get raw object retrieves vertex data as rendered on the screen,
            # with modifiers applied.
            nmesh = Blender.NMesh.GetRawFromObject(o.getName())
            (segmentMaterial, segmentImage) = mesh2XML(o.getName(), nmesh, matR)
            segmentData.append((oName, segmentMaterial, segmentImage))
        else:
            print "WARNING: unknown blender object type: '%s'" % otype
    printXML ('</segments>')
    
    # materials to xml
    print "INFO: exporting materials..."
    setOutFile('materials.xml')
    printXML ('<materials>')
    for m in Blender.Material.Get():
        materialToXML(m)
    printXML ('</materials>')
    
    # scene to xml
    print "INFO: exporting scene..."
    setOutFile('models.xml')
    printXML ('<models>')
    printXML ('<model id="export">')
    for (n,mat,image) in segmentData:
        printXML ('    <segment id="%s">' % n)
        if image!=None:
            printXML ('        <image val="%s" />' % image)
        if mat!=None:
            printXML ('        <material name="%s" />' % mat)
        printXML ('    </segment>\n')
    printXML ('</model>')
    printXML ('</models>')

    if outFile!=None:
        outFile.close()
    
    print "\n************* EXPORT STOP  **************\n"

initGUI()

