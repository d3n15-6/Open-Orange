#encoding: utf-8
#coding=iso-8859-15
from OpenOrange import *

ParentTRT5Settings = SuperClass("TRT5Settings","Setting",__file__)
class TRT5Settings(ParentTRT5Settings):

    def check(self):
        res = ParentTRT5Settings.check(self)
        if (not res): return res
        if (not self.Currency):
            return self.FieldErrorResponse("NONBLANKERR","Currency")
        return res
    
    @classmethod
    def getSupplierLimit(objclass, supcode):
        tset = TRT5Settings.bring()
        from Supplier import Supplier
        sup = Supplier.bring(supcode)
        rows = []
        if (sup):
            if (sup.PurchaseType == 0):
                rows = [x.Amount for x in tset.PurType0]
            else:
                rows = [x.Amount for x in tset.PurType1]
        if (rows):
            return (tset.Currency, rows[-1])
        message("Falta configurar Tabla Opciones de Monotributistas")
        return (None,None)

    @classmethod
    def exceedSupplierLimit(objclass, supcode, cur, sum):
        lcur,lvalue = objclass.getSupplierLimit(supcode)
        if (cur == lcur):
            return sum > lvalue
        else:
            from Currency import Currency
            rsum = Currency.ContextFreeConvertTo(sum,cur,lcur)
            #print rsum
            return rsum > lvalue
        return False

ParentTRT5SettingsPurType0Row = SuperClass("TRT5SettingsPurType0Row","Record",__file__)
class TRT5SettingsPurType0Row(ParentTRT5SettingsPurType0Row):
    
    def pasteCategory(self, record):
        self.Category = self.Category.upper()

ParentTRT5SettingsPurType1Row = SuperClass("TRT5SettingsPurType1Row","Record",__file__)
class TRT5SettingsPurType1Row(ParentTRT5SettingsPurType1Row):

    def pasteCategory(self, record):
        self.Category = self.Category.upper()
