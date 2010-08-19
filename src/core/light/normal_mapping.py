# -*- coding: UTF-8 -*-
'''
Created on 30.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from shader.shader_utils import FragShaderFunc, VertShaderFunc

# returns matrix for tangent space to object space transformations
# needs to be calculated per pixel in fragment shader.
getTBN = """
mat3 getTBN(vec3 normal, vec3 position, vec2 texCoord)
{
    vec3 dpx = dFdx(position);
    vec3 dpy = dFdy(position);
    vec2 dtx = dFdx(texCoord);
    vec2 dty = dFdy(texCoord);
    
    vec3 tangent = normalize(dpy * dtx.t - dpx * dty.t);
    vec3 binormal = cross(tangent, normal);
   
    return mat3(tangent, binormal, normal);
}
"""

class BumpMapFrag(FragShaderFunc):
    """
    normal mapping fragment shader.
    this shader function takes the normal, modifies it and returns it.
    this technique only changes the normal, advanced techniques may
    modify texture and vertex coordinates.
    """
    
    NORFAC_NAME = "bumpNorfac"
    
    def __init__(self, enabledLights=[0]):
        FragShaderFunc.__init__(self, name='bump')
        self.numLights = len(enabledLights)
        self.enabledLights = enabledLights
        
        # normal map texture sampler
        self.addConstant(type="float", name=self.NORFAC_NAME, val="1.0")
    
    def code(self):
        return """
    /**
     * this method returns a per fragment normal from a normal map.
     * the normal exists in tangent space.
     **/
    void %(NAME)s(vec4 texel, inout vec3 normal)
    {
        normal = normalize( texel.xyz * 2.0 - 1.0 );
    }
""" % { 'NAME': self.name,
        'NORF': self.NORFAC_NAME }


class BumpMapVert (VertShaderFunc):
    def __init__(self, enabledLights=[0]):
        VertShaderFunc.__init__(self, 'bump')
        self.numLights = len(enabledLights)
        self.enabledLights = enabledLights
        
        self.addVarying(type="vec3", name="lightVec[%d]" % self.numLights)
        self.addAttribute(type="vec4", name="vertexTangent")
    
    def code(self):
        code = """
    /**
     * this method transforms the varyings eyeVec and lightVec to tangent space.
     * the normal map must contain tangents in tangent space, this value is used
     * directly in the fragment shader. the varyings are transformed because
     * the vectors must be in the same space for the light calculation to work.
     * the normal in the fragment sahder can also be transformed to eyespace instead of this,
     * but this would need more calculations, then doing it in the vertex shader.
     * @param n: the normal attribute at the processed vertex in eye space.
     **/
    void %(NAME)s(vec3 n)
    {
        // get the tangent in eye space (multiplication by gl_NormalMatrix transforms to eye space)
        // the tangent should point in positive u direction on the uv plane in the tangent space.
        vec3 t = normalize( gl_NormalMatrix * vertexTangent.xyz );
        // calculate the binormal, cross makes sure tbn matrix is orthogonal
        // multiplicated by handeness.
        vec3 b = cross(n, t) * vertexTangent.w;
        // transpose tbn matrix will do the transformation to tangent space
        //mat3 tbn = transpose( mat3(t, b, n) );
        vec3 buf;
        
        // do the transformation of the eye vector (used for specuar light)
        buf.x = dot( eyeVec, t );
        buf.y = dot( eyeVec, b );
        buf.z = dot( eyeVec, n );
        eyeVec = normalize( buf );
        //eyeVec = normalize( tbn * eyeVec );
        
        // do the transformation of the light vectors
""" %  { 'NAME': self.name }
        
        for n in range(self.numLights):
            code += """
        buf.x = dot( lightVec[%(INDEX)d], t );
        buf.y = dot( lightVec[%(INDEX)d], b );
        buf.z = dot( lightVec[%(INDEX)d], n ) ;
        lightVec[%(INDEX)d] = normalize( buf  );
        //lightVec[%(INDEX)d].z = abs( lightVec[%(INDEX)d].z  );
        //lightVec[%(INDEX)d] = normalize( tbn * lightVec[%(INDEX)d] );
""" % { 'INDEX': n }
        
        return code + """
    }
"""

