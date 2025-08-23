#encoding: utf-8
from OpenOrange import *

ParentSupplierWindow = SuperClass("SupplierWindow", "AddressableWindow", __file__)
class SupplierWindow(ParentSupplierWindow):

    def buttonClicked(self, buttonname):
        ParentSupplierWindow.buttonClicked(self, buttonname)
        sup = self.getRecord()
        if buttonname == "getRetencGroup":
            from Retencion import Retencion
            from TaxSettings import TaxSettings
            myRec = self.getRecord ()
            percent = myRec.updateRetencGroup()
            if percent != None:
                ts = TaxSettings.bring()
                r = Retencion.bring (ts.IIBBTaxRetTable)
                if not r: return False
                r.updateRetencGroup (myRec.TaxCat1,percent)
                return r.store ()
