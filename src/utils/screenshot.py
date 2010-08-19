# -*- coding: UTF-8 -*-
'''
Created on 13.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

def glLibScreenshot(path,overwrite=False):
    size = glGetFloatv(GL_VIEWPORT)
    size = [int(round(size[2])),int(round(size[3]))]
    glPixelStorei(GL_PACK_ALIGNMENT,4)
    glPixelStorei(GL_PACK_ROW_LENGTH,0)
    glPixelStorei(GL_PACK_SKIP_ROWS,0)
    glPixelStorei(GL_PACK_SKIP_PIXELS,0)
    data = glReadPixels(0,0,size[0],size[1],GL_RGB,GL_UNSIGNED_BYTE)
    surface = pygame.image.fromstring(data,size,'RGB',1)
    if overwrite:
        pygame.image.save(surface,path)
    else:
        path = path.split(".")
        counter = 1
        while True:
            try:pygame.image.load(path[0]+"."+path[1])
            except:break
            counter += 1
        if counter == 1:
            pygame.image.save(surface,path[0]+"."+path[1])
        else:
            pygame.image.save(surface,path[0]+"_"+str(counter)+"."+path[1])
