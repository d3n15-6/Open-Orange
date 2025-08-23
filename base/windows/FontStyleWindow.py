#encoding: utf-8
# Agosto 2007 - Martin Salcedo
from OpenOrange import *

ParentFontStyleWindow = SuperClass("FontStyleWindow","MasterWindow",__file__)
class FontStyleWindow(ParentFontStyleWindow):

    def getPasteWindowName(self,fieldname):
        record = self.getRecord()
        if(fieldname == "Color"):
            from ItemColorPaste import ItemColorPaste
            report = ItemColorPaste()
            report.record = record
            specs = report.getRecord()
            report.open(False)
            return ""
