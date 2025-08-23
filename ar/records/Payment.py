#encoding: utf-8
from OpenOrange import *

ParentPayment = SuperClass("Payment","PurchaseTransaction",__file__)
class Payment(ParentPayment):

    def calculateRetentions(self, checking=False):
        if not self.Status == self.DRAFT:
            return ErrorResponse("Status Must Be Draft")
        if (not checking):
            if (self.isModified() or self.isNew()):
               return ErrorResponse("REGISTERNOTSAVED")
        if (self.confirmed() or self.Received):
           beep
           return ErrorResponse("Record Approved. Can't Be Modified.")
        # Find the biggest amount row because we deduct from that one
        if (not checking):
            from PayMode import PayMode
            for pay in self.PayModes:
                pm = PayMode.bring(pay.PayMode)
                if pm:
                    if pm.PayType != 0:
                        return self.FieldErrorResponse("Incorrect Payment Type in Payment Form. It must be Cash Type","PayMode")
        # Get withholdings regimen for this supplier
        procs = ["doGAN","doIBR","doIVA","doREL", "doSUSS", "doSEG", "doGAN","doVATMonth"]
        from Retencion import Retencion
        sup = self.getSupCodeRecord()
        if (sup):
            retsdue = sup.Withholdings.split(",")
            for retcode in retsdue:
                ret = Retencion.bring(retcode)
                if ret:
                    retentionMethod = getattr(ret,procs[ret.RetType])
                    if callable(retentionMethod):
                        bigRow = self.getPaymentBigRow()
                        if (bigRow.Amount > 0):
                            Params = {}
                            Params["FTrans"] = self
                            Params["BigRow"] = bigRow
                            Params["Amount"] = bigRow.Amount
                            retres = retentionMethod(**Params)
                            for retline in retres:
                                if (retline.Amount > bigRow.Amount):
                                    retline.Amount = bigRow.Amount
                                #Check if exists any type of retentions and then return True
                                if (checking):
                                    return True
                                bigRow.Amount -= retline.Amount
                                newWithRow = PaymentPayModeRow()
                                newWithRow.Amount  = self.roundValue(retline.Amount)
                                if (hasattr(retline,"InvoiceNr")):
                                    newWithRow.RetentionToNr = retline.InvoiceNr
                                newWithRow.PayMode = ret.getPayMode()
                                newWithRow.pastePayMode()
                                self.PayModes.append(newWithRow)
        if (checking):
            return False
        return True

    def getPaymentBigRow(self):
        biggest = 0
        bigrow = PaymentPayModeRow()
        for payrow in self.PayModes:
            pmode = payrow.getPayModeRecord()
            if (pmode.PayType not in (pmode.WITHHOLDING,pmode.RECEIVEDWITHHOLDING)):
                if (biggest < payrow.Amount):
                    bigrow = payrow
                    biggest = payrow.Amount
        return bigrow

    def afterInsert(self):
        res = ParentPayment.afterInsert(self)
        if (not res): return res
        self.updateTRT5Condition()
        return res

    def afterUpdate(self):
        res = ParentPayment.afterUpdate(self)
        if (not res): return res
        self.updateTRT5Condition()
        return res

    def updateTRT5Condition(self):
        if (self.confirming()):
            sup = self.getSupCodeRecord()
            if (sup.TaxRegType == 5):
                from Retencion import Retencion
                cur,bimp = Retencion.getLastInvSum(self.SupCode,self.TransDate)
                if (bimp != 0):
                    from TRT5Settings import TRT5Settings
                    exceed = TRT5Settings.exceedSupplierLimit(self.SupCode,cur,bimp)
                    if (exceed):
                        sup.TRT5Retention = True
                        res = sup.store()

ParentPaymentInvoiceRow = SuperClass('PaymentInvoiceRow', "Record", __file__)
class PaymentInvoiceRow(ParentPaymentInvoiceRow):
    pass

ParentPaymentPayModeRow = SuperClass('PaymentPayModeRow', "Record", __file__)
class PaymentPayModeRow(ParentPaymentPayModeRow):
    pass