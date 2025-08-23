#encoding: utf-8
from OpenOrange import *

ParentPurchaseInvoice = SuperClass("PurchaseInvoice","PurchaseTransaction",__file__)
class PurchaseInvoice(ParentPurchaseInvoice):

    def getOldWithholding(self, rettype, type):
        rquery = Query()
        rquery.sql  = "SELECT SUM(PMr.Amount) Amount "
        rquery.sql += "FROM PaymentPayModeRow PMr "
        rquery.sql += "INNER JOIN PayMode PM ON PMr.PayMode = PM.Code "
        rquery.sql += "INNER JOIN Retencion R ON PM.RetCode = R.Code "
        rquery.sql += "WHERE?AND R.RetType = i|%s| " %(rettype)
        rquery.sql += "WHERE?AND R.Type = i|%s| " %(type)
        rquery.sql += "WHERE?AND PMr.RetentionToNr = i|%s| " %(self.SerNr)
        rquery.sql += "GROUP BY PMr.RetentionToNr "

        if (rquery.open() and rquery.count() > 0):
            return rquery[0].Amount
        return 0.0

    def getNetoFactor(self, rettable=None):
        from Province import Province
        from TaxSettings import TaxSettings
        t = TaxSettings.bring()
        taxacc = t.getTaxAccounts() + Province.getTaxAccounts()
        total,vat = 0,0
        taxes = 0
        notaffected = 0
        affectedaccs = []
        if (rettable):
            affectedaccs = [x.Account for x in rettable.AffectedAccs]
        for prow in self.PurchaseInvoiceRows:
            if (prow.Account in taxacc):
                taxes += prow.RowTotal
            if (affectedaccs and prow.Account not in affectedaccs):
                notaffected += prow.RowNet
        taxes += self.VatTotal
        res = ((self.Total-taxes-notaffected)/self.Total)
        #print self.SerNr,"Total",self.Total,"taxes",taxes,"notaffected",notaffected,"factor",res
        return res


ParentPurchaseInvoiceRow = SuperClass("PurchaseInvoiceRow","Record",__file__)
class PurchaseInvoiceRow(ParentPurchaseInvoiceRow):
    pass

ParentPurInvInstallRow = SuperClass("PurInvInstallRow","Record",__file__)
class PurInvInstallRow(ParentPurInvInstallRow):
    pass

ParentPurInvPayModeRow = SuperClass("PurInvPayModeRow","Record",__file__)
class PurInvPayModeRow(ParentPurInvPayModeRow):
    pass