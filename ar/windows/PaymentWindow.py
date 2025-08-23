#encoding: utf-8
from OpenOrange import *

ParentPaymentWindow = SuperClass("PaymentWindow","PurchaseTransactionWindow",__file__)
class PaymentWindow(ParentPaymentWindow):

    def buttonClicked(self, buttonname):
        ParentPaymentWindow.buttonClicked(self, buttonname)
        if buttonname == "PasteRetentions":
            payment = self.getRecord()
            res = payment.calculateRetentions()
            if not res:
                message(res)
            else:
                from PurchaseSettings import PurchaseSettings
                psett = PurchaseSettings.bring()
                if psett.PaymentRetentionsResume:
                    self.showRetentionsResume()
                payment.Status = payment.WITHCALCULATED

    def showRetentionsResume(self):
        record = self.getRecord()
        from PaymentRetentionsResume import PaymentRetentionsResume
        report = PaymentRetentionsResume()
        report.PaymentNr = record.SerNr
        report.open(False)