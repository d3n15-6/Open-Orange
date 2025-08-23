#encoding: utf-8
# Agosto 2007 - Martin Salcedo
from OpenOrange import *

ParentFontStyle = SuperClass("FontStyle","Master",__file__)
class FontStyle(ParentFontStyle):
    buffer = RecordBuffer("FontStyle")

    def getPDFFont(self):
        if (self.PDFFont):
            return self.PDFFont
        return self.Family