# namespace package boilerplate
try:
    __import__('pkg_resources').declare_namespace(__name__)
except ImportError, e:
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)

from sys import path as spath
from os import path as opath
parentPath = opath.split(opath.split(opath.abspath(__file__))[0])[0]
print parentPath
if not parentPath in spath:
    spath.insert(0, parentPath)
