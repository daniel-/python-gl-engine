
cPickVertexShader = """
void main(void)
{
  gl_Position = ftransform();
  gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

cPickFragmentShader = """
uniform vec4 color;
uniform sampler2D sampler;
 
void main(void)
{
  if (texture2D(sampler, vec2(gl_TexCoord[0])).a < 0.2)
    discard;
 
  gl_FragColor = color;
}
"""
