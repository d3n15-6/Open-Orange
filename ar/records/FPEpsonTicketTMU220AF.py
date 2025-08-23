#encoding: utf-8
from time import sleep
from OpenOrange import *
import string
from FPEpson import FPEpson
from FPEpsonTicket import *
from Comunication import *
from FPDriver import FPDriver
from FPDriver import Command

#TODO: migrar este codigo al FPEpsonTicket.py. En la 2000AF este codigo imprime
# sin problemas. Habria que probar que pasa con la 2002
NONFISCAL_MAXSTR = 40

# NOTA Que: Un ticket-Factura se imprime a Resp. Inscr y Monotributista todo el resto recibo Ticket

class FPEpsonTicketTMU220AF(FPEpsonTicket):

    def printInvoice(self,inv):
        ##############################forceTicketFactura########################
        # solo valido para etiquetadoras. retorna True si el documento a imprimir
        # debe ser ticket factura. Los casos puntuales son:
        # - si se debe imprimir nota de credito /debito
        # - el el tipo de documento es A.
        # - si el cliente es Responsable Inscripto o Monotributista.
        # - el monto total del documento alcanza o supera los $ 1000.
        # - si existe algun item cuyo precio con iva incluido supera los $ 1000.
        # - si esta configurado asi (y no se cumple ninguna de las anteriores).

        if self.forceTicketFactura(inv):
            from Customer import Customer
            cust = ifNone(Customer.bring(inv.CustCode),Customer())
            originNr = None
            if inv.InvoiceType == 1:
                record = inv.getOriginRecord()
                if record:
                    originNr = record.OfficialSerNr
            self.openFiscalReceipt(inv.TaxRegType,inv.DocType,inv.TaxRegNr,inv.Address,inv.City,inv.Province,cust.FantasyName,inv.CustName,inv.InvoiceType, originNr)
        else:
            self.openFiscalTicket(inv.InvoiceType)
        invTypeFactor =1
        if inv.InvoiceType == 1: #nota de credito
            invTypeFactor = -1
        sleep(2) #dudoso
        #IDEM HASAR, PRIMERO POSITIVOS DESPUES NEGATIVOS
        for item in (it for it in inv.Items if it.ArtCode and (it.RowTotal * invTypeFactor) >=  0):
            ImpInt = 0
            dispatchNr = ""
            if inv.DocType == 0:
                price = item.Price
            else: price = item.VATPrice
            if self.forceTicketFactura(inv):
                itemQty = item.Qty * invTypeFactor
                self.itemLine(item.Name,price,itemQty,0,item.Discount,ImpInt,item.SerialNr,dispatchNr,item.VATCode) #ver Rate
            else:
                self.ticketItemLine(item.Name,price,item.Qty,0,item.Discount,ImpInt,item.SerialNr,dispatchNr,item.VATCode)

        for item in (it for it in inv.Items if it.ArtCode and (it.RowTotal * invTypeFactor) <  0):
            ImpInt = 0
            dispatchNr = ""
            if inv.DocType == 0:
                price = item.Price
            else: price = item.VATPrice
            if self.forceTicketFactura(inv):
                itemQty = item.Qty * invTypeFactor
                self.itemLine(item.Name,price,itemQty,0,item.Discount,ImpInt,item.SerialNr,dispatchNr,item.VATCode) #ver Rate
            else:
                self.ticketItemLine(item.Name,price,item.Qty,0,item.Discount,ImpInt,item.SerialNr,dispatchNr,item.VATCode)

        if self.forceTicketFactura(inv):
            rate=21.00
            for itr in inv.Taxes:
                if itr.TaxCode == "PIVA":
                    # por ahora mejor solo utiliza 0 ya que este codigo estÃ¡ siendo
                    # utilizado por la impresora 2000 AF, la cual solo acepta este modo.
                    self.Perceptions(0,rate,"Perc. de IVA",abs(itr.Amount))
                elif itr.TaxCode.startswith("IBR"):
                    #jaa: ojo con el texto que va en este lugar si ponemos:
                    # "Percepcion Ingresos Brutos, ya deja de funcionar", de la 
                    # prueba empirica, palabra explosiva pareciera que es "Ingresos",
                    # pero no me animo a probar "Percepcion" tampoco!.
                    #self.Perceptions(0,rate,"Perc. de IIBB BsAs",itr.Amount)
                    self.Perceptions(0, rate, "Perc. de IIBB %s" % itr.TaxCode[3:], abs(itr.Amount))
                else:
                    self.DFPC.appendMessage("OpenOrange No puede aplicar este impuesto a la impresion!: %s" % itr.TaxCode)
            paid = 0
            for pmode in inv.Payments:
                self.payDeal(pmode.Comment,pmode.Paid*invTypeFactor)
                paid += pmode.Paid
            restvalue = inv.Total - paid
            restvalue*=invTypeFactor
            if (restvalue > 0):
                from PayTerm import PayTerm
                pt = PayTerm.bring(inv.PayTerm)
                self.payDeal(pt.Name,restvalue)
            officialNr = self.closeFiscalReceipt(inv.DocType,inv.InvoiceType)
        else:
            paid = 0
            for pmode in inv.Payments:
                self.ticketPayDeal(pmode.Comment,pmode.Paid)
                paid += pmode.Paid
            restvalue = inv.Total - paid
            if (restvalue > 0):
                from PayTerm import PayTerm
                pt = PayTerm.bring(inv.PayTerm)
                self.ticketPayDeal(pt.Name,restvalue)
            officialNr = self.closeFiscalTicket()
        return officialNr

    def generalDiscount(self,txPayDeal,Amount):
        """ aplica un descuento general al documento fiscal(solo puede llamarse antes de cerrar """
        if Amount < 0: Amount*=-1
        mAmount = "%.2f" %(Amount)
        mAmount = mAmount.replace(".","").rjust(9,"0")
        cmd = "%s%s%s%s%s%s%s" %(chr(100),S,self.ffs(txPayDeal[0:25]),S,mAmount,S,'D') #0x44h
        return self.Sent2FiscPrinter(cmd)

    def openFiscalTicket(self, invoiceType,pharmacy=False):
        print "FPEpsonTicketTMU220AF.openFiscalTicket():1"
        # nota de credito
        if invoiceType == 1: 
            type = "M"
        else:
                # G - farmacia
                # C - cualquier otro
                if pharmacy: 
                    type = "G"
                else: 
                    type = "C"
        cmd = Command(chr(64),type)  #40H
        print "FPEpsonTicketTMU220AF.openFiscalTicket():1, Log del comando"
        cmd.log()
        print "FPEpsonTicketTMU220AF.openFiscalTicket():2, END Log del comando"
        return self.Sent2FiscPrinter(str(cmd))

    def openFiscalReceipt(self,TaxRegType,DocType,VATNr,Addr1,Addr2,Addr3,FantasyName,CustName, InvoiceType, originNr=None):
        from FiscalPrinter import FiscalPrinter
        from TaxSettings import TaxSettings
        PRINTCOUNT = {1:chr(0x31),2:chr(0x32),3:chr(0x33),4:chr(0x34),5:chr(0x35)}
        Copias = 1
        ExitType = 'C' #continuo    "S" = hoja suelta
        CharSize = "12"
        if InvoiceType == 0:
            InvType = FPDriver.InvoiceTypes[3]
        else:
            InvType = FPDriver.InvoiceTypes[InvoiceType]
        taxSettings = TaxSettings()
        if not taxSettings.load():
            self.appendMessage("Debe Configurar sus de seteos de impuestos(modulo Impuestos, Seteos de Impuestos)")
            return None
        emisorTaxInscType = FPDriver.INSCRIPTION [taxSettings.TaxRegType]
        custTaxInscType = FPDriver.INSCRIPTION [TaxRegType]
        if not CustName: CustName =  " "
        else: CustName = self.ffs(CustName[0:20])
        if not FantasyName: FantasyName =  " "
        else: FantasyName = self.ffs(FantasyName[0:20])
        if not Addr1: Addr1 =  " "
        else: Addr1 = self.ffs(Addr1[0:20])
        if not Addr2: Addr2 =  " "
        else: Addr2 = self.ffs(Addr2[0:20])
        if not Addr3: Addr3 =  " "
        else: Addr3 = self.ffs(Addr3[0:20])
        if InvoiceType == 0:
            remitoRelacionado1 = "-"
        elif originNr:
            remitoRelacionado1 = originNr
        else:
            remitoRelacionado1 = "00000000" # si es nota de credito debe incluir el nro origen.
        remitoRelacionado2 = " "
        if (TaxRegType in [0,3,5]):                #bug fix lo 02/2007
            custDocType= "CUIT"
            custDocNr = string.replace(VATNr,'-','')[0:11]
        else:
            custDocType = "DNI"
            custDocNr = string.replace(VATNr, '-','')[0:11]
        #60H
        #N:no imprimir leyenda "Bienes de Uso"
        leyenda = "N"
        #B: imprimir leyenda "Bienes de Uso", necesario si emisor es resp. 
        # inscripto y destinatario es resp. no inscripto.
        if taxSettings.TaxRegType ==0 and  TaxRegType == 0:
            leyenda="B"
        cmd = Command(chr(96),InvType, ExitType, FPDriver.DocTypes[DocType], \
                PRINTCOUNT[Copias], 'F', CharSize, emisorTaxInscType,       \
                custTaxInscType, self.ffs(CustName) , self.ffs(FantasyName), custDocType,       \
                custDocNr, leyenda, self.ffs(Addr1), self.ffs(Addr2), self.ffs(Addr3), remitoRelacionado1, \
                remitoRelacionado2, "C" )
        print "FPEpsonTicketTMU220AF.openFiscalReceipt():5, Log del comando"
        cmd.log()
        print "FPEpsonTicketTMU220AF.openFiscalReceipt():5, END Log del comando"
        return self.Sent2FiscPrinter(str(cmd)) 

    def closeFiscalReceipt(self,DocType,InvoiceType):
        # mapeo, si es ticketeadora, debe enviar 'T' en lugar de 'F'.
        # T significa Ticket-Factura.
        if InvoiceType == 0:
            InvoiceType = 3
        return FPEpsonTicket.closeFiscalReceipt(self, DocType, InvoiceType)

    def printFiscalText(self,text):
        cmd = "%s%s%s" %(chr(65),S,self.ffs(text[0:20]))
        return self.Sent2FiscPrinter(cmd)

    def closeFiscalTicket(self):
        cmd = Command(chr(69),'T')  #45H
        print "FPEpsonTicketTMU220AF.closeFiscalTicket():1, Comand log"
        cmd.log()
        print "FPEpsonTicketTMU220AF.closeFiscalTicket():2, END Comand log"
        try:
            ret = self.Sent2FiscPrinter(str(cmd))
            ticketNr = str(ret[0])
            return ticketNr
        except: return "000"

    def ticketItemLine(self, ArtName, mPrice, mQty1, mQty2, mRebate, mImpInt,
                        serialNr,dispatchNr,vatcode):
        # no se pueden mandar items negativos    
        # No points or commas are allowed ! Fixed 2 decimals
        # ctype "M" : Suma  / "R" : Bonificacion
        # Rate should have a "0" if not defined
        from VATCode import VATCode
        vc = VATCode.bring(vatcode)
        if mRebate:
            self.ticketItemLine(ArtName, mPrice, mQty1, mQty2,0,mImpInt, serialNr,
                dispatchNr, vatcode)
            mPrice= ((mPrice * mRebate)/100) 
            ctype= "R"        # Bonificacion
            if mQty1<0:
                mQty1 = - mQty1
        else:
          if mQty1>0:
            ctype = "M"
          else:
            mQty1 = - mQty1
            #ctype  = "M" 
            ctype  = "R" # item negativo, resta
        Qty = "%.3f" % mQty1
        Qty = Qty.replace(".","").rjust(8,"0")
        if (vc.Percent):
          Rate = "%d" %(vc.Percent * 100)
          Rate = Rate.replace(".","").rjust(4,"0")
        else:
          Rate = "0000"
        InclPrice = "%.2f" %(mPrice)
        InclPrice = InclPrice.replace(".","").rjust(9,"0")
        #TODO: esta ticketadora tambien soporta precion de la forma nnnnnnn.nnnn
        #es decir 7 enteros y 4 decimales con el ".", podria hacerce
        ImpIntern = "%.8f" %(mImpInt)
        ImpIntern = ImpIntern.replace(".","").rjust(15,"0")     
        cmd = Command(chr(66),self.ffs(ArtName[0:11]),Qty,InclPrice,Rate,ctype, \
                      "0"*5, "0"*8, ImpIntern)
        print "FPEpsonTicketTMU220AF.ticketItemLine():1, Comienzo del Log"
        cmd.log()
        print "FPEpsonTicketTMU220AF.ticketItemLine():2, END del Log"
        return self.Sent2FiscPrinter(str(cmd))

    def openNonFiscalDoc(self):
        type = "D"   # o U
        cmd = "%s" %(chr(72))  #48H
        res = self.Sent2FiscPrinter(cmd) # doesnt return anything

    def printBarTab(self,bt,**kwargs):
        """ Print Fiscal if paid cash if on room account print non fiscal.
        En kwargs se puede recibir el parametro nonFiscal, que si el cual es
        recibido con el valor True, entnoces se imprime un comprobante no
        fiscal de la comanda. 
        En caso de que la comando posea un ResNr asociado(numero de reserva)
        entonces tambien se genera un documento no fiscal."""
        nonFiscal = kwargs.get("nonFiscal",False) or (bt.ResNr)
        if (nonFiscal):
            # imprime un reporte no fiscal
            self.openNonFiscalDoc()
            self.printNonFiscalText("Comanda Nr %i" % bt.SerNr)
            self.printNonFiscalText("Mesa: %s" % bt.TableNr)
            for item in bt.BarTabRows:
                needed , desc = 0 , 0
                if not item.Invalid:
                    needed = len("%.2f" % item.RowTotal) +1
                    desc = "%2.f x %s [%.2f]" %(item.Qty,item.ArtName,item.VATPrice)
                    rest = NONFISCAL_MAXSTR -len(desc)
                    if rest <= needed:
                        desc=desc[:-(needed -rest)]
                    r= NONFISCAL_MAXSTR - needed
                    desc = desc.ljust(r,".")
                    Text = "%s %.2f" %(desc,item.RowTotal)
                    self.printNonFiscalText(Text)
            long = NONFISCAL_MAXSTR -needed
            desc = "TOTAL".ljust(long ,".")
            self.printNonFiscalText("%s %.2f" %(desc,bt.Total) )

            # Print Payments
            covers = 1
            if bt.Covers: covers = bt.Covers
            self.printNonFiscalText("Consumo por comensal: %.2f" %(bt.Total/float(covers)))
            if bt.ResNr:
                self.printNonFiscalText("Cargos a Habitacion %s" % bt.Room)
                self.printNonFiscalText(" ")
                self.printNonFiscalText(" ")
                self.printNonFiscalText("Firma Cliente: ")
                self.printNonFiscalText(" ")
                self.printNonFiscalText(" ")
            elif bt.Payments.count():
                for prow in bt.Payments:
                  self.printNonFiscalText("Formas de Pago")
                  self.printNonFiscalText("%s: %.2f" %(prow.Comment,prow.Paid))
            else:
                self.printNonFiscalText("Forma de Cancelacion no definida.")
            self.closeNonFiscalDoc()
        else:
            # genera un invoice (que no se guarda) para enviarlo a imprimir
            # mmm johnny doesnt work that well ... forma de Hasar entonces
            self.openFiscalTicket(0)
            sleep(2) #dudoso
            for bti in bt.BarTabRows:
                if (bti.ArtCode != "" and not bti.Invalid):
                    price = bti.VATPrice
                    self.ticketItemLine(bti.ArtName,price,bti.Qty,0,None,0,None,None,bti.VATCode)
            paid = 0
            for pmode in bt.Payments:
                self.ticketPayDeal(pmode.Comment,pmode.Paid)
                paid += pmode.Paid
            restvalue = bt.Total - paid
            if (restvalue > 0):
               message("error")
            officialNr = self.closeFiscalTicket()
            return officialNr

    def Perceptions(self, percType, Alic, Text, Amount):
        FPEpson.Perceptions(self, percType, Alic, Text, Amount)
