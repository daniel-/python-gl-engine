# -*- coding: UTF-8 -*-
'''
Created on 03.07.2010

@author: Daniel Beßler <daniel@orgizm.net>
'''

from xml_parser.xml_loader import XMLLoader

from gui.model_app import ModelApp

# load models from xml file
modelNames = ['curves',  'patches', 'nurbs']
xmlLoader = XMLLoader(['../data/evaluator.xml'])
models = map(lambda m: xmlLoader.getModel(m), modelNames)
del xmlLoader

# create the window
app = ModelApp()
app.setDefaultSceneFBO()
# create models (must be done after window creation)
for m in models:
    m.create(app=app)
    app.addModel(m)
# enter the mainloop
app.mainloop()
