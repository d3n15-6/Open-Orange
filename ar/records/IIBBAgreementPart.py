#encoding: utf-8
from OpenOrange import *
from GlobalTools import *

ParentIIBBAgreementPart = SuperClass("IIBBAgreementPart","Master",__file__)
class IIBBAgreementPart(ParentIIBBAgreementPart):
    
    def pasteCode(self):
        self.Name = getMasterRecordField("Customer","Name",self.Code)

    @classmethod
    def bring(self, code, province):
        apart = IIBBAgreementPart()
        apart.Code = code
        apart.Province = province
        if (apart.load()):
            return apart
        return None

    def uniqueKey(self):
        return ('Code','Province')
    