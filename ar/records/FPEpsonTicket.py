#encoding: utf-8
from time import sleep
from OpenOrange import *
import string
from FPEpson import FPEpson
from Comunication import *
from FPDriver import FPDriver


class FPEpsonTicket(FPEpson):

    def printInvoice(self,inv):
        if self.forceTicketFactura(inv):
            res = FPEpson.printInvoice(self,inv)
            return res

        self.openFiscalTicket(inv)
        for item in inv.Items:
            if (item.ArtCode != ""):
                ImpInt = 0         # impuestos internos
                dispatchNr = ""    # Later fill in with procedure fetching this number from latest import
                if inv.DocType == 0:
                    price = item.Price
                else: 
                    price = item.VATPrice
                self.ticketItemLine(item.Name,price,item.Qty,0,
                          item.Discount,ImpInt,item.SerialNr,dispatchNr,item.VATCode)
        rate=21.00
        for itr in inv.Taxes:
            if (itr.TaxCode == "PIVA"):
                self.Perceptions(2,rate,"Percepcion de iva",itr.Amount)
            elif itr.TaxCode.startswith("IBR"):
                #jaa: ojo con el texto que va en este lugar si ponemos:
                # "Percepcion Ingresos Brutos, ya deja de funcionar", de la 
                # prueba empirica, palabra explosiva pareciera que es "Ingresos",
                # pero no me animo a probar "Percepcion" tampoco!.
                self.Perceptions (0, rate, "Perc. de IIBB %s" % itr.TaxCode[3:], itr.Amount)
            else:
                self.DFPC.appendMessage("OpenOrange No puede aplicar este impuesto a la impresion!: %s" % itr.TaxCode)
        paid = 0
        for pmode in inv.Payments:
          self.ticketPayDeal(pmode.Comment,pmode.Paid)
          paid += pmode.Paid
        restvalue = inv.Total - paid
        if (restvalue > 0):
          from PayTerm import PayTerm
          pt = PayTerm.bring(inv.PayTerm)
          self.ticketPayDeal(pt.Name,restvalue)
        res = self.closeFiscalTicket(inv)
        return res

    def ticketPayDeal(self,txPayDeal,Amount):
        strType = "T"     # always this value
        mAmount = "%.2f" % (Amount)
        mAmount = mAmount.replace(".","").rjust(9,"0")
        cmd = "%s%s%s%s%s%s%s" % (chr(68),S,self.ffs(txPayDeal[0:27]),S,mAmount,S,strType) #44
        self.Sent2FiscPrinter(cmd)

    def openFiscalTicket(self, inv):
        if inv.InvoiceType == 1:
            Type = "M"
        else:
            Type = "C" # solo para farmacias es distinto
            cmd = "%s%s%s" % (chr(64),S,Type)  #40H
            self.Sent2FiscPrinter(cmd)

    def closeFiscalTicket(self,inv):
        if inv.InvoiceType == 1:
            Type = "M"
        else:
            Type = "T"
            cmd = "%s%s%s" % (chr(69),S,Type)  #45H
            res = self.Sent2FiscPrinter(cmd)
        try:
            docNr = res[0]
        except:
            print ("PrintInvoice->closeFiscalReceipt(): Problema obteniendo Numero de factura")
            return ""
        return docNr
            

    def ticketItemLine(self,ArtName,mPrice,mQty1,mQty2, 
        mRebate,mImpInt,serialNr,dispatchNr,VATCode):
        # no se pueden mandar items negativos    
        # No points or commas are allowed ! Fixed 2 decimals
        # ctype "m" : Sum  / "M" : Deduct
        # Rate should have a "0" if not defined
        from VATCode import VATCode
        vc = VATCode()
        vc.Code = VATCode
        vc.load()
        (Desc1,Desc2,Desc3) = (chr(127),chr(127),chr(127))
        if serialNr:
           Desc1 = "Numero de Serie: %s"  % (serialNr)
        if dispatchNr:
           Desc1 += "Numero de Despacho: %s"  % (serialNr)
        if (mRebate):
          mPrice= ((mPrice * mRebate)/100) * mQty1
          ctipo = "R"        # Bonificacion
          if (mPrice<0):
            mPrice = - mPrice;
        else:
          if (mPrice>0):
            ctype = "M"
          else:
            mPrice = - mPrice
            ctype  = "M"
        Qty1      = "%.3f" % (mQty1)
        Qty1 = Qty1.replace(".","").rjust(8,"0")
        Qty2      = "%.2f" % (mQty2)
        Qty2 = Qty2.replace(".","").rjust(8,"0")
        if (vc.Percent):
          Rate      = "%d" % (vc.Percent * 100)
          Rate = Rate.replace(".","").rjust(4,"0")
        else:
          Rate = "0000"
        InclPrice = "%.2f" % (mPrice)
        InclPrice = InclPrice.replace(".","").rjust(9,"0")
        ImpIntern = "%.8f" % (mImpInt)
        ImpIntern = ImpIntern.replace(".","").rjust(17,"0")
        cmd = "%s%s%s%s%s%s%s%s%s%s" % (chr(66),S,self.ffs(ArtName[0:20]),S,Qty1,S,InclPrice,S,Rate,S) #42H
        cmd += "%s%s%s%s%s%s%s" % (ctype,S,"0",S,"00000000",S,ImpIntern)    
        self.Sent2FiscPrinter(cmd)

    def openNonFiscalDoc(self):
        type = "D"   # o U
        cmd = "%s" % (chr(72))  #48H
        res = self.Sent2FiscPrinter(cmd) # doesnt return anything

    def Perceptions (self, percType, Alic, Text, Amount):
        if percType == 0:
            FPEpson.Perceptions (self, percType, Alic, Text, Amount)
        else:
            self.DFPC.appendMessage("Tipo de percepcion Erronea para esta Etiquetadora")
