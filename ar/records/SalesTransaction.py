#encoding: utf-8
from OpenOrange import *
from Customer import Customer

ParentSalesTransaction = SuperClass("SalesTransaction", "FinancialTrans", __file__)
class SalesTransaction(ParentSalesTransaction):

    def generateTaxes(self):
        ParentSalesTransaction.generateTaxes(self)
        from TaxSettings import TaxSettings
        from Retencion import Retencion
        ts = TaxSettings.bring()
        self.Taxes.clear()
        taxRowName = "%sTaxRow" % self.__class__.__name__
        #lo only for argentina
        if (ts.PercepAgent1):
            am = 0
            for item in self.Items:
               from Item import Item
               it = Item.bring(item.ArtCode)
               am += item.Qty * it.Alcohol
            itr = NewRecord(taxRowName)
            itr.TaxCode = "ICE"
            itr.Amount  = am
            self.Taxes.append(itr) 
        if (ts.PercepAgent2):     # Percepción de Ingresos Brutos
            res = Retencion.doIIBBPerception(self)
        if (ts.PercepAgent3):     # Percepción de IVA
            res = Retencion.doVATPerception(self)

    def getToPerceptTotal(self):
        from Item import Item
        tptotal = 0.0
        for iline in self.Items:
            itm = iline.getArtCodeRecord()
            if (itm and not itm.DontPerceptIIBB):
                tptotal += iline.RowNet
        return tptotal
