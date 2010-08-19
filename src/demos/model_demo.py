# -*- coding: UTF-8 -*-
'''
Created on 03.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from utils.gl_config import importGL
OpenGL = importGL()
from OpenGL import GL as gl

from gui.model_app import ModelApp
from xml_parser.xml_loader import XMLLoader

from numpy import array, float32

# set to true to profile code
# note: may take some time after closing the application.
PROFILING = False

# load models from xml file
modelNames = ['cube', 'mirror', 'plane']
xmlLoader = XMLLoader(['../data/cube.xml'])
models = map(lambda m: xmlLoader.getModel(m), modelNames)
del xmlLoader

app = ModelApp()
app.setDefaultSceneFBO()

# shadow maps require bounded scene....
# TODO: maybe generating the bounds ?
# TODO: SM: why y=50.0 ? (from nvidia sdk CSM example)
td = 10.0 # bounding value from xml file...
# TODO: SM: why 1.0? (from nvidia sdk CSM example)
radius = 1.0
sceneBoundPoints = array( [
    [-td, 50.0, -td, 1.0],
    [-td, 50.0,  td, 1.0],
    [ td, 50.0,  td, 1.0],
    [ td, 50.0, -td, 1.0] ], float32 )
app.setSceneBounds(sceneBoundPoints, radius)

for m in models:
    app.addModel(m)
    m.create(app=app)

if PROFILING:
    import hotshot
    from hotshot import stats
    prof = hotshot.Profile("appProfile")
    prof.runcall(app.mainloop)
    prof.close()
    
    print "loading statistics, this may take a while...."
    s = stats.load("appProfile")
    s.sort_stats("time").print_stats()
else:
    app.mainloop()

