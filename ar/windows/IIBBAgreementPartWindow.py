#encoding: utf-8
from OpenOrange import *
from GlobalTools import *

ParentIIBBAgreementPartWindow = SuperClass("IIBBAgreementPartWindow","MasterWindow",__file__)
class IIBBAgreementPartWindow(ParentIIBBAgreementPartWindow):
    
    def afterEdit(self, fname):
        afterEdit(self, fname)