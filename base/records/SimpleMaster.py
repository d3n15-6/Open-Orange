#encoding: utf-8
from OpenOrange import *

ParentSimpleMaster = SuperClass("SimpleMaster","Master",__file__)
class SimpleMaster(ParentSimpleMaster):

    def checkCode(self):
        return True
