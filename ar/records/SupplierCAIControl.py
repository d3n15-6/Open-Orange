#encoding: utf-8
from OpenOrange import *
from GlobalTools import *
import string

ParentSupplierCAIControl = SuperClass("SupplierCAIControl","Numerable",__file__)
class SupplierCAIControl(ParentSupplierCAIControl):

    def pasteSupCode(self):
        self.SupName = getMasterRecordField("Supplier", "Name", self.SupCode)

    def expandArInvoiceNumber(self, s):
         # if you start with capitals suppose the user wants to enter himself
         if s and s[0] in ("a","A","b","B", "c","C", "d", "D", "m", "M"):     # d = documento aduana, m = factura m
           pstring = s[1:].strip()
           parts = string.split(pstring,"-")
           suc = parts[0].rjust(4,"0")
           return "%s %s-%s" % (string.upper(s[0]),suc,parts[1].rjust(8,"0") )
         else:
           return s

    def pasteFrNumber(self):
        self.FrNumber = self.expandArInvoiceNumber(self.FrNumber)

    def pasteToNumber(self):
        self.ToNumber = self.expandArInvoiceNumber(self.ToNumber)

    def check(self):
        if (not self.CAI):
            return self.FieldErrorResponse("NONBLANKERR", "CAI")
        res= ParentSupplierCAIControl.check(self)
        if (not res): return res
        return True
