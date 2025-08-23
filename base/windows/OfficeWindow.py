#encoding: utf-8
from OpenOrange import *

ParentOfficeWindow = SuperClass("OfficeWindow","AddressableWindow",__file__)
class OfficeWindow(ParentOfficeWindow):
    
    def getBasePrice(self):
        self.getRecord().getBasePrice()
        

