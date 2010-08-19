# -*- coding: UTF-8 -*-
'''
Created on 02.06.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader.shader_utils import FragShaderFunc, VertShaderFunc
from core.light.light import Light

class PixelLightVert(VertShaderFunc):
    def __init__(self, app, lights, lightIndexes=None):
        VertShaderFunc.__init__(self, name='plight')
        self.app = app
        self.numLights = len(lights)
        self.lights = lights
        if lightIndexes==None:
            self.lightIndexes = range(self.numLights)
        else:
            self.lightIndexes = lightIndexes
        
        self.addVarying(type="vec3", name="lightVec[%d]" % self.numLights)
        self.addVarying(type="float", name="attenFacs[%d]" % self.numLights)
        self.addVarying(type="vec4", name="eyeVec")
        self.addVarying(type="vec3", name="positionVarying")
    
    def code(self):
        code = """
    /**
     * calculates light vector needed for per pixel lighting.
     **/
    void %s(vec4 v)
    {
        positionVarying = vertexPosition;
        // save the vertex vector in eye space
        eyeVec = v;
""" %  self.name
        
        for n in range(self.numLights):
            light = self.lights[n]
            
            type = light.getLightType()
            if type == Light.DIRECTIONAL_LIGHT:
                code += """
        // directional light
        lightVec[%(INDEX)d] = normalize( gl_LightSource[%(LIGHT)d].position.xyz );
""" % { 'LIGHT': self.lightIndexes[n], 'INDEX': n }
            elif type == Light.POINT_LIGHT:
                code += """
        // point light
        vec3 aux = vec3( gl_LightSource[%(LIGHT)d].position - v );
        lightVec[%(INDEX)d] = normalize( aux );
        
        float dist = length(aux);
        attenFacs[%(INDEX)d] = 1.0/(gl_LightSource[%(LIGHT)d].constantAttenuation + 
                    gl_LightSource[%(LIGHT)d].linearAttenuation * dist +
                    gl_LightSource[%(LIGHT)d].quadraticAttenuation * dist * dist );
""" % { 'LIGHT': self.lightIndexes[n], 'INDEX': n }
            else:
                code += """
        // spot light
        vec3 aux = vec3( gl_LightSource[%(LIGHT)d].position - v );
        lightVec[%(INDEX)d] = normalize( aux );
        
        float spotEffect = dot( normalize(
                gl_LightSource[%(LIGHT)d].spotDirection),
                normalize( -lightVec[%(INDEX)d] ));
        if (spotEffect > gl_LightSource[%(LIGHT)d].spotCosCutoff) {
            spotEffect = pow(spotEffect, gl_LightSource[%(LIGHT)d].spotExponent);
            float dist = length(aux);
            attenFacs[%(INDEX)d] = spotEffect / (gl_LightSource[%(LIGHT)d].constantAttenuation +
                        gl_LightSource[%(LIGHT)d].linearAttenuation * dist +
                        gl_LightSource[%(LIGHT)d].quadraticAttenuation * dist * dist);
        } else {
            attenFacs[%(INDEX)d] = 0.0;
        }
""" % { 'LIGHT': self.lightIndexes[n], 'INDEX': n }
        
        return code + """
    }
"""


class PixelLightFrag(FragShaderFunc):
    """
    this fragment shader function handles the light and shadow calculations.
    """
    
    getOccCoef = """
float getOccCoef(sampler2DArray map,
                 vec4 shadow_coord)
{
    // get the stored depth
    float shadow_d = texture2DArray(map, shadow_coord.xyz).x;
    
    // get the difference of the stored depth and the distance of this fragment to the light
    float diff = shadow_d - shadow_coord.w;
    
    // smoothen the result a bit, so that we don't get hard shadows
    return clamp( diff*250.0, 0.0, 1.0);
}
"""
    
    def __init__(self, app, lights, lightIndexes=None):
        FragShaderFunc.__init__(self, name='plight')
        self.app = app
        self.numLights = len(lights)
        self.lights = lights
        if lightIndexes==None:
            self.lightIndexes = range(self.numLights)
        else:
            self.lightIndexes = lightIndexes
        
        self.addVarying(type="vec3", name="lightVec[%d]" % self.numLights)
        self.addVarying(type="float", name="attenFacs[%d]" % self.numLights)
        self.addVarying(type="vec4", name="eyeVec")
        self.addVarying(type="vec3", name="positionVarying")
        
        # add stuff for shadows
        i = 0
        self.hasShadow = False
        for light in self.lights:
            if light.shadowMapArray == None: continue
            self.hasShadow = True
            numShadowMaps = len(light.shadowMapArray.shadowMaps)
            i += 1
            
            numVecs = len(light.shadowMapArray.farVecs)
            for j in range(numVecs):
                self.addUniform( type="vec%d" % light.shadowMapArray.farVecs[j], name="shadowFar%d%d" % (i-1,j) )
            #for j in range(len(light.shadowMapArray.shadowMaps)):
            self.addUniform( type="mat4", name="shadowNormalMat%d[%d]" % (i-1,numShadowMaps) )
            
            self.addUniform( type=light.shadowMapArray.textureType, name="shadowMap%d" % (i-1) )
            if light.shadowMapArray.textureType == "sampler2DArray":
                self.addDep("getOccCoef", PixelLightFrag.getOccCoef)
            
        if self.hasShadow:
            self.setMinVersion(130)
            self.enableExtension("GL_EXT_gpu_shader4")
    
    def shadowCode(self,
                   lightIndex,
                   shadowMapArray,
                   shadowMapArrayCount,
                   debugColors=False):
        """
        calculate the shadow factor
        0.0 means completely shadowed and 1.0 completely lit.
        """
        numMaps = len(shadowMapArray.shadowMaps)
        mapSize = shadowMapArray.sizeF
        kernel = shadowMapArray.kernel
        kernelOffset = shadowMapArray.kernelOffset
        
        j = 0
        space = ""
        getIndexCode = ""
        for i in range(len(shadowMapArray.farVecs)):
            v = shadowMapArray.farVecs[i]
            getIndexCode += """%sif (gl_FragCoord.z < shadowFar%d%d.x) {
                shadowMapIndex = %d;
            }""" % (space, shadowMapArrayCount, i, j)
            j += 1
            space = " else "
            if v>1:
                getIndexCode += """%sif (gl_FragCoord.z < shadowFar%d%d.y) {
                shadowMapIndex = %d;
            }""" % (space, shadowMapArrayCount, i, j)
                j += 1
            if v>2:
                getIndexCode += """%sif (gl_FragCoord.z < shadowFar%d%d.z) {
                shadowMapIndex = %d;
            }""" % (space, shadowMapArrayCount, i, j)
                j += 1
            if v>3:
                getIndexCode += """%sif (gl_FragCoord.z < shadowFar%d%d.w) {
                shadowMapIndex = %d;
            }""" % (space, shadowMapArrayCount, i, j)
                j += 1
        # remove last 3 lines and replace it with else statement
        getIndexCode = reduce(lambda x,y: x + "\n" + y, getIndexCode.split('\n')[:-3])
        getIndexCode += """
            } else {
                shadowMapIndex = %d;
            }""" % (j-1)
        
        if debugColors:
            getIndexCode += """
            vec4 color[8] = vec4[8](
                    vec4(1.0, 0.7, 0.7, 1.0),
                    vec4(0.7, 1.0, 0.7, 1.0),
                    vec4(1.0, 1.0, 0.7, 1.0),
                    vec4(0.7, 0.7, 1.0, 1.0),
                    vec4(1.0, 0.7, 1.0, 1.0),
                    vec4(0.7, 1.0, 1.0, 1.0),
                    vec4(1.0, 1.0, 1.0, 1.0),
                    vec4(0.7, 0.7, 0.7, 1.0));
            base *= color[shadowMapIndex];"""
        
        # use kernel for shadow lookup
        lookupKernel = ""
        for k in kernel:
            lookupKernel += """
            {
                shadowLookup = shadowCoord + vec4( %(x)f, %(y)f, %(z)f, %(w)f );
                shadowLookup.w = -(lightNormal.x*shadowLookup.x +
                                   lightNormal.y*shadowLookup.y + d)/lightNormal.z;
                _shadow += getOccCoef(%(MAP)s, shadowLookup);
            }""" % { 'MAP': "shadowMap%d" % shadowMapArrayCount,
        'x': kernelOffset * k[0],
        'y': kernelOffset * k[1],
        'z': kernelOffset * k[2],
        'w': kernelOffset * k[3] }
        if kernel!=[]:
            lookupKernel += "            _shadow = _shadow/%d;\n" % len(kernel)
        
        return """            // shadow map selection is done by distance of pixel to the camera.
            
            int shadowMapIndex;
            
            // find the appropriate depth map to look up in based on the depth of this fragment
            %(GET_INDEX)s
            
            // transform this fragment's position from view space to scaled light clip space
            // such that the xy coordinates are in [0;1]
            // note there is no need to divide by w for othogonal light sources
            vec4 shadowCoord = gl_TextureMatrix[ shadowMapIndex ] * eyeVec;
            
            // avoid light bleeding
            vec4 lightNormal4 = shadowNormalMat%(LIGHT)d[ shadowMapIndex ]*vec4(normalVarying, 0.0);
            vec3 lightNormal = normalize(lightNormal4.xyz);
            float d = -dot(lightNormal, shadowCoord.xyz);
            
            shadowCoord.w = shadowCoord.z;
            // tell glsl in which layer to do the look up
            shadowCoord.z = float(shadowMapIndex);
            
            // sum shadow samples    
            float _shadow = getOccCoef(%(MAP)s, shadowCoord);
            vec4 shadowLookup;
            %(LOOKUP_KERNEL)s
            shadow += _shadow;
""" % { 'NUM_MAPS': numMaps,
        'FAR_ARRAY': "FAR_ARRAY",
        'MAP': "shadowMap%d" % shadowMapArrayCount,
        'TEX_SIZE0': mapSize,
        'TEX_SIZE1': 1.0/mapSize,
        'GET_INDEX': getIndexCode,
        'LOOKUP_KERNEL': lookupKernel,
        'LIGHT': lightIndex }
    
    def ambientLightCode(self, lightInstance, lightIndex):
        """
        get the ambient term for this light.
        """
        type = lightInstance.getLightType()
        
        if type == Light.DIRECTIONAL_LIGHT:
            return "ambient += gl_FrontLightProduct[%(i)d].ambient;" % { 'i': lightIndex }
        elif type == Light.POINT_LIGHT or type == Light.SPOT_LIGHT:
            return "ambient += attenFacs[%(i)d] * gl_FrontLightProduct[%(i)d].ambient;" % { 'i': lightIndex }
        else:
            raise ValueError, "Unknown light type!"
    
    def lightCode(self, lightInstance, lightIndex):
        """
        get the diffuse and specular term for this light.
        """
        
        type = lightInstance.getLightType()
        
        if type == Light.SPOT_LIGHT:
            return """
            float spotEffect = dot( normalize( gl_LightSource[%(i)d].spotDirection ), normalize( -lightVec[%(i)d]  ) );
            if (spotEffect > gl_LightSource[%(i)d].spotCosCutoff) {
                diffuse  += diffuseShadow * attenFacs[%(i)d] * (gl_FrontLightProduct[%(i)d].diffuse * nDotL);
                specular += shadow * attenFacs[%(i)d] * gl_FrontLightProduct[%(i)d].specular * pow(rDotE, gl_FrontMaterial.shininess);
            }
""" % { 'i': lightIndex }
        elif type == Light.DIRECTIONAL_LIGHT:
            return """
            diffuse  += diffuseShadow * gl_FrontLightProduct[%(i)d].diffuse * nDotL;
            specular += shadow * gl_FrontLightProduct[%(i)d].specular * pow(rDotE, gl_FrontMaterial.shininess);
""" % { 'i': lightIndex }
        elif type == Light.POINT_LIGHT:
            return """
            diffuse  += diffuseShadow * attenFacs[%(i)d] * (gl_FrontLightProduct[%(i)d].diffuse * nDotL);
            specular += shadow * attenFacs[%(i)d] * gl_FrontLightProduct[%(i)d].specular * pow(rDotE, gl_FrontMaterial.shininess);
""" % { 'i': lightIndex }
        else:
            raise ValueError, "Unknown light type!"
    
    def code(self):
        """
        generates light terms (ambient/diffuse/specular).
        """
        
        shadowMapArrayCount = 0
        lightContributions = ""
        
        # iterate over lights and collect contributions
        for lightIndex in range(self.numLights):
            lightInstance = self.lights[lightIndex]
            
            lightColor = """
        // LIGHT%(lightIndex)d
        float nDotL = max( dot( n, normalize(  lightVec[%(lightIndex)d] ) ), 0.0 );
        
        %(AMBIENT_COLOR)s
        
        // if nDotL<=0, we can skip diffuse/specular calculation,
        // since this pixel is not lit anyway.
        if (nDotL > 0.0) {
            vec3 reflected = normalize( reflect( - lightVec[%(lightIndex)d], n ) );
            float rDotE = max( dot( reflected, eye ), 0.0);
""" % { 'lightIndex': lightIndex, 'AMBIENT_COLOR': self.ambientLightCode(lightInstance, lightIndex) }
            
            # calculate shadow amount
            if lightInstance.shadowMapArray!=None:
                lightColor += "            float shadow = 0.0;\n\n"
                lightColor += self.shadowCode(lightIndex, lightInstance.shadowMapArray, shadowMapArrayCount)
                lightColor += "            shadow = min(shadow, 1.0);\n"
                shadowMapArrayCount += 1
            else: # no shadow maps used
                lightColor += "            const float shadow = 1.0;\n\n"
            
            # real light still emits some diffuse light in shadowed region
            lightColor += "            float diffuseShadow = %f + ( 1.0 - %f ) * shadow;\n" % (lightInstance.dimming,
                                                                                               lightInstance.dimming)
            
            # add diffuse and specular light
            lightColor += self.lightCode(lightInstance, lightIndex)
            lightColor += "        }\n" 
            
            lightContributions += lightColor
        
        # return the per pixel light code
        return """
    void %(NAME)s(vec4 base, vec3 n, out vec4 outcol)
    {
        vec4 ambient = vec4(0.0);
        vec4 diffuse = vec4(0.0);
        vec4 specular = vec4(0.0);
        
        vec3 eye = normalize( - eyeVec.xyz );
        float pixelDistance = length( eyeVec );
        
        %(LIGHT_CONTRIBUTIONS)s
        
        outcol = (gl_FrontLightModelProduct.sceneColor + ambient + diffuse) * base + specular;
        outcol.a = base.a;
        
        // TODO: FOG: if use fog !
        float fog = clamp(gl_Fog.scale*(gl_Fog.end + eyeVec.z), 0.0, 1.0);
        outcol = mix(gl_Fog.color, outcol, fog);
    }
""" % { 'NAME': self.name, 'LIGHT_CONTRIBUTIONS': lightContributions }

