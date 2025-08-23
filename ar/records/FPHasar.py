#encoding: utf-8
from time import sleep
from OpenOrange import *
import string
from FPDriver import FPDriver, Command
from Comunication import *
#from LowLevelTools import *

MAXSTR = 40
INSCRIPTION = ["I","C","A","E","N","M","T"]
#DOC =  [" ","C","2","4","3","1","0"]
DOC =  ["C","2","4","3","1","0"]
DOCEQ = {0: " ",   # "Ninguno" en open
         1: "C", # cuit
         2: 2,   # dni
         3: 4,   # cedula
         4: "L", # cuil
         5: 1,   # libreta civica
         6: 0,   # libreta enrolamiento
         7: 3    # pasaporte
         }
FISCALSTATUS = ["Error Memoria Fiscal",
                "Error RAM",
                "Zero",
                "Comando Desconocido",
                "Datos Invalidos",
                "Comando No valido para Estado Fiscal",
                "Desbordamiento de Datos",
                "Memoria Fiscal llena",
                "Memoria Fiscal casi llena",
                "Impresora Fiscal Inicializada",
                "Impresora Fiscal Inicializada",
                "Fecha Ingresada Invalida",
                "Documento Fiscal Abierto",
                "Documento Abierto",
                "Factura Abierta",
                "Checkbit"
                ]
PRINTERSTATUS = [  "No se Usa",
                   "No se Usa",
                   "Falla de Impresora",
                   "Impresora fuera de linea",
                   "Falta de Papel del Diario",
                   "Falta de Papel de Tickets",
                   "Buffer impresora lleno",                   
                   "Buffer impresora vacio",                   
                   "Tapa de Impresora Abierta",                   
                   "No se Usa",
                   "No se Usa",
                   "No se Usa",
                   "No se Usa",
                   "No se Usa",
                   "Cajon de Dinero Cerrado o Ausente",
                   "Checkbit"]
AUXSTATUS = [  "Memoria Fiscal no formateada",
                   "Memoria Fiscal no inicializada",
                   "No hay ningun comprobante abierto",
                   "Un comprobante fiscal se encuentra abierta: vta habilitada",
                   "Comprobante fiscal abierto: se acaba de imprimir un texto fiscal",
                   "Un comprobante no fiscal se encuentra abierto",
                   "Compr.Fiscal Abierto: se realizo al menos un pago",                   
                   "Compr.Fiscal Abierto: se saldo el monto",                   
                   "Compr.Fiscal Abierto: se realizo una percepcion",                   
                   "El controlador ha sido dado de baja",
                   "Compr.Fiscal Abierto: se realizo un descuento/recargo general",                   
                   "Compr.Fiscal Abierto: se realizo una bonificacion/recargo devol.envase",                   
                   "Una nota de credito se encuentra abierta: credito habilitado",
                   "Una nota de credito se encuentra abierta: se realizo una bonificacion/recargo devol.envase",
                   "Una nota de credito se encuentra abierta: se realizo un descuento/recargo general",
                   "Una nota de credito se encuentra abierta: se realizo una percepcion",
                   "Una nota de credito se encuentra abierta: se acaba de imprimir un texto fiscal"
                  ]
HEADERS = { # 1-10 headers
            1:"",
            2:"",
            3:"Header 3",
            4:"Header 4",
            5:"Header 5",
            6:"",
            7:"",
            8:"",
            9:"",
            10:"",
            # 11 - 20 footers
            11:"Footer 1",
            12:"Footer 2",
            13:"Footer 3",
            14:"Footer 4",
            15:"",
            16:"",
            17:"",
            18:"",
            19:"",
            20:"" }



DocTypes = {"01":"Ticket Fact A","02":"Ticket Fact B","03":"Ticket Fact C","04":"Ticket ND A","05":"Ticket ND B","06":"Ticket ND C","0A":"Ticket","20":"Doc No Fiscal","40":"Ticket NC A","41":"Ticket NC B","42":"Ticket NC C","49":"Voucher Tarj Cred"}
MaxReturnRechargeDesc = {0:50,6:50,1:50,2:40,8:40}

class FPHasar(FPDriver):
    # Hasar Command Table
    commandTable = {   chr(128):"openDNFH",
                       chr(66):"itemLine",
                       chr(42):"statusRequest",
                       chr(98):"setCustomerData",
                       chr(147):"setEmFP",
                       chr(148):"getEmFP",
                       chr(64):"OpenFiscalReceipt",
                       chr(68):"totalTender",
                       chr(69):"closeFiscalReceipt",
                       chr(129):"closeDNFH",
                       chr(146):"getFantasyName",
                       chr(109):"ReturnRecharge"
                   }
    Caracteres = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;-_:"
    #nro max de veces que puede llamarse el comando FiscalText
    maxFiscalTextCalls = 4

    def ffs(self,text):
        """Translates an spanish string into a standard english character string"""
        res = ""
        for x in text:
          if x not in self.Caracteres:
              res+= chr(self.TRANSTABLE.get(x,ord(" ")))
          else:
            res += x
        return res
        
    def printInvoice(self, inv):
        from Invoice import Invoice
        offNr=None
        if inv.InvoiceType == Invoice.CREDITNOTE: 
            offNr = self.__printCreditNote(inv)
        else: offNr = self.__printInvoice(inv)

        # cosas comunes a todos los comprobantes
        if self.DFPC.PaperCutterf and self.PrinterModel != 8:
            self.forwardPaper(10)
            self.cutPaper()
        # Copias adicionales
        for j in range(0,self.DFPC.F1):
            self.Reprint()
            if (self.DFPC.PaperCutterf):
                self.openDrawer()
            self.closeFiscalReceipt(1)
        #LO SACO PORQUE GENERA PROBLEMAS Y ESE METODO ES SOLO PARA HASAR 330. - CA
        #
        #if self.caiflag:
        #    self.getLastCAI(inv.SerNr)
        #
        return offNr

    def __printInvoice(self,inv):
        from Invoice import Invoice
        from Customer import Customer
        from PayTerm import PayTerm
        cust = Customer.bring(inv.CustCode)
        if not cust: return
        #Pasaporte no soporta letras en hasar 320, se manda como encabezado
        TaxRegNr = inv.TaxRegNr
        passPort = None
        pt = PayTerm.bring(inv.PayTerm)
        if (cust.IDType == 7 and self.PrinterModel == 0):
            TaxRegNr = "0"
            passPort = inv.TaxRegNr
        if self.hasHeader:
           self.printHeaderTrailer(inv,"Invoice",passPort)
        self.setCustomerData(inv.TaxRegType,TaxRegNr,inv.Address,inv.City,inv.Province,inv.CustName,cust.IDType)
        generalDiscount=0.0
        OfficialNr = self.OpenFiscalReceipt(inv.DocType, inv.InvoiceType)
        discItemSum = sum((it.RowTotal for it in inv.Items if it.RowTotal < 0))
        totalPriceflag = False
        priceType = "Price"
        rowType = "RowNet"
        #LOS DESCUENTOS GENERALES DEBEN IR AL FINAL
        discountByVATCode = {}
        if (self.DFPC.printVATPrice):
            totalPriceflag = True
            priceType = "VATPrice"
            rowType = "RowTotal"
        for item in (it for it in inv.Items if it.ArtCode and it.RowTotal >= 0):
            dispatchNr = ""
            exec("price = item.%s "%priceType)
            #SI OCULTAN LOS DESCUENTOS
            if (self.DFPC.HideItemDiscounts):
                if (item.Discount != 0 and item.Qty != 0):
                    exec("price = item.%s / item.Qty "%rowType)
            qty = item.Qty
            if item.UnitFactor:
                qty *= item.UnitFactor
                if self.DFPC.HideItemDiscounts:
                    price /= item.UnitFactor  
            self.itemLine(item.ArtCode, item.Name, price, qty, 0,
                item.Discount, item.LuxGoodTax, item.SerialNr, dispatchNr,
                item.VATCode, totalPriceflag, inv.InvoiceType) #ver Rate
            if (item.Discount and item.Qty > 0):
                exec("rowT = item.%s "%rowType)
                factor = 1
                if item.UnitFactor:
                    factor = item.UnitFactor
                delta = abs(rowT- price * item.Qty * factor)
                if (not self.DFPC.ResumeItemDiscounts):
                    #SE DEBE MANDAR EL DESCUENTO SOBRE EL ULTIMO ITEM
                    self.ItemDiscount(rowT, item.Discount, delta, inv.DocType,totalPriceflag)
                else:
                    try:
                        discountByVATCode[item.VATCode] += delta
                    except:
                        discountByVATCode[item.VATCode] = delta

        for item in (it for it in inv.Items if it.ArtCode and it.RowTotal < 0):
            exec("rowT = item.%s "%rowType)
            if (self.DFPC.ResumeItemDiscounts):
                try:
                    discountByVATCode[item.VATCode] += rowT
                except:
                    discountByVATCode[item.VATCode] = rowT
            else:
                self.ReturnRecharge(rowT, item.Name, item.VATCode, item.LuxGoodTax, totalPriceflag)

        #RESUMIDOS PERO AGRUPADOS POR CODIGO DE IVA (LEGAL)
        if (self.DFPC.ResumeItemDiscounts and len(discountByVATCode.keys())):
            for vat in discountByVATCode.keys():
                self.ReturnRecharge(discountByVATCode[vat] , "", vat, item.LuxGoodTax, totalPriceflag)

        #TODO: Probar funcionamiento con percepciones de iva.
        # siempre deben enviarse primero las percepciones de iva.
        rate=21.00
        for itr in (it for it in inv.Taxes if it.TaxCode == "PIVA"):
            self.Perceptions (self.PERCEPTION_GLOBAL_IVA, rate, "Percepcion de iva", itr.Amount)
        for itr in (it for it in inv.Taxes if it.TaxCode.startswith("IBR")):
            self.Perceptions (self.PERCEPTION_OTHER, None, "Perc. IBr.%s" % itr.TaxCode[3:], itr.Amount)

        #IMPRESION DE FORMAS DE PAGO ------------------------------------------

        invTypeFactor =1
        if (inv.InvoiceType == 1): #nota de credito
            invTypeFactor = -1

        from PayMode import PayMode
        paymentQty = inv.Payments.count()
        #hardcodeado porque puede ser que la forma de pago CC sea otra cosa
        ccName = "Cuenta Corriente" 
        paid = 0
        for pmode in inv.Payments:
            paid += pmode.Paid
        restvalue = inv.Total - paid
        restvalue *= invTypeFactor
        lines = 0
        if (restvalue > 0):
            lines += 1
        lines += paymentQty
        #esta impresora solo permite enviar 4 lineas de pagos
        if (lines <= 4):
            #puedo imprimir la descr de cada forma de pago
            for pmode in inv.Payments:
                self.totalTender(pmode.Comment,"T",pmode.Paid)
            if (restvalue):
                self.totalTender(ccName,"T",restvalue)
        else:
            payDict = {}
            #tengo que agrupar por tipo de la forma de pago
            categorias = {}
            categorias[0] = "Contado" #efect
            categorias[1] = "Contado" #tarj de credito
            categorias[2] = "Contado" #cheque
            categorias[10] = "Contado" #cheque europeo 
            categorias[9] = "Retencion Sufrida"
            for pay in inv.Payments:
                pmode = PayMode.bring(pay.PayMode)
                if (pmode):
                    if (payDict.has_key(categorias[pmode.PayType])):
                        payDict[categorias[pmode.PayType]] += pay.Paid
                    else:
                        payDict[categorias[pmode.PayType]] = pay.Paid
            pmode = PayMode()
            for key in payDict.keys():
                self.totalTender(key, "T", payDict[key])
            if (restvalue > 0):
                self.totalTender(ccName, "T", restvalue)
        #FIN IMPRESION FORMAS DE PAGO ----------------------------------------------
        OfficialNrClose = self.closeFiscalReceipt(1)
        if not OfficialNr:
            OfficialNr = OfficialNrClose
        return OfficialNr

    def __printCreditNote(self,inv):
        from Invoice import Invoice
        from Customer import Customer
        cust = Customer.bring(inv.CustCode)
        if not cust: return
        #Pasaporte no soporta letras en hasar 320, se manda como encabezado
        TaxRegNr = inv.TaxRegNr
        passPort = None
        if (cust.IDType == 7 and self.PrinterModel == 0):
            TaxRegNr = "0"
            passPort = inv.TaxRegNr
        if self.hasHeader:
           self.printHeaderTrailer(inv,"Invoice",passPort)
        self.setCustomerData(inv.TaxRegType,TaxRegNr,inv.Address,inv.City,inv.Province,inv.CustName,cust.IDType)
        generalDiscount=0.0
        self.setEmFP(inv.AppliesToInvoiceNr)
        OfficialNr = self.openDNFH(inv.DocType,inv.SerNr)
        totalPriceflag = False
        priceType = "Price"
        rowType = "RowNet"
        if (self.DFPC.printVATPrice):
            totalPriceflag = True
            priceType = "VATPrice"
            rowType = "RowTotal"
        
        discountByVATCode = {}
        for item in (it for it in inv.Items if it.ArtCode and it.RowTotal <= 0):
            dispatchNr = ""
            exec("price = item.%s "%priceType)
            #SI OCULTAN LOS DESCUENTOS
            if (self.DFPC.HideItemDiscounts):
                if (item.Discount != 0 and item.Qty != 0):
                    exec("price = item.%s / item.Qty "%rowType)
            qty = item.Qty
            if item.UnitFactor:
                qty *= item.UnitFactor
                if self.DFPC.HideItemDiscounts:
                    price /= item.UnitFactor  
            self.itemLine(item.ArtCode, item.Name, price, -1 * qty, 0,item.Discount, item.LuxGoodTax, item.SerialNr,dispatchNr, item.VATCode, totalPriceflag, inv.InvoiceType)
            if item.Discount:
                exec("rowT = item.%s "%rowType)
                factor = 1
                if item.UnitFactor:
                    factor = item.UnitFactor
                delta = abs(rowT- price * item.Qty * factor)
                if (not self.DFPC.ResumeItemDiscounts):
                    #SE DEBE MANDAR EL DESCUENTO SOBRE EL ULTIMO ITEM
                    self.ItemDiscount(rowT, item.Discount, delta, inv.DocType,totalPriceflag)
                else:
                    try:
                        discountByVATCode[item.VATCode] += delta
                    except:
                        discountByVATCode[item.VATCode] = delta

        #LOS DESCUENTOS GENERALES DEBEN IR AL FINAL
        for item in (it for it in inv.Items if it.ArtCode and it.RowTotal > 0):
            exec("rowT = item.%s "%rowType)
            if (self.DFPC.ResumeItemDiscounts):
                try:
                    discountByVATCode[item.VATCode] += rowT
                except:
                    discountByVATCode[item.VATCode] = rowT
            else:
                self.ReturnRecharge(-1 * rowT, item.Name, item.VATCode, item.LuxGoodTax, totalPriceflag)

        if (self.DFPC.ResumeItemDiscounts and len(discountByVATCode.keys())):
            for vat in discountByVATCode.keys():
                self.ReturnRecharge(-1 * discountByVATCode[vat] , "", vat, item.LuxGoodTax, totalPriceflag)

        self.closeDNFH()
        return OfficialNr

    def printBarTab(self,bt,**kwargs):
        """ Print Fiscal if paid cash if on room account print non fiscal.
        En kwargs se puede recibir el parametro nonFiscal, que si el cual es
        recibido con el valor True, entnoces se imprime un comprobante no
        fiscal de la comanda. 
        En caso de que la comando posea un ResNr asociado (numero de reserva)
        entonces tambien se genera un documento no fiscal."""
        nonFiscal = kwargs.get("nonFiscal",False)

        if (nonFiscal):
            #self.printNonFiscalDoc()
            self.clearHeaders()
            self.openNonFiscalDoc()
            self.printNonFiscalText("Comanda Nr %i" % bt.SerNr)
            for item in bt.BarTabRows:
                needed, disc = 0 , 0
                if not item.Invalid:
                    needed = len("%.2f" % item.RowTotal) +1
                    desc = "%2.f x %s [%.2f]" %(item.Qty,item.ArtName,item.VATPrice)
                    rest = self.maxStr -len(desc)
                    if rest <= needed:
                        desc=desc[:-(needed -rest)]
                    r= self.maxStr - needed
                    desc = desc.ljust(r,".")
                    if (item.Discount):
                        rTotal = item.VATPrice * item.Qty
                    else:
                        rTotal = item.RowTotal
                    Text = "%s %.2f" % (desc,rTotal)
                    self.printNonFiscalText(Text)
                    if (item.Discount):
                        discount = item.RowTotal - item.VATPrice * item.Qty
                        needed = len("%.2f" % discount) +1
                        if (discount < 0):
                            desc = "Descuento "
                        else:
                            desc = "Recargo "
                        desc += "%.2f porc.  [%.2f]" %(item.Discount , abs(discount))
                        rest = self.maxStr -len(desc)
                        if rest <= needed:
                            desc=desc[:-(needed -rest)]
                        r= self.maxStr - needed
                        desc = desc.ljust(r,".")
                        Text = "%s" % (desc)
                        self.printNonFiscalText(Text)
            long = self.maxStr -needed
            desc = "TOTAL".ljust(long ,".")
            self.printNonFiscalText("%s %.2f" %(desc,bt.Total) )
            # Print Payments
            covers = 1
            if bt.Covers: covers = bt.Covers
            self.printNonFiscalText("Consumo por comensal: %.2f" % (bt.Total/float(covers)))
            if bt.ResNr:
                self.printNonFiscalText("Cargos a Habitacion %s" % bt.Room)
                self.printNonFiscalText(" ")
                self.printNonFiscalText(" ")
            self.printNonFiscalText("Firma Cliente: ")
            self.printNonFiscalText(" ")
            self.printNonFiscalText(" ")
            if bt.Payments.count():
                for prow in bt.Payments:
                  self.printNonFiscalText("Formas de Pago")
                  self.printNonFiscalText("%s: %.2f" % (prow.Comment,prow.Paid))
                  
            else:      
                self.printNonFiscalText("Forma de Cancelacion no definida.")
            self.printNonFiscalText("Mozo %s "%bt.Waiter)
            self.printNonFiscalText("Nro. Mesa: %s" % bt.TableNr)
            self.closeNonFiscalDoc()
        else:
            #FACTURA O NC

            #TIPOS DE MONTOS A UTILIZAR
            VATFlag = False
            priceType = "Price"
            rowType = "RowNet"
            if (self.DFPC.printVATPrice):
                VATFlag = True
                priceType = "VATPrice"
                rowType = "RowTotal"

            from BarTab import BarTab
            isCreditNote = False
            factor = 1

            if (bt.Total < 0):
                isCreditNote = True
                factor = -1

            #HEADER:
            self.clearHeaders()
            headerList = []
            headerList.append("Nro de Comanda: %s"%  bt.SerNr)
            headerList.append("Mozo: %s " %bt.Waiter)
            headerList.append("Nro. Mesa: %s" % bt.TableNr)
            i = 3
            for header in headerList:
                self.SetHeaderTrailer(i, header)
                i += 1
            #FIN HEADERS
            from Customer import Customer
            cust = Customer.bring(bt.CustCode)
            if cust:
                self.setCustomerData(cust.TaxRegType,cust.TaxRegNr,cust.Address,cust.City,cust.Province,cust.Name,cust.IDType)
                if (isCreditNote):
                    self.setEmFP(None)
                    OfficialNr = self.openDNFH(cust.DocType,"")
                else:
                    OfficialNr = self.OpenFiscalReceipt(cust.DocType,0)
            else:
                if (isCreditNote):
                    OfficialNr = self.openDNFH(1,"")
                else:
                    OfficialNr = self.OpenFiscalReceipt(1,0)   # B y Factura Normal

            #PRIMERO SE MANDAN LOS ITEMS QUE TIENEN EL MISMO SIGNO DEL DOCUMENTO:
            # PARA FACTURA, > 0
            # PARA NC < 0
            for item in bt.BarTabRows:
                if (((item.RowTotal * factor) > 0 )and item.ArtCode != "" and not item.Invalid):
                    exec("rowT = item.%s "%rowType)
                    exec("price = item.%s "%priceType)
                    self.itemLine(item.ArtCode,item.ArtName,price,item.Qty*factor,0,None,None,"","","1",VATFlag,0) 
                    if (item.Discount):
                        delta = rowT - price * item.Qty 
                        if delta < 0: delta*=-1
                        self.ItemDiscount(rowT, item.Discount, delta, 1,VATFlag)

            discountByVATCode = {}

            #LOS DESCUENTOS GENERALES DEBEN IR AL FINAL
            for item in bt.BarTabRows:
                if (((item.RowTotal * factor ) < 0) and not item.Invalid): 
                    exec("rowT = item.%s "%rowType)
                    if (self.DFPC.ResumeItemDiscounts):
                        try:
                            discountByVATCode[item.VATCode] += rowT
                        except:
                            discountByVATCode[item.VATCode] = rowT
                    else:
                        self.ReturnRecharge(rowT * factor, item.ArtName, item.VATCode, 0.00, VATFlag)

            if (self.DFPC.ResumeItemDiscounts and len(discountByVATCode.keys())):
                for vat in discountByVATCode.keys():
                    self.ReturnRecharge(discountByVATCode[vat] , "", item.VATCode, 0.00, VATFlag)

            #mal, debe ser como en factura!
            #self.totalTender("Efectivo","T",bt.Total)
            if (not isCreditNote):
                #IMPRESION DE FORMAS DE PAGO ------------------------------------------

                from PayMode import PayMode
                paymentQty = bt.Payments.count()
                #hardcodeado porque puede ser que la forma de pago CC sea otra cosa
                ccName = "Forma de Cancelacion no definida." 
                paid = 0
                for pmode in bt.Payments:
                    paid += pmode.Paid
                restvalue = bt.Total - paid
                lines = 0
                if (restvalue > 0):
                    lines += 1
                lines += paymentQty
                #esta impresora solo permite enviar 4 lineas de pagos
                if (lines <= 4):
                    #puedo imprimir la descr de cada forma de pago
                    for pmode in bt.Payments:
                        self.totalTender(pmode.Comment,"T",pmode.Paid)
                    if (restvalue):
                        self.totalTender(ccName,"T",restvalue)
                else:
                    payDict = {}
                    #tengo que agrupar por tipo de la forma de pago
                    categorias = {}
                    categorias[0] = "Contado" #efect
                    categorias[1] = "Contado" #tarj de credito
                    categorias[2] = "Contado" #cheque
                    categorias[10] = "Contado" #cheque europeo 
                    categorias[9] = "Retencion Sufrida"
                    for pay in bt.Payments:
                        pmode = PayMode.bring(pay.PayMode)
                        if (pmode):
                            if (payDict.has_key(categorias[pmode.PayType])):
                                payDict[categorias[pmode.PayType]] += pay.Paid
                            else:
                                payDict[categorias[pmode.PayType]] = pay.Paid
                    pmode = PayMode()
                    for key in payDict.keys():
                        self.totalTender(key, "T", payDict[key])
                    if (restvalue > 0):
                        self.totalTender(ccName, "T", restvalue)
                #FIN IMPRESION FORMAS DE PAGO ----------------------------------------------
            else:
                self.closeDNFH()
            if (not isCreditNote):
                if self.PrinterModel != 2:
                    self.closeFiscalReceipt(1)
                else:
                    OfficialNr = self.closeFiscalReceipt(1)
            return OfficialNr


    def printDelivery(self,deliv):
        from Delivery import Delivery
        from Customer import Customer
        cust = Customer.bring(deliv.CustCode)
        if not cust: return
        self.printHeaderTrailer(deliv,"Delivery")
        self.setCustomerData(cust.TaxRegType,
                             cust.TaxRegNr,deliv.Address,
                             deliv.City,deliv.Province,deliv.CustName,cust.IDType)
        OfficialNr = self.openDNFH(3,str(deliv.SerNr))  # 3 = Remito
        for item in deliv.Items:
            description = self.getItemDescription(item.ArtCode,self.ffs(item.ArtName))
            self.PrintEmbarkItem("%s-%s" % (description,item.Qty))
        self.closeDNFH()
        if (self.DFPC.PaperCutterf):
            self.forwardPaper(10)
            self.cutPaper()
        # Copias adicionales
        for j in range(0,self.DFPC.DeliveryCopies):
            self.Reprint()
            if (self.DFPC.PaperCutterf):
                self.openDrawer()
        return OfficialNr

    # realiza un checkeo general sobre el invoice, previo al intento de impresion de la factura
    def checkInvoice(self,invoice):
        # si tipo de factura es A, entonces tiene que haber cliente, y ademas debe ser responsable
        # inscripto
        if (invoice.TaxRegType != 1): # 1:Consumidor Final
            from Customer import Customer
            cust = Customer.bring(invoice.CustCode)
            if not cust: return ErrorResponse("INVALIDVALUEERR"+invoice.CustCode)
            # 1: CUIT
            if cust.IDType != 1: return ErrorResponse("TAXREGNRNEEDED")
        return True

    def cancelFiscal(self):          
        # 3.5.4 Cerrar Comprabante no fiscal
        cmd = "%s" % (chr(64))               #4AH
        self.Sent2FiscPrinter(cmd)
        # 3.7.2 Reimpresion del ultimo documento emitido
        cmd = "%s" % (chr(152))  #98H
        self.Sent2FiscPrinter(cmd)

    def Reprint(self):      
        # 3.7.2 Cancelar documento
        cmd = "%s" % (chr(153))  #99H
        self.Sent2FiscPrinter(cmd)

    def SetDateTime(self):      
        Datum  = today().strftime("%d%m%Y")
        Today = today();
        hh    = now().time().hour
        mm    = now().time().minute
        ss    = now().time().second
        cmd = "%s%s%s%s%s%s%s" % (chr(88),S,Datum,S,hh,mm,ss)
        self.Sent2FiscPrinter(cmd)
  
    def getTimeDate(self):      
        # 3.8.2 Reportar Fecha y hora actual
        cmd = "%s" % (chr(89))  #59H
        ret =  self.Sent2FiscPrinter(cmd)
        cmd = "%s" % (chr(74))               #4AH
        self.Sent2FiscPrinter(cmd)
        return ret

    def SetFantasyName(self,Line,Text):      
        # 3.8.3 Programar texto del nombre de fantasia del propietario
        cmd = "%s%s%s%s%s" % (chr(95),S,Line,S,Text)  #5FH
        self.Sent2FiscPrinter(cmd)

    def SetHeaderTrailer(self,Line,Text):      
        # 3.8.5 Programar texto de encabezamiento y cola de documentos
        if Text =="" or Text==None: Text = " "
        log("SETHEADER: %s" % Text)
        cmd = "%s%s%s%s%s" % (chr(93),S,Line,S,self.ffs(Text[0:120]))  #5DH
        self.Sent2FiscPrinter(cmd)
    
    def closeNonFiscalDoc(self):      
        # 3.5.4 Cerrar Comprabante no fiscal
        cmd = "%s" % (chr(74))               #4AH
        self.Sent2FiscPrinter(cmd)

    # genera un diccionario para poder aplicar eval a las expresiones que
    # generan los headers y trailers.
    def __genVarSpace(self, record, recordName):
        from User import User
        from Customer import Customer
        try:
            from Reservation import Reservation
        except ImportError,e:
            pass
        varspace = {}
        cust = Customer.bring(record.CustCode)
        for fname in record.fieldNames():
            key = recordName+fname
            varspace[key] = utf8(record.fields(fname).getValue())
        #TODO: estandarizar el sig key para que sea Customer+fname
        for fname in cust.fieldNames():
            varspace[fname] = utf8(cust.fields(fname).getValue())
        us = User.bring (record.User)
        if us:
            varspace["UserName"] = us.Name
        if hasattr(record,"OriginNr") and record.OriginNr != None:
            if record.OriginType == record.Origin["Reservation"]:
                res = Reservation.bring(record.OriginNr)
                for fname in res.fieldNames():
                    key = "Reservation"+fname
                    varspace[key] = utf8(res.fields(fname).getValue())
                    #para compatibilidad con configuraciones anteriores.
                    oldkey= "Res"+fname
                    varspace[oldkey] = utf8(res.fields(fname).getValue())
                rooms = []
                for rrow in res.RoomRows:
                    rooms.append(rrow.Room)
                varspace["ResRooms"] = ",".join(rooms)
            else:
                obj = None
                try:    
                    rname = record.getOriginsByType()[record.OriginType]
                    sernr = str(record.OriginNr)
                    exec ("from %s import %s" % (rname,rname))
                    exec ("obj = %s.bring (%s)" % (rname,sernr))
                    for fname in obj.fieldNames ():
                        key= rname+fname
                        varspace[key] = utf8(obj.fields(fname).getValue())
                except:
                    pass
        return varspace

    def printHeaderTrailer(self,record,recordName="Invoice", passPort=None):
        from Delivery import Delivery
        self.clearHeaders()
        #parche, porque 
        if type(record) == Delivery:
            record.OriginNr = record.SONr
            record.OriginType = Delivery.Origin["SalesOrder"]
        varspace = self.__genVarSpace(record, recordName)
        from Currency import Currency
        from ExchangeRate import ExchangeRate
        b1, b2 = Currency.getBases()
        exRate = ExchangeRate.getRate(b2, today())
        varspace["dolcot"] = round(exRate.Value, 4)
        hlist = []
        if (passPort):
            self.DFPC.Header3 = '"Pasaporte: " + str(InvoiceTaxRegNr)'
        #Se quita el Header 3 para poner el pasaporte (En Hasar 320 solo se puede informar asi)
        fields = ["Header1","Header2","Header3","Footer1","Footer2","Footer3","Footer4"]
        for field in fields:
            formula = self.DFPC.fields(field).getValue()
            try:
                res = eval(formula, varspace,{"locals":varspace})
            except:
                res = ""
            hlist.append(res)
        self.writeHeaders(hlist)

    def setCustomerData(self,TaxRegType,TaxRegNr,Addr1,Addr2,Addr3,CustName,DocName):
        #alert(" set cust data")
        # 3.8.7 Datos del Comprador
        Address = "%s-%s-%s" % (Addr1,Addr2,Addr3)
        if (self.ticketflag) and (self.PrinterModel<>8):
          Address = ""
        Document = DOCEQ[DocName] 
        log("adress: %s" % Address)
        log("Documento: %s" % Document)
        Tipo = INSCRIPTION[TaxRegType]
        cmd = "%s%s%s%s%s%s" % (chr(98),S,self.ffs(CustName[0:self.maxStrCustomer]),S,self.ffs(string.replace(TaxRegNr,'-','')[0:11]),S)  #62H
        if self.PrinterModel == 2:
            cmd += "%s%s%s"  % (Tipo,S,Document)
        else:
            cmd += "%s%s%s%s%s"  % (Tipo,S,Document,S,self.ffs(Address[0:self.maxStrCustomer]))
        self.Sent2FiscPrinter(cmd)


    def delEmFP(self):      
        # 3.8.8 Borrar informacion remito 
        cmd = "%s%s%s%s%s" % (chr(147),S,"1",S,DEL)  #93H
        self.Sent2FiscPrinter(cmd)
        cmd = "%s%s%s%s%s" % (chr(147),S,"2",S,DEL)  #93H
        self.Sent2FiscPrinter(cmd)

    def setEmFP(self,InvoiceSerNr):   
        # 3.8.8 Cargar informacion remito - y factura de credito
        # algunos modelos require un nro con este formato !
        InvoiceNr = "0000-00000000"         
        from Invoice import Invoice
        inv = Invoice.bring(InvoiceSerNr)
        if inv:
          InvoiceNr = inv.OfficialSerNr[-13:]
        cmd = "%s%s%s%s%s" % (chr(147),S,"1",S,str(InvoiceNr))  #93H
        self.Sent2FiscPrinter(cmd)

    def getEmFP(self):      
        cmd = "%c%s%s" % (148,S,"1")  #94H   
        pars = self.Sent2FiscPrinter(cmd)

    def cutPaper(self):      
        # Corte de Papel ( solo 615F y PR4F )
        cmd = "%s" % (chr(80))  
        self.Sent2FiscPrinter(cmd)

    def forwardPaper(self,Lines=5):      
        if (self.ticketflag): 
            lf = str(Lines).rjust(2,"0")
            cmd = "%s%s%s" % (chr(80),S,lf) 
            ret = self.Sent2FiscPrinter(cmd)
            self.closeNonFiscalDoc()
            return ret
        else:
            log("forwardPaper: Solo las etiquetadores hasar poseen esta funcion.")   
            return True
            
    def openDrawer(self):      
        # Apertura de Cajon ( solo 615F y PR4F )
        cmd = "%s" % (chr(123))               #7BH
        self.Sent2FiscPrinter(cmd)

    def statusRequest(self,type=None):
        cmd = "%s" % (chr(42))       #2AH
        statusList = self.Sent2FiscPrinter(cmd)
        stats = {}
        stats["Estado Fiscal"] = self.FiscalStatus
        stats["Estado Impresora"] = self.PrinterStatus

        stats["Ultimo Ticket B"] = statusList[0]
        i = int(statusList[1],16)                       # hex2dec
        if i < len(AUXSTATUS):
          stats["Estado Aux"] = AUXSTATUS[i]
        else:
          stats["Estado Aux"] = "Unknown aux status %s " % i
        stats["Ultimo Ticket A"] = statusList[2]
        stats["Ultimo N/C B"] = statusList[4]
        stats["Ultimo N/C A"] = statusList[5]
        stats["Doc Status"] = ""
        if (statusList[3][3] == "1"):
          stats["Doc Status"] = "Ult Documento Cancelado"
        if int(statusList[3][:2]):
          stats["Doc Status"] = "Un %s se encuentra abierto " % DocTypes[statusList[3][:2]]
        stats["Est.Aux"] = statusList[1]
          
        sd = {}
        sd["Global"] = stats
        sd["Impresora"] = self.processStatus(self.PrinterStatus,PRINTERSTATUS)
        sd["Fiscal"] = self.processStatus(self.FiscalStatus,FISCALSTATUS)
        return sd
                
    def processStatus(self,binStateString,stateList): 
        stats = {}
        i=0 
        for nibble in binStateString: 
            name = "%s. %s" % (str(i).rjust(2,"0"),stateList[i])
            stats[name] = nibble
            i+=1
        return stats

    def STATPRN(self):      
        # 3.2.2 Consulta de Estado Intermedio
        cmd = "%s" % (chr(161))               #A1H
        self.Sent2FiscPrinter(cmd)

            
    def GetPrinterVersion(self):
        # 3.2.6 Consulta de Version de Controlador Fiscal
        cmd = "%s" % (chr(127))               #7FH
        return self.Sent2FiscPrinter(cmd)

    def dailyClose(self,Type,Printflag):   
        # 3.3.2 Cierre de jornada fiscal solo "X" o "Z"
        #para limpiar los datos que hayan quedado de otro comprobante
        self.clearHeaders()
        cmd = "%s%s%s" % (chr(57),S,Type)               #39H
        res = self.Sent2FiscPrinter(cmd)
        self.closeNonFiscalDoc()
        #ToDo: averiguar los nombres y el orden de los campos de la respuesta
        d =  {}
        fields = range(0,len(res))
        i=0
        for field in fields:
            d[field] = res[i]
            i+=1
        return d

    def DailyReport(self,DaySpec=""):      
        # 3.3.2 Cierre de jornada fiscal solo "X" o "Z"
        # DaySpec is Z oAAMMDD
        if DaySpec=="": 
          Type = "Z"
        else:
          Type = "F"
        cmd = "%s%s%s%s%s" % (chr(60),S,DaySpec,S,Type)      #3CH
        self.Sent2FiscPrinter(cmd)

    def GetWorkingMemory(self,Type):      
        # 3.3.6 Consulta Memoria de trabajo
        cmd = "%s" % (chr(103))               #67H
        self.Sent2FiscPrinter(cmd)
 
    def OpenFiscalReceipt(self,DocType,InvoiceType):
        """ Habre un documento fiscal.
        Retorna el numero de factura official (el que se imprime en la factura). """
        # 3.4.1 Abrir Comprobante Fiscal
        hlistfct = ["A","B","B"]
        hlistnd = ["D","E","E"]
        if self.ticketflag and (self.PrinterModel not in (2, 8)):
                hDocType = "T"
                tmp = "S"            # slip ("S") or ticket ("T")
        else:
            tmp = "T"
            if InvoiceType == 0:
                hDocType = hlistfct[DocType]
            elif InvoiceType == 1:
                self.DFPC.appendMessage("Error: Invallid Syntax para nota de credito")
            elif InvoiceType ==2:
                hDocType = hlistnd[DocType]
        cmd = "%s%s%s%s%s" % (chr(64),S,hDocType,S,tmp)       #40H
        pars = self.Sent2FiscPrinter(cmd)
        if len(pars):
            return pars[0]
        else:  
            log("OpenFiscalReceipt didnt return a Invoice Number")
            return ""

    def PrintFiscalText(self,Text):      
        # 3.4.2 Imprimir Texto Fiscal - despues del comando printlineitem
        cmd = "%s%s%s%s%s" % (chr(65),S,Text,S,"0")               #41H
        self.Sent2FiscPrinter(cmd)

    #TODO: el siguiente método debería ubicarse en FiscalPrinter.
    def formatPrice(self, price):
        """ formatPrice (float())=>str ().
        Formatea el precio segun la cantidad de decimales configurada en 
        FiscalPrinter."""
        presition = self.DFPC.DecimalsPrecision or 2
        if presition < 0:
            raise Exception ("Presicion decimal no puede ser negativa.")
        format= "%%.%if" % presition
        fPrice = format % price
        return fPrice

    #dada una descripcion larga, la separa en palabras para que quede mas "lindo"
    def getWrapDescription(self, des):
        words = des.split(" ")
        lines = []
        tmp = ""
        for w in words:
            if ((len(tmp) + 1 + len(w)) <= self.maxStr ):
                tmp += w + " "
            else:
                lines.append(tmp)
                tmp = w[:self.maxStr] + " "
        if (tmp):
            lines.append(tmp)
        return lines
        #parts = len(lines)
        #parts -= 1
        #if (parts > self.maxFiscalTextCalls):
        #    parts = self.maxFiscalTextCalls


    #dada una descripcion me dice cuantos textos fiscales se deberian imprimir
    #def getFiscalQty(self, desc):
    #    import math
    #    parts = float(len(desc)) / float(self.maxStr)
    #    #redondeo para arriba
    #    parts = int(math.ceil(parts))
    #    parts -= 1
    #    if (parts > self.maxFiscalTextCalls):
    #        parts = self.maxFiscalTextCalls
    #    return parts

    #dada una descripcion me dice cuantos textos fiscales se deberian imprimir
    def getFiscalQty(self, descLines):
        parts = len(descLines)
        parts -= 1
        if (parts > self.maxFiscalTextCalls):
            parts = self.maxFiscalTextCalls
        return parts


    def itemLine(self, ArtCode, ArtName, Price, Qty, mQty2, mRebate,ImpIntern,serialNr,dispatchNr, itemVATCode,TotalPricef,InvoiceType):
        Desc = self.getItemDescription(ArtCode,self.ffs(ArtName))
        descLines = self.getWrapDescription(Desc)   
        actual = 0
        i = 0
        if (self.DFPC.WrapItemDescription):
            totalFiscalLines = self.getFiscalQty(descLines)
            while (i < totalFiscalLines):
                #llamo a fiscaltext[actual:actual+self.maxStr]
                #self.PrintFiscalText(Desc[actual:actual+self.maxStr])
                self.PrintFiscalText(descLines[i])
                i +=1
                #actual += self.maxStr
        #Desc= Desc[actual:actual+self.maxStr]
        Desc = descLines[i]
        self._itemLine(Desc, Price, Qty, mQty2, mRebate,ImpIntern,serialNr,dispatchNr, itemVATCode,TotalPricef,InvoiceType)

        
    def _itemLine(self, Desc, Price, Qty, mQty2, mRebate,ImpIntern,serialNr,dispatchNr, itemVATCode,TotalPricef,InvoiceType):
        from VATCode import VATCode
        vc = VATCode.bring(itemVATCode)
        if (vc):
          Rate      = "%.2f" % (vc.Percent)
          Rate = Rate.rjust(5,"0")
          #print "Percent %.2f" % (vc.Percent)
          #print "Rate = %s" % Rate
        else:
            # importante !
            Rate = "00.00"
        if ImpIntern:
            sImpIntern = "%.2f" % (ImpIntern)
        else:  
            if self.ticketflag:
                sImpIntern = "0.00"
            else:
                sImpIntern = "0"
        if (Qty > 0):
            # M: Suma monto 
            ctipo = "M"   
        else:
            #m: Resta Monto
            ctipo = "m"
        Qty = abs(Qty)
        if TotalPricef:
            # T: Precio Total, otro: precio base
            totalPrice = "T"
        else:
            totalPrice = "X"

            ## mmm INVESTIGATE !!!
            #Rate= "**.**"
        #fPrice = "%.2f" % Price
        #define la presicion decimal
        Price = abs(Price)
        fPrice = self.formatPrice(Price)
        #Desc = self.getItemDescription(ArtCode,self.ffs(ArtName))
        #Desc= Desc[0:self.maxStr]
        cmd = "%s%s%s%s%.2f%s%s%s" % (chr(66),S,self.ffs(Desc),S,Qty,S,fPrice,S)   #42H
        cmd += "%s%s%s%s%s%s%s%s%s" % (Rate,S,ctipo,S,sImpIntern,S,"0",S,totalPrice)
        self.Sent2FiscPrinter(cmd)

    def getItemDescription(self,code,name):
        if self.ticketflag:
          Desc = self.ffs(name)
        else:
          Desc = "%s - %s" % (code,self.ffs(name))
        #Desc= Desc[0:self.maxStr]
        return Desc
        
    # con el redondeo se pierden algunos decimales, por lo que a esta hay que pasarle
    # el monto 
    
    def ItemDiscount(self,RowNet,Discount,Amount,DocType,InclVat=False):
        #  Descuento sobre un item
        if (Discount > 0):
          Type = "m"
          Text = "Descuento del %.2f porc." % Discount
        else:
          Type = "M"
          Text = "Recargo del %.2f porc." % (Discount * -1)
        vatFactor = "X"
        #if (DocType==99): vatFactor = "T"
        if InclVat: vatFactor = "T"  # con iva
        else: vatFactor="X"
        mAmount = "%.2f" % Amount
        cmd = "%s%s%s%s%s%s%s%s%s%s%s" % (chr(85),S,Text[0:self.maxStr],S,mAmount,S,Type,S,"0",S,vatFactor)     #55H
        self.Sent2FiscPrinter(cmd)

     
    def GeneralDiscount(self,Text,Amount,DocType,InclVat=True):
        """ GeneralDiscount (Text, Ammount, DocType, InclVat) -> None.
        Aplica un Descuento o Recargo general. Text es la descripcion, Amount 
        es el monto y dependiendo de su signo se aplica descuento o recargo,
        DocType corresponde con el DocType del invoice de OO, y InclVat indica
        si se el descuento/recargo incluye (True) o no incluye iva (False) por
        defecto esta en False.
        """
        Type=None
        if (Amount < 0):
          Type = "m"         # "m" Descuento
          mAmount = "%.2f" % (Amount * -1)
        else:
          Type = "M" # "M" Recargo
          mAmount = "%.2f" % Amount
        if InclVat: vatFactor = "T"  # con iva
        else: vatFactor="X" 
        #if (DocType==99): vatFactor = "T"
        cmd = "%s%s%s%s%s%s%s%s%s%s%s" % (chr(84),S,self.ffs(Text[0:self.maxStr]),S,mAmount,S,Type,S,"0",S,vatFactor) 
        self.Sent2FiscPrinter(cmd)
 

    def ChargeRNI(self,Amount):      
        # 3.4.7 Recargo IVA a Responsable no Inscripto
        cmd = "%s%s%f" % (chr(97),S,Amount)    # 61H
        self.Sent2FiscPrinter(cmd)



    def Subtotal(self):
        # 3.4.9 SubTotal
        cmd = "%s%s%s%s%s%s%.2f" % (chr(67),S,"",S,"x",S,"0")    # 43H
        self.Sent2FiscPrinter(cmd)
 
    def ReceiptText(self,Text):      
        # 3.4.10 ReceiptText
        cmd = "%s%s%f" % (chr(151),S,Text[0:105])    # 97H
        self.Sent2FiscPrinter(cmd)
 

    def totalTender(self,PayDeal,strType,Amount):      
        # 3.4.11 Total
        # strType = C:Cancela T:Pago
        #if (ImpFP.BaseCur == 0):
        #  tmp = MulRateToBase1(CurncyCode,tMonto,FrRate,ToRateB1,ToRateB2,BaseRate1,BaseRate2,2);
        #else:
        #  tmp = MulRateToBase2(CurncyCode,tMonto,FrRate,ToRateB1,ToRateB2,BaseRate1,BaseRate2,2);
        Amount = self.formatPrice(Amount)
        cmd = "%s%s%s%s%s%s%s%s%s" % (chr(68),S,self.ffs(PayDeal[0:self.maxStr]),S,Amount,S,strType,S,"0")    # 44H
        self.Sent2FiscPrinter(cmd)

    #TODO: hacer que se utilize el parametro qCopy, para imprimir una cantidad de
    # copias elegida.
    def closeFiscalReceipt(self,qCopy):      
        # 3.4.12 Cerrar Comprobante Fiscal
        if (self.PrinterModel in (1,6)):
            #alert(self.DFPC)
            #0 es Cant de copias - Solo para la hasar330F, PL-9F, PL-8F, 322F  (SP)
            cmd = "%s%s%s" % (chr(69),S,"0")               #45H
        else: 
            cmd = "%s" % (chr(69))               #45H
        res = self.Sent2FiscPrinter (cmd)
        if self.PrinterModel != 2:
            try:
                docNr = res[2]
            except:
                log("PrintInvoice->closeFiscalReceipt(): Problema obteniendo Numero de factura")
            return ""
        else:
            try:
                docNr = res[0]
            except:
                log("PrintInvoice->closeFiscalReceipt(): Problema obteniendo Numero de factura")
                return ""
        return docNr

  
    def getLastCAI(self,invoiceNr):      
        # 3.3.9 Consultar numero de CAI del ultimo doc emitido
        # Solo para la hasar SMH/P 330F SMH/P-9F - version 2 de modelos SMH/P-8F y SMH/P-322F
        cmd = "%s%s%s" % (chr(126),S,"0")               #7EH
        #devuelve (IdDocumento,PrimeraPagina,UltimaPagina,CAI)
        pars = self.Sent2FiscPrinter(cmd)    
        from SalesCAI import SalesCAI
        sc = SalesCAI()
        sc.SerNr = invoiceNr
        sc.CAI = pars[-1]
        sc.FiscalPrinter = True
        sc.store()
        return 
  
    def openNonFiscalReceipt(self):      
        # 3.5.1 Abrir Comprobante no Fiscal
        cmd = "%s" % (chr(72))               #48H
        self.Sent2FiscPrinter(cmd) 
        #pass
 
    def openNonFiscalDoc(self):      
        # 3.5.1 Abrir Comprobante no Fiscal
        cmd = "%s" % (chr(72))               #48H
        self.Sent2FiscPrinter(cmd) 

    def printNonFiscalText(self,Text):      
        # 3.5.3 Imprimir texto no fiscal
        cmd = "%s%s%s%s%s" % (chr(73),S,Text,S,"0")    #49H
        self.Sent2FiscPrinter(cmd)
 
    def closeNonFiscalReceipt(self):      
        # 3.5.4 Cerrar Comprabante no fiscal
        cmd = "%s" % (chr(74))               #4AH
        self.Sent2FiscPrinter(cmd)

    def getFantasyName(self):      
        cmd = "%s%s%s" % (chr(146),S,"1") 
        return self.Sent2FiscPrinter(cmd)[0]

    def openDNFH(self,DocType,DocNr): 
        # 3.6.1 Abrir documento no fiscal homologado
        # hDocType: R for Nota de Credito A,
        #          S for Nota de Credito B o C
        #          r for Remito
        #          s for Orden de Salida
        #          t for Resumen de cuenta
        #          x for Recibo X

        hlistnc = ["R","S","S","r"]
        hDocType = hlistnc[DocType]
        if (self.ticketflag):  
           tmp = "S"                 # slip ("S") or ticket ("T") 
        else:
           tmp = "T"
        if (self.DFPC.PrinterModel == 8):
            # aunque la documentacion dice lo contrario, con un param demas no funciona
            cmd = "%s%s%s%s%s" % (chr(128),S,str(hDocType),S,str(tmp))      
        else:
            #NOTAS DE CREDITO, EL ULTIMO CAMPO ES OPCIONAL, PERO SI SE PASA DA ERROR
            #if (hDocType == "R" or hDocType=="S"):
            #    cmd = "%c%s%s%s%s" % (128,S,hDocType,S,tmp)    #80H
            #else:
            #CA comento para ver si es la causa de error al imprimir NC en hasar 330 (2-12)
            cmd = "%s%s%s%s%s%s%s" % (chr(128),S,str(hDocType),S,tmp,S,str(DocNr))    #80H


        res = self.Sent2FiscPrinter(cmd)
        try:
            officialNr = res[0]
        except:
            log("PrintInvoice->openDNFH(): Problema obteniendo Numero de factura")
            return ""
        return officialNr

    #def PrintDNFHInfo (self, lineNr, text):
    #    cmd = Command (chr(133),str(lineNr),self.ffs (text)[0:120])
    #    self.Sent2FiscPrinter(str(cmd))

    def PrintEmbarkItem(self,ArtName,Qty):      
        # 3.6.2 Imprimir Item en Remito
        cmd = "%s%s%s%s%s%s%s" % (chr(130),S,ArtName[0:120],S,Qty,S,"0")  #82H
        self.Sent2FiscPrinter(cmd)
 
    def PrintQuotationItem (self,ArtName):
        # 3.6.4 Imprimir Item en Cotizacion
        cmd = "%s%s%s%s%s" % (chr(132),S,ArtName[0:120],S,"")      #84H
        self.Sent2FiscPrinter(cmd)

    def closeDNFH(self):      
        # 3.6.5 Cerrar Comprabante no fiscal homologado
        if (self.DFPC.PrinterModel == 6):
          cmd ="%s%s%s" % (chr(129),S, "0")
        else:  
          cmd = "%c" % (129)               #81H        
        self.Sent2FiscPrinter(cmd)

    #si amountType = T indica que se le esta pasando el precio Total,
    #cualquier otra cosa se interpreta como precio base
    #si amount < 0 -> resta (m)
    #si amount > 0 -> suma (M)
    #TODO: ver tema de impuestos
    def ReturnRecharge(self, amount, description, vatCode, taxes, totalPriceflag=False):
        #SOLO SE UTILIZARA PARA DESCUENTOS POR ESO SIEMPRE IRA "m"
        #SEGUN EL SIGNO DE amount SE PONDRA NEGATIVO O POSITIVO
        signType = "m"
        #Quito esta palabra porque parece es reservada, da error
        #desc = "Descuento "
        desc = "D"
        """if (amount > 0):
            signType= "M"
            desc = "Recargo"
        """
        amount = abs(amount)
        famount = "%.2f" %(amount)
        from VATCode import VATCode
        vc = VATCode.bring(vatCode)
        if (vc):
            vatPercent = "%.2f" % (vc.Percent)
            desc += vatPercent
        amountType = "B"
        display = "0" #no tiene importancia
        if (totalPriceflag):
            amountType = "T"
        if (not description):
            description = "%s%s" %(desc,description)
        #descuento-recargo
        calificadorOperacion= "B"
        maxDesc= MaxReturnRechargeDesc[self.PrinterModel]
        cmd  ="%s%s%s%s"%(chr(109),S,self.ffs(description)[:maxDesc], S)
        cmd +="%s%s%s%s%s%s%s%s%s%s"%(famount, S, vatPercent,S, signType, S, taxes, S, display, S)
        cmd +="%s%s%s" %(amountType, S, calificadorOperacion)
        log("FISCAL PRINTER - RETURN RECHARGE ------------ LOG")
        log("Comando : %s"%str(cmd))
        log("monto: %s"%famount)
        log("signo: %s"%signType)
        log("amountType: %s"%amountType)
        log("calificadorOperacion: %s"%calificadorOperacion)
        res = self.Sent2FiscPrinter(cmd)
        log("Respuesta: %s"%str(res))
        log("END FISCALPRINTERLOG-------------------------")

    def getStatusTypeList(self):
        return ["Hasar",]


    def getHeaders(self):
        list = []
        for line in ["3","4","5","11","12","13","14"]:
            cmd = "%s%s%s" % (chr(94),S,line)  #0x5e
            res=self.Sent2FiscPrinter(cmd) # doesnt return anything
            if len(res):
                list.append(res[0])
            else: 
                list.append("")
        return list

    def clearHeaders(self):
        i = 0 
        for line in ["3","4","5","11","12","13","14"]:
           tmp = DEL
           cmd = "%s%s%s%s%s" % (chr(93),S,line,S,tmp)  #0x5dh
           self.Sent2FiscPrinter(cmd) # doesnt return anything
           i+=1


    def writeHeaders(self,list):
        i = 0 
        for line in ["3","4","5","11","12","13","14"]:
            tmp = list[i][0:120] # max is 48
            if tmp:
                cmd = "%s%s%s%s%s" % (chr(93),S,line,S,self.ffs(tmp))  #0x5dh
                self.Sent2FiscPrinter(cmd) # doesnt return anything
            i+=1

    PERCEPTION_OTHER=0 #Otro tipo de Percepcion
    PERCEPTION_IVA_TAX=1 #Percepcion de IVA a una tasa de IVA determinada.
    PERCEPTION_GLOBAL_IVA=2 #Percepcion Global de IVA
    #TODO: Probar funcionamiento con percepciones de iva.
    # Percepciones ingresos brutos funcionan OK.
    # Ojo, una vez emitido el siguiente, no se puede proseguir con la venta 
    # quedando solamente habilitados los comandos, ChargeNonRegisteredTax, 
    # TotalTender y CloseFiscalReceipt o el mismo Perceptions
    def Perceptions(self, percType, Alic, Text, Amount):
        if percType == self.PERCEPTION_OTHER:
            alic = "**.**"
        else:
            alic = ("%.2f" % round(Alic,2)).rjust(5,"0") #NN.NN
        text = self.ffs(Text[0:20])
        amount = ("%.2f" % round(Amount,2)).rjust(9,"0") #NNNNNN.NN
        cmd = Command(chr(96), alic, text, amount)
        return self.Sent2FiscPrinter(str(cmd))

