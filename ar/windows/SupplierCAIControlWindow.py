#encoding: utf-8
# Diciembre 2008 - Claudia Acosta
from OpenOrange import *
from GlobalTools import *

ParentSupplierCAIControlWindow = SuperClass("SupplierCAIControlWindow","NumerableWindow",__file__)
class SupplierCAIControlWindow(ParentSupplierCAIControlWindow):
    def afterEdit(self, fieldname):
        afterEdit(self, fieldname)

