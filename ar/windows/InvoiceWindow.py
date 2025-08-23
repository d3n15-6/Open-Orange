# encoding: utf-8
from OpenOrange import *
from GlobalTools import *

ParentInvoiceWindow = SuperClass("InvoiceWindow","SalesTransactionWindow",__file__)
class InvoiceWindow(ParentInvoiceWindow):

    ################FISCAL PRINTER################
    def sendPrintFiscalInvoice(self):
        from FiscalPrinter import FiscalPrinter
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        fp = FiscalPrinter.bring(ls.Computer)
        record = self.getRecord()
        if record.isModified():
            message (tr("You need to save the current record first!"))
            return False
        res = record.sendPrintFiscalInvoice()
        if (not res): 
            return res
        else:
            res = record.save()
            if (not res):
                log(res)
                message("No se pudo guardar la factura, intente guardar manualmente")
                return
            else:
                commit()
        record.refresh()
        return res

    def sendCancelFiscalInvoice(self):
        from FiscalPrinter import FiscalPrinter
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        fp = FiscalPrinter.bring(ls.Computer)
        invoice = self.getRecord()
        if (not invoice.checkFiscalPrinter()):
            return
        fp.cancelFiscalInvoice()
        fp.showMessages()