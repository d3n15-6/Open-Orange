# encoding: utf-8
from OpenOrange import *

ParentInvoice = SuperClass("Invoice","SalesTransaction",__file__)
class Invoice(ParentInvoice):

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentInvoice.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if not res:
            return res
        from SerNrControl import SerNrControl
        snc = SerNrControl.getControlForNumerable(self)
        if (fieldname == "OfficialSerNr"):
            if not (snc and snc.IsManualTransaction) and not currentUserCanDo("CanModifyInvoiceOfficialSerNr", False):
                return False
        return True

    def checkInvoiceDoc(self):
        from Customer import Customer
        import Validator
        cust = Customer.bring(self.CustCode)
        res = False
        msg = "Compruebe Inscripcion en Factura y Tipo de Doc en Cliente "
        if (cust):
            #Fact A: 
            if (self.DocType == 0):
                #tipo de doc: cuit
                if (cust.IDType == 1 and self.TaxRegType == 0): #resp insc
                    res = True
                    if (not Validator.VATRegNrOK(self.TaxRegNr,cust.Country)):
                        msg = "CUIT Invalido"
                        res = False
                else:
                    res = True
            elif (self.DocType == 1 ): #fact b
                if (self.TaxRegType != 0 and cust.IDType >0): #no se permite tipo doc ninguno
                    res = True
                    if (cust.IDType == 1 and not Validator.VATRegNrOK(self.TaxRegNr,cust.Country)): #compruebo que el cuit sea valido
                        msg = "CUIT Invalido"
                        res = False
                else:
                    res = True
            else:
                res = True
        if (not res):
            return self.FieldErrorResponse(msg,"DocType")
        return True

    def check(self):
        res = ParentInvoice.check(self)
        if (not res): return res
        res = self.checkInvoiceDoc()
        if (not res): return res
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        from FiscalPrinter import FiscalPrinter
        if not FiscalPrinter.bring(ls.Computer):
            result = self.checkOfficialSerNr()
        else:
            #si es una impresora fiscal, controlo que el total no sea 0
            res = self.controlInvoiceTotal()
            if (not res):
                return res
        return res

    def checkFiscalPrinter(self):
        from FiscalPrinter import FiscalPrinter
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        fp = FiscalPrinter.bring(ls.Computer)
        if (ls.Computer != self.Computer):
            message("Esta factura fue generada por la impresora fiscal %s" %(self.Computer))
            return None
        if not fp:
            message("No hay una impresora fiscal definida para este punto de venta")
            return None
        return True

    #ES PARA QUE NO TENGAN DIFERENCIAS CON EL ARQUEO DE CAJA, 
    #FACTURA CON UNA FECHA SE IMPRIME EN OTRA Y SE "ROMPE" LA CORRELATIVIDAD DEL NRO OFICIAL
    def checkInvoiceDate(self):
        from FiscalPrinter import FiscalPrinter
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        fp = FiscalPrinter.bring(ls.Computer)
        result = True
        if (fp.PrintOnlyTodayTrans):
            if (self.InvoiceDate != today()):
                result = False
        if (not result):
            message("La fecha de la factura no es la de hoy, no se puede imprimir.")
        return result

    def controlInvoiceTotal(self):
        if (roundedZero(self.Total)):
            return self.FieldErrorResponse("NONZEROERR", "Total")
        return True

    def sendPrintFiscalInvoice(self):
        from FiscalPrinter import FiscalPrinter
        from LocalSettings import LocalSettings
        #no se puede imprimir si es transacción manual.
        res = self.checkSerNrControl()
        if (not res):
            message("No se puede imprimir por impresora fiscal una transacción manual. Revise Control de Números Seriales.")
            return False
        ls = LocalSettings.bring()
        fp = FiscalPrinter.bring(ls.Computer)
        if (self.Printed):
            message (tr("Document was already printed"))
            return False
        #Chequeos para evitar problemas
        #VUELVO A CONTROLAR LA CONDICION DEL CLIENTE PORQUE SI CAMBIAN EL CLIENTE LUEGO DE APROBAR LA FACTURA TENGO ERRORES
        res = self.checkInvoiceDoc()
        if (not res):
            return res
        #FACTURA CON TOTAL 0 NO SE PUEDEN IMPRIMIR POR IMP. FISCAL
        res = self.controlInvoiceTotal()
        if (not res):
            return res
        res = self.checkFiscalPrinter()
        if (not res): return res
        res = self.checkInvoiceDate()
        if (not res): return res
        if (self.Total > 1000 and not self.TaxRegNr):
            message ("Debe ingresar un Nro de documento valido")
            return False
        #SHOULD BE: if self.canBePrinted():
        if fp.PrintOnlyApproved:
            if (not self.confirmed()):
                message(tr("ONLYALLOWED4APPROVEDTRANS"))
                return False
        invprintform = self.printingFormat()
        nr = fp.printInvoice(invprintform)
        fp.showMessages()
        if not nr: return False
        self.OfficialSerNr = nr
        self.Printed = True
        return True

    def beforeInsert(self):
        res = ParentInvoice.beforeInsert(self)
        if not res: return res
        #SI NO ES TRANSACCION MANUAL Y ESTA SETEADO QUE IMPRIMA AL APROBAR
        if (self.checkSerNrControl()):
            from FiscalPrinter import FiscalPrinter
            from LocalSettings import LocalSettings
            ls = LocalSettings.bring()
            fp = FiscalPrinter.bring(ls.Computer)
            if (fp):
                if (fp.PrintOnConfirming and self.confirming() and not self.Printed):
                    res = self.checkFiscalPrinter()
                    if (not res): return res
                    res = self.sendPrintFiscalInvoice()
                    if (not res): return res
        return res

    def beforeUpdate(self):
        res = ParentInvoice.beforeUpdate(self)
        if not res: return res
        #SI NO ES TRANSACCION MANUAL Y ESTA SETEADO QUE IMPRIMA AL APROBAR
        if (self.checkSerNrControl()):
            from FiscalPrinter import FiscalPrinter
            from LocalSettings import LocalSettings
            ls = LocalSettings.bring()
            fp = FiscalPrinter.bring(ls.Computer)
            if (fp):
                if (fp.PrintOnConfirming and self.confirming() and not self.Printed):
                    res = self.checkFiscalPrinter()
                    if (not res): return res
                    res = self.sendPrintFiscalInvoice()
                    if (not res): return res
        return res

    def checkSerNrControl(self):
        from SerNrControl import SerNrControl
        if (SerNrControl.isManualTransaction(self)):
            return False
        return True

    def makeOfficialSerNr(self, Revert=False):
        if Revert:
            pass
            #self.OfficialSerNr = None   dont delete the official nr after unoking
        else:
            if not self.OfficialSerNr:
                if (self.DocType == 6): return True
                from OurSettings import OurSettings
                from SerNrControl import SerNrControl
                snc = SerNrControl.getControlForNumerable(self)
                if (snc):
                    if (not snc.IsManualTransaction):
                        from FiscalPrinter import FiscalPrinter
                        from LocalSettings import LocalSettings
                        ls = LocalSettings.bring()
                        if not FiscalPrinter.bring(ls.Computer):
                            tmp = str(self.SerNr)
                            #Esto molesta en el ordenamiento de facturas: sixcom por ejemplo no lo quiere
                            #no cambiar antes de discutir con LO
                            #if self.InvoiceType == Invoice.CREDITNOTE: argpref = "NC"
                            #elif self.InvoiceType == Invoice.DEBITNOTE: argpref = "ND"
                            argpref = Invoice.DocTypes[self.DocType]
                            #self.OfficialSerNr = argpref + "-00" + tmp[1:3] + "-00" + tmp[3:9]
                            if (len(str(self.SerNr)) >= 9):
                                self.OfficialSerNr = "%s-%s-%s" %(Invoice.DocTypes[self.DocType],tmp[1:3].rjust(4,"0"),tmp[3:10].rjust(8,"0"))
                                res = self.checkOfficialSerNr()
                                if not res:
                                    return res
                            else:
                                self.OfficialSerNr = "%s-%s-%s" %(Invoice.DocTypes[self.DocType],"0000",str(self.SerNr).rjust(8,"0"))
                                res = self.checkOfficialSerNr()
                                if not res:
                                    return res
                    else:
                        self.setFocusOnField("OfficialSerNr")
                        return ErrorResponse("%s \n %s: %s" %(tr("NONBLANKERR"),tr("Field"),tr("Official Nr.")))
        return True

ParentInvoiceItemRow = SuperClass("InvoiceItemRow","Record",__file__)
class InvoiceItemRow(ParentInvoiceItemRow):
    pass

ParentInvoicePayModeRow = SuperClass("InvoicePayModeRow","Record",__file__)
class InvoicePayModeRow(ParentInvoicePayModeRow):
    pass

ParentInvoiceInstallRow = SuperClass("InvoiceInstallRow","Record",__file__)
class InvoiceInstallRow(ParentInvoiceInstallRow):
    pass

ParentInvoiceTaxRow = SuperClass("InvoiceTaxRow","Record",__file__)
class InvoiceTaxRow(ParentInvoiceTaxRow):
    pass
