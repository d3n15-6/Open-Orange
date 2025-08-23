#encoding: utf-8
from OpenOrange import *

ParentSupplier = SuperClass("Supplier","Addressable",__file__)
class Supplier(ParentSupplier):

    def fieldIsEditable(self, fname, rfname=None, rownr=None):
        res = ParentSupplier.fieldIsEditable(self, fname, rfname, rownr)
        if (fname == "TRT5Retention"):
            cond = currentUserCanDo("CanChangeTRT5Retention",False)
            return cond
        return res

    def checkTaxRegNr(self):
        res = ParentSupplier.checkTaxRegNr(self)
        if (not res): return res
        if (self.TaxRegType == self.TAXREGTYPE_RESP): #Resp.Inscripto
            # Si la fecha no esta cargada asumo que no tiene vencimiento.
            if (not self.fields("TaxRegNrDueDate").isNone()  and self.TaxRegNrDueDate < today()):
                return self.FieldErrorResponse(tr("CUIT", "Expired"),"TaxRegNrDueDate")
        return res
