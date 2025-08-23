#encoding: utf-8
#coding=iso-8859-15

from time import sleep
from OpenOrange import *
import string
from FPDriver import FPDriver
from Comunication import *
from FPDriver import Command

S   = chr(28)      # 0x1Ch separador
DEL = chr(127)
MAXSTR = 20
MAXSTRDESCRIPTION=MAXSTR
FISCALSTATUS = ["Error Memoria Fiscal",
                "Error RAM",
                "Poco Bateria",
                "Comando No conocido",
                "Datos Invalidos",
                "Comando No valido para Estado Fiscal",
                "Desbordamiento de Datos",
                "Memoria Fiscal llena",
                "Memoria Fiscal casi llena",
                "Impresora Fiscalizado",
                "Impresora Fiscalizado",
                "Hay que hacer cierre Journada Fiscal",
                "Documento Fiscal Abierto",
                "Documento Fiscal Abierto",
                "Impresion Inicializada",
                "Checkbit"
                ]
PRINTERSTATUS = ["No se Usa",
                   "No se Usa",
                   "Falla de Impresora",
                   "Impresora fuera de linea",
                   "No se Usa",
                   "No se Usa",
                   "Buffer impresora lleno",                   
                   "Buffer impresora vacio",                   
                   "Entrada Frontal preparada 1",                   
                   "Entrada Frontal preparada 2",                   
                   "No se Usa",
                   "No se Usa",
                   "No se Usa",
                   "No se Usa",
                   "No hay papel",
                   "Checkbit"]

HEADERS={  50:"Header1",
           51:"Header2", 
           52:"Header3",
           53:"Header4",
           54:"Header5",
           55:"Header6",
           57:"Header7",
           58:"Header8",
           59:"Header9",
           60:"Header10",
           61:"Header11",
           11:"Footer1",
           12:"Footer2",
           13:"Footer3",
           14:"Footer4",
           15:""}

STATUSTYPELIST = ["N","P","C","A","D"]              
class FPEpson(FPDriver):

    # Epson Command Table
    commandTable = {   chr(96): "OpenFiscalReceipt",
                       chr(98): "itemLine",
                       chr(42): "statusRequest",
                       chr(100): "payDeal",
                       chr(101): "closeFiscalReceipt",
                   }



    # TODO: lo que sigue es un error o esta hecho a proposito (constructor mal nombrado)
    #       verificarlo y arreglarlo si es necesario
    def __init_(self):
        self.paperCutterf = True
    
    def sentACK(self):
        pass

    def setHeaders (self):
        pass
    def setTrailers (self):
        pass

    def printInvoice(self,inv):
        """ print invoice on fiscal printer epson """
        if (self.hasHeader):
            try:
                self.CleanHeader()
                self.CleanFooter()
                self.printHeaderTrailer(inv)
            except:
                log ("PrintInvoice->printHeaderTrailer (): Error seteando encabezado y pie de documento fiscal")
        from Customer import Customer
        cust = Customer.bring(inv.CustCode)
        self.openFiscalReceipt(inv.TaxRegType,inv.DocType,inv.TaxRegNr,inv.Address,inv.City,inv.Province,cust.FantasyName,inv.CustName,inv.InvoiceType)
        firstOfficialNr = self.getCurrentDocumentNr()# cuando hay transporte, se salva el primer numero de documento

        #CA
        if (inv.InvoiceType == 0 or inv.InvoiceType == 2): #Invoice or DebitNote
            self.processInvoiceItems(inv)
        else:
            self.processCreditNoteItems(inv)

        rate=21.00
        for itr in inv.Taxes:
            if (itr.TaxCode == "PIVA"):
                self.Perceptions(2,rate, "Perc.I.V.A.",itr.Amount)
            elif (itr.TaxCode.startswith("IBR")):
                #self.Perceptions(0, rate, "Perc. I.B." % itr.TaxCode[3:], itr.Amount)
                self.Perceptions(0, rate, "Perc.I.B.%s" %(itr.TaxCode[3:]), itr.Amount)
        """
        paid = 0
        for pmode in inv.Payments:
          self.payDeal(pmode.Comment,pmode.Paid)
          paid += pmode.Paid
        restvalue = inv.Total - paid
        if (restvalue > 0):
          from PayTerm import PayTerm
          pt = PayTerm.bring(inv.PayTerm)
          self.payDeal(pt.Name,restvalue)"""


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
        #esta impresora solo permite enviar 3 lineas de pagos
        if (lines <= 3):
            #puedo imprimir la descr de cada forma de pago
            for pmode in inv.Payments:
                self.payDeal(pmode.Comment,pmode.Paid)
            if (restvalue):
                self.payDeal(ccName,restvalue)
        else:
            payDict = {}
            #tengo que agrupar por tipo de la forma de pago
            categorias = {}
            categorias[0] = "Contado"
            categorias[1] = "Contado"
            categorias[2] = "Contado"
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
                self.payDeal(key, payDict[key])
            if (restvalue > 0):
                self.payDeal(ccName, restvalue)
        #FIN IMPRESION FORMAS DE PAGO ----------------------------------------------
        print "CERRANDO DOCUMENTO --------"
        # ultimo numero de comprobante utilizado
        lastOfficialNr = self.closeFiscalReceipt(inv.DocType,inv.InvoiceType)
        print "LISTO, RETORNANDO NUMERO"
        if firstOfficialNr:
            return firstOfficialNr
        return lastOfficialNr


    def processInvoiceItems(self, inv):
        discItems = [] # items con qty negativos, significan descuentos sobre el total
        for item in inv.Items:
            price=item.Price
            if item.Qty < 0:
                discItems.append(item)
                continue
            if (item.ArtCode != ""):
                ImpInt = 0         # impuestos internos
                dispatchNr = ""    # Later fill in with procedure fetching this number from latest import
                itemQty=item.Qty
                if inv.DocType == 0:
                    itemPrice=item.Price
                else: itemPrice = item.VATPrice
                itemQty=item.Qty
                # verifica si el item es de descuento, si es asi lo que hace es
                # enviar el price en negativo para que itemLine lo pueda 
                # distinguir como tal.
                #if itemQty < 0:
                #    itemPrice*=-1
                #    itemQty*=-1 
                if self.mustTransport(): 
                    sleep(2) # por las dudas le damos tiempo a chupar el papel
                    self.transport() # transporte por cantidad exedida
                    #if not firstOfficialNr:
                    #    firstOfficialNr = nr
                self.itemLine(item.Name,itemPrice,itemQty,0,
                              item.Discount,ImpInt,item.SerialNr,
                              dispatchNr,item.VATCode) #ver Rate
        for item in discItems:
            if self.mustTransport(): 
                sleep(2) # por las dudas le damos tiempo a chupar el papel
                self.transport() # transporte por cantidad exedida
            if inv.DocType == 0:
                discAmount=item.RowNet
            else:
                discAmount=item.RowTotal
            self.generalDiscount(item.Name, discAmount)

    def processCreditNoteItems(self, inv):
        for item in inv.Items:
            price=item.Price

            if (item.ArtCode != ""):
                ImpInt = 0         # impuestos internos
                dispatchNr = ""    # Later fill in with procedure fetching this number from latest import
                itemQty=item.Qty
                if inv.DocType == 0:
                    itemPrice=item.Price
                else: itemPrice = item.VATPrice
                itemQty=item.Qty
                # verifica si el item es de descuento, si es asi lo que hace es
                # enviar el price en negativo para que itemLine lo pueda 
                # distinguir como tal.
                #if itemQty < 0:
                #    itemPrice*=-1
                #    itemQty*=-1 
                if self.mustTransport (): 
                    sleep(2) # por las dudas le damos tiempo a chupar el papel
                    self.transport() # transporte por cantidad exedida
                    #if not firstOfficialNr:
                    #    firstOfficialNr = nr
                self.itemLine(item.Name,itemPrice,itemQty*-1,0,
                              item.Discount,ImpInt,item.SerialNr,
                              dispatchNr,item.VATCode) #ver Rate


    def printHeaderTrailer(self,inv):
        self.CleanHeader()
        self.CleanFooter()
        varspace = {}  
        from Customer import Customer
        cust = Customer.bring(inv.CustCode)
        for fname in cust.fieldNames():
            varspace[fname] = cust.fields(fname).getValue()
        for fname in inv.fieldNames():
            varspace[fname] = inv.fields(fname).getValue()
        if (inv.OriginType == inv.Origin["Reservation"]) and (inv.OriginNr):
          from Reservation import Reservation
          res = Reservation()
          res.SerNr = inv.OriginNr
          res.load()
          for fname in res.fieldNames():
             key= "Reservation"+fname
             varspace[key] = res.fields(fname).getValue()
          rooms = []   
          for rrow in res.RoomRows:
             rooms.append(rrow.Room)
          varspace["ReservationRooms"] = ",".join(rooms)
        else: 
          print "printHeaderTrailer(): originType no parece ser de Reserva"
        try:
            print "calculando 0"
            import ExchangeRate
            print "calculando 1"
            import Currency
            print "calculando 2"
            totalBase = ExchangeRate.convertWithFromRate(inv.Total, inv.CurrencyRate, inv.Currency,Currency.getBase2(), inv.TransDate)
            varspace["TotalBase2"] = totalBase
        except:
            print "ERROR CALCULANDO TotalBase2"
        fieldTrans = {"Header1":"50","Header2":"51","Header3":"52",
                    "Footer2":"12","Footer3":"13"}
        #fieldTrans = {"Header1":"50","Header2":"51","Header3":"52"}
        for field in fieldTrans.keys():
            formula = self.DFPC.fields(field).getValue()
            try:
                print "FORMULA: [%s]" % str(formula)
                text= eval(formula,varspace)
                print "TEXT=[%s]" % text
                maxlength=40
                if field.startswith("F"): maxlength=128 #128 chars maximo
                text = text[0:maxlength]
            except:
                text = ""
            print "EN EPSON HEADER AND TRAILER(8)"
            self.SetHeaderTrailer(fieldTrans[field], self.ffs(text))

    # TODO: verificar si este codigo funciona tambien en Hasar, si es asi 
    #       habria que moverlo hacia FPDriver.py
    def CleanHeader(self):
        self.SetHeaderTrailer("50",chr(127))
        self.SetHeaderTrailer("51",chr(127))
        self.SetHeaderTrailer("52",chr(127))

    # TODO: verificar si este codigo funciona tambien en Hasar, si es asi 
    #       habria que moverlo hacia FPDriver.py
    def CleanFooter(self):
        self.SetHeaderTrailer("11",chr(127))
        self.SetHeaderTrailer("12",chr(127))
        self.SetHeaderTrailer("13",chr(127))


    def printBarTab(self,bt,**kwargs):
        """ Print Fiscal if paid cash if on room account print non fiscal.
        En kwargs se puede recibir el parametro nonFiscal, que si el cual es
        recibido con el valor True, entnoces se imprime un comprobante no
        fiscal de la comanda. 
        En caso de que la comando posea un ResNr asociado (numero de reserva)
        entonces tambien se genera un documento no fiscal."""
        nonFiscal = kwargs.get("nonFiscal",False) or (bt.ResNr)
        if (nonFiscal):
            #self.printNonFiscalDoc()
            self.openNonFiscalDoc()
            self.printNonFiscalText("Comanda Nr %i" % bt.SerNr)
            for item in bt.BarTabRows:
                needed , desc = 0 , 0
                if not item.Invalid:
                    needed = len("%.2f" % item.RowTotal) +1
                    desc = "%2.f x %s [%.2f]" %(item.Qty,item.ArtName,item.VATPrice)
                    rest = MAXSTR -len(desc)
                    if rest <= needed:
                        desc=desc[:-(needed -rest)]
                    r= MAXSTR - needed
                    desc = desc.ljust(r,".")
                    Text = "%s %.2f" % (desc,item.RowTotal)
                    self.printNonFiscalText(Text)
            long = MAXSTR -needed
            desc = "TOTAL".ljust(long ,".")

            self.printNonFiscalText("%s %.2f" %(desc,bt.Total) )
            self.closeNonFiscalDoc()
        else:
            from BarTab import BarTab
            from Customer import Customer
            cust = Customer.bring(bt.CustCode)
            if not cust: return cust
            #self.printHeaderTrailer(inv)
            OfficialNr = self.openFiscalReceipt(cust.TaxRegType,1,cust.TaxRegNr,cust.Address,                             
            cust.City,cust.Province,cust.FantasyName,cust.Name,1)# B y Factura Normal
            for item in bt.BarTabRows:
                if (item.RowTotal > 0 and not item.Invalid and item.ArtCode != ""):
                    self.itemLine(item.ArtName,item.VATPrice,item.Qty,0,None,None,None,None,None)

            # items de descuento general, luego de estos no puede imprimirse un item "normal"
            for item in bt.BarTabRows:
                if (item.RowTotal < 0 and not item.Invalid): 
                    self.GeneralDiscount(item.Name,item.RowTotal,inv.DocType)

            self.closeFiscalReceipt(1, 1)
            #if (self.DFPC.PaperCutterf):
            #    self.forwardPaper(10)
            #    self.cutPaper()
            # Copias adicionales
            #for j in range(0,self.DFPC.F1):
            #    self.Reprint()
            #if (self.DFPC.PaperCutterf):
            #    self.openDrawer()
            #self.closeFiscalReceipt(1,1)
            return OfficialNr









    # realiza un checkeo general sobre el invoice, previo al intento de impresion de la factura
    def checkInvoice(self,invoice):
        # si tipo de factura es A, entonces tiene que haber cliente, y además debe ser responsable
        # inscripto
        if (invoice.TaxRegType != 1): # 1:Consumidor Final
            from Customer import Customer
            cust = Customer.bring(invoice.CustCode)
            if not cust: return ErrorResponse("INVALIDVALUEERR"+invoice.CustCode)
            # 1: CUIT
            if cust.IDType != 1: return ErrorResponse("TAXREGNRNEEDED")
        return True




    def getFiscalandPrinterStatus(self,ps,fs):
        bstr_pos = lambda n: n>0 and bstr_pos(n>>1)+str(n&1) or ''
        binstr = lambda n: n>0 and bstr_pos(n>>1)+str(n&1) or ''   
        hex2binstr = lambda n: binstr(int(n,16))
        printstat = hex2binstr(ps).rjust(16,"0")
        fiscstat = hex2binstr(fs).rjust(16,"0")
        #alert(ps +":" + printstat)
        #alert(fs +":" + fiscstat)
        fiscalText = ""
        printerText = ""
        for i in range(15):
            if int(fiscstat[i]):  fiscalText  += FISCALSTATUS[15-i]    + ", "
            if int(printstat[i]): printerText += PRINTERSTATUS[15-i] + ", "
        log("Estado fiscal: "+fiscalText)
        return 


    def openFiscalReceipt(self,TaxRegType,DocType,VATNr,Addr1,Addr2,Addr3,FantasyName,CustName,InvoiceType):
        from FiscalPrinter import FiscalPrinter
        Copias = 1
        #if (self.DFPC.F1 is not None and self.DFPC.F1 > 0):
        #    Copias = self.DFPC.F1
          # mal
        
        ExitType = 'C' #continuo    "S" = hoja suelta
        CharSize = "12"
        InvType = FPDriver.InvoiceTypes[InvoiceType]
        #F:form pre impreso
        #I:emisor

        CHARSIZE = {(10,"FX-880F"):chr(0x31), 
                    (12,"LX-300+"):chr(0x31),
                    (17,"FX-880F"):chr(31)  }
        PRINTCOUNT = {1:chr(0x31),2:chr(0x32),3:chr(0x33),4:chr(0x34),5:chr(0x35)}
        #InvType= "N" #debug CA
        cmd = "%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (chr(96), S,InvType, S,ExitType, S, FPDriver.DocTypes[DocType], S, PRINTCOUNT[Copias], S,'F',S,CharSize,S,'I',S,FPDriver.INSCRIPTION[TaxRegType],S)  #60H
        if not CustName: CustName =  " "
        if not FantasyName: FantasyName =  " "
        if not Addr1: Addr1 =  " "
        if not Addr2: Addr2 =  " "
        if not Addr3: Addr3 =  " "
        cmd += self.ffs(CustName[0:40]) + S + self.ffs(FantasyName[0:40]) + S
        if (TaxRegType in [0,3,5]):                #bug fix lo 02/2007
          cmd += "CUIT" + S + string.replace(VATNr,'-','')
        else:
          cmd += " " + S + " "
        #N:no impr "Bienes de Uso"
        
        cmd += S + "N" + S + self.ffs(Addr1[0:40]) + S + self.ffs(Addr2[0:40]) + S +  self.ffs(Addr3[0:40]) + S + " " + S + " "
        cmd += S + "G" #"C"
        self.Sent2FiscPrinter(cmd)   # There are no return values 

    def closeFiscalReceipt(self,DocType,InvoiceType):
        #DocType  debe coincidir con el utilizado p/abrirlo
        InvType = FPDriver.InvoiceTypes[InvoiceType]
        cmd = "%s%s%s%s%s%s%s" %(chr(101),S,InvType,S,FPDriver.DocTypes[DocType],S,DEL)  #65H
        res = self.Sent2FiscPrinter(cmd)
        try:
            docNr = res[0]
        except:
            print ("PrintInvoice->closeFiscalReceipt(): Problema obteniendo Numero de factura")
            return ""
        return docNr

    def payDeal(self,txPayDeal,Amount):
        strType = "T"     # always this value
        mAmount = "%.2f" %(Amount)
        mAmount = mAmount.replace(".","").rjust(12,"0")
        cmd = "%s%s%s%s%s%s%s" %(chr(100),S,txPayDeal[0:27],S,mAmount,S,strType) #64H
        self.Sent2FiscPrinter(cmd)

    # realiza un descuento general (o un recargo) sobre la factura 
    def generalDiscount(self,Text,Amount):
        fact = 1
        strType = "R"
        if Amount < 0: 
            strType = "D"
            fact = -1
        mAmount = "%.2f" %(Amount*fact)
        mAmount = mAmount.replace(".","").rjust(12,"0")
        cmd = "%s%s%s%s%s%s%s" %(chr(100),S,self.ffs(Text[0:27]),S,mAmount,S,strType) #64H
        self.Sent2FiscPrinter(cmd)

    def cancelFiscal(self):
        texto=" "
        cmd = "%s%s%s%s%s%s%s" %(chr(100),S,texto,S,'000000000000',S,'C')  #64H
        self.Sent2FiscPrinter(cmd)

    def dailyClose(self,Type,Printflag=True):      
        """ Encargada de realizar cierres de jornada.
            Type puede ser X o Z y definen el tipo de cierre
            Printflag si es True imprime el cierre de jornada indicado """
        fields = ["NrCierre","CantCanceladas","CantDocsHomo","CantDocsNoHomo","CantFacB",
                  "CantFacA","UltFacB","TotalFact","TotalIVA","TotalPercep","UltFacA"    ]
        par = ' '
        if Printflag: par = 'P'
        cmd = "%s%s%s%s%s" %(chr(57),S,Type,S,par)  #39H
        res =  self.Sent2FiscPrinter(cmd)
        self.closeNonFiscalDoc()
        try:
            dic = {}
            for i in range(0,len(fields)):
                dic[fields[i]] = res[i]
        except:
            dic = {}
        return dic

    def getCurrentDocumentNr(self): 
        """ retorna el numero previo de comprobante del tipo actual que se está imprimiendo """
        docType = self.getCurrentDocumentType()
        if docType == 'A': field = 'UltimaFactA'
        elif docType == 'B': field = 'UltimoTicketFactura'
        elif docType == 'C': field = 'UltimoTicketFactura'
        else: 
            print "getCurrentDocumentNr(): retornando con error para docType %s" % docType
            return "0"*8
        print "getCurrentDocumentNr(): retornando numero para tipo %s" % field
        ret = self.statusRequest('A')
        return str(ret.get(field,""))

    def getCurrentDocumentType(self):
        """ retorna el tipo del documento que se esta emitiendo """
        ret = self.statusRequest('D')
        return ret.get("TipoDocumentoActual","")

    def statusRequest(self,type):
        """ statusRequest (type) -> {}.
        type:
            N: Información Normal o compatible con todos los modelos.
            P: Información sobre las Características del Controlador Fiscal.
            C: Información sobre el contribuyente.
            A: Información sobre los contadores de documentos fiscales y no fiscales.
            D: Información sobre el documento que se esta emitiendo
        specificFlag: el nombre de un campo unico dentro un tipo elegido, que 
        se desee recuperar.
        """
        types = ["N","P","C","A","D"]
        fields = {"N" : ["UltimaFactB","UltimaFecha","UltimaHora","UltimaCierre","AuditoriaParial","AuditoriaTotal","Impresor","AuditoriaNr"],
                  "P" : ["Ancho10cpi","Ancho12cpi","Ancho17cpi","AnchoTickets","LineasDeValidacion","HabilitadoTicket","HabilitadoTicketFactura","HabilitadoFactura","DigitosCierre","Papel[s(cont)/r(Ticket)]","Modelo"],
                  "C" : ["CUIT","PuntoDeVta","Responsablidad","TasaIvaEstandar","","","RazonSocial"],
                  "A" : ["UltimaCierre","UltimaFactBSinProblemas","UltimoTicketFactura","UltimaFactASinProblemas","UltimaFactA","UltimaNrNoFiscal","UltimaNrNoFiscalHomo","UltimaNrNoFiscalHomoRef","09","10","11"],
                  "D" : ["DocumentoActual F/O/H","TipoDocumentoActual","Sin Uso"]
                  }
        if type in types:
            cmd = Command(chr(42),type)  #2AH
            res = self.Sent2FiscPrinter(str(cmd))
            dic = {}
            i = 0
            #for field in fields[type]:
            #    dic[field] = res[i]
#            log("###################################################MSP2")
#            log(("str(res)",str(res)))
            for resele in res:                    # turn around the logic makes it less printer dependent
#                try:
                    parname = fields[type][i]
#                    log(fields)
#                    log(("parname",parname))
#                    log(("resele",resele))
#                    log(("type",type))
#                    log(("i",i))
                    dic[parname] = resele
                    i += 1
#                except Exception,ex:
#                    log(("ERROR",ex))
#            log("###################################################MSP2")
            return dic
        else:
          return "Error: Wrong Parameter"

    def Cancel2(self):
        texto = "Cancelacion por el usuario"
        cmd = "%s%s%s%s%s%s%s%s%s" %(chr(68),S,texto,S,"0",S,'C',S,"")  #44H
        self.Sent2FiscPrinter(cmd)

    def itemLine(self,ArtName,mPrice,mQty1,mQty2, 
                mRebate,mImpInt,serialNr,dispatchNr,
                itemVATCode,Desca="",Descb="",Descc=""):
        # no se pueden mandar items negativos    
        # No points or commas are allowed ! Fixed 2 decimals
        # ctype "m" : Sum  / "M" : Deduct
        # Rate should have a "0" if not defined
        from VATCode import VATCode
        vc = VATCode()
        vc.Code = itemVATCode
        vc.load()
        (Desc1,Desc2,Desc3) = (DEL,DEL,DEL)
        if serialNr:
           Desc1 = "Numero de Serie: %s"  %(serialNr)
        if dispatchNr:
           Desc1 += "Numero de Despacho: %s"  %(serialNr)
        if mRebate:
          self.itemLine(ArtName,mPrice,mQty1,mQty2,0,mImpInt,serialNr,
                        dispatchNr,itemVATCode,Desca="",Descb="",Descc="")
          mPrice=((mPrice * mRebate)/100) 
          ctype= "R"        # Bonificacion
          if (mPrice<0):
            mPrice = - mPrice;
        else:
          if (mPrice>0):
            ctype = "M"
          else:
            mPrice = - mPrice
            #ctype  = "m"
            ctype  = "R"
        Qty1      = "%.3f" %(mQty1)
        Qty1 = Qty1.replace(".","").rjust(8,"0")
        Qty2      = "%.2f" %(mQty2)
        Qty2 = Qty2.replace(".","").rjust(8,"0")
        if (vc.Percent):
            Rate = "%d" %(vc.Percent * 100)
            Rate = Rate.replace(".","").rjust(4,"0")
        else:
            Rate = "0000"
        InclPrice = "%.2f" %(mPrice)
        InclPrice = InclPrice.replace(".","").rjust(9,"0")
        
        if mImpInt: 
            ImpIntern = "%.8f" %(mImpInt)  #9.8
            ImpIntern = ImpIntern.replace(".","").rjust(17,"0")
        else:
            ImpIntern = "0"*17
        mRNI      = "0"*4  # porcentaje a Resp No Insc.
        cmd = "%s%s%s%s%s%s%s%s%s%s" %(chr(98),S,self.ffs(ArtName[0:20]),S,Qty1,S,InclPrice,S,Rate,S) #62H
        cmd += "%s%s%s%s%s%s" %(ctype,S,"0",S,"00000000",S)    
        cmd += "%s%s%s%s%s%s%s%s%s" %(self.ffs(Desc1[0:20]),S,self.ffs(Desc2[0:20]),S,self.ffs(Desc3[0:20]),S,mRNI,S,ImpIntern)    
        self.Sent2FiscPrinter(cmd)   # no returns

    def transport(self,closeCurrent=True):
        """ Transporta a una nueva hoja de impresion, devuelve el numero del documento fiscal anterior"""
        #transportType = 'T'# close current and open new
        #transportType = 'O' # open new
        cmd = "%s%s%s%s%s%s%s%s%s" %(chr(92),S,'D',S,'P',S,'T',S,'T')
        ret1 = self.Sent2FiscPrinter(cmd)
        cmd = "%s%s%s%s%s%s%s%s%s" %(chr(92),S,'D',S,'P',S,'T',S,'O')
        ret2 =self.Sent2FiscPrinter(cmd)
        return ret2

    def mustTransport(self,quote=False):
        """ retorna true si se debe transportar para continuar imprimiendo en otra hoja"""
        if quote: itemType ='N' # cotización
        else: itemType='L'
        cmd = "%s%s%s%s%s" %(chr(92),S,'Q',S,itemType)
        ret = self.Sent2FiscPrinter(cmd)
        try:
            return ret[0] == 'N'
        except:
            print "mustTransport retorna False, por ocurrir una exepcion ret = [%s]" % str(ret)
            return False

    ################# Comandos para Docs No Fiscales #############################

    def openNonFiscalDoc(self):
        type = "D"   # o U
        cmd = "%s%s%s%s%s" %(chr(72),S,type,S,"O")  #48H
        sleep(0.3)
        return self.Sent2FiscPrinter(cmd) # doesnt return anything

    def printNonFiscalText(self,Text):
        cmd = Command(chr(73),self.ffs(Text[:40]))  #49H
        return self.Sent2FiscPrinter(str(cmd)) # doesnt return anything

    def closeNonFiscalDoc(self):
        cmd = Command(chr(74),'T')  #4AH
        return self.Sent2FiscPrinter(str(cmd)) 

    def forwardPaper(self):
        cmd = "%s" %(chr(75))  #4BH
        res = self.Sent2FiscPrinter(cmd) # doesnt return anything

    def getTimeDate(self):
        cmd = "%s" %(chr(89))  #59H
        res = self.Sent2FiscPrinter(cmd)
        d = "%s/%s/%s" %(res[0][0:2],res[0][2:4],res[0][4:6])
        t = "%s:%s" %(res[1][:2],res[1][2:4])
        return (d,t) 

    def OpenDrawer(self):
        cmd = "%s" %(chr(123))  #7BH
        self.Sent2FiscPrinter(cmd)

    def getHeaders(self):
        list=[] 
        for line in HEADERS.keys():
            ln = str(line).rjust(5,"0")
            cmd = "%s%s%s" %(chr(94),S,ln)  #0x5e
            res=self.Sent2FiscPrinter(cmd) # doesnt return anything
            list.append(res[0])
        return list

    def SetHeaderTrailer(self,nr,text):
        # formateado de la siguiente manera
        # fLine = str(nr).rjust(5,"0") 
        print "SetHeaderTrailer(): RECIBIDO TEXT [%s]" % text
        fLine = str(nr)
        if text: tmp = text
        else: tmp = DEL
        cmd = "%s%s%s%s%s" %(chr(93),S,self.ffs(fLine),S,tmp)  #0x5dh
        try:
            print "comando enviado: %s" % cmd.replace(S,"-")
        except:
            pass
        #if self.TestMode == True: print cmd.replace(S,"-")
        self.Sent2FiscPrinter(cmd)

    # Percepcion en factura(0x66h , 102 dec)
    # OJO: Si se envía una Percepción de IVA y no se han facturado productos 
    # a dicha tasa, el comando será rechazado.
    # PercType puede ser
    PERCEPTION_OTHER=0 #Otro tipo de Percepcion
    PERCEPTION_IVA_TAX=1 #Percepcion de IVA a una tasa de IVA determinada.
    PERCEPTION_GLOBAL_IVA=2 #Percepcion Global de IVA
    def Perceptions(self, percType, Alic, Text, Amount):
        # "O"= Otro tipo de Percepción
        # "T"= Percepción de IVA a una tasa de IVA determinada.
        # "I = Percepción Global de IVA
        # En Comprobantes tipo A se aceptan percepciones tipo O, I y T
        # En Comprobantes tipo B se aceptan percepciones tipo O e I.
        # En Comprobantes tipo C se aceptan percepciones tipo O.
        type_list = ["O","T","I"]
        type = type_list[percType]
        Amount = ("%.2f" % abs(Amount)).replace(".","")
        Amount = Amount.rjust(10,"0")
        #Amount = "%s.%s" %(Amount[:-2],Amount[-2:])
        Alic = "%.2f" % Alic
        Alic = Alic.replace(".","").rjust(4,"0")
        # parece increible, pero asi es!: si el tipo es T, entonces la tasa de iva
        # va en el campo 3 y el monto de perc. va en el campo 4. Pero si NO es T
        # entonces la cosa es al revez, cosa de locos
        if type == "T":
            field_3=Alic
            field_4=Amount
        else:
            field_3=Amount
            field_4=Alic
        #cmd = Command(chr(102), self.ffs(Text.ljust(20," ")), type, field_3)
        #DEL MANUAL LX300F
        #Detalle : Si se coloca en el Campo 02 el calificador “T” en el campo 03 debe ir la tasa y en el campo 04 el ·
        #monto, caso contrario en el Campo 03 ira el Monto y el Campo 04 no se informa.

        if (type=="T"):

            cmd = Command(chr(102), self.ffs(Text.ljust(25," ")), type, field_3, field_4)
        else:
            cmd = Command(chr(102), self.ffs(Text.ljust(25," ")), type, field_3)
        cmd.log(["cmd","descripcion","tipo","field_3","field_4"])
        #cmd = "%s%s%s%s%s%s%s%s%s" %(chr(102), S, self.ffs(Text.ljust(25," ")), S, type, S, field_3, S, field_4)
        self.Sent2FiscPrinter(str(cmd))

    def writeHeaders(self,list,Clearflag=False):
        i = 0
        for line in HEADERS.keys():
           if (HEADERS[line]):
               tmp = list[i][0:40]
               if Clearflag: tmp = DEL
               fLine = str(line).rjust(5,"0")
               cmd = "%s%s%s%s%s" %(chr(93),S,fLine,S,tmp)  #0x5dh
               self.Sent2FiscPrinter(cmd) # doesnt return anything
               i+=1
 
    def getAllStatusRequest(self):
        d = {}
        for type in STATUSTYPELIST:
            res = self.statusRequest(type)
            d[type]=res
        return d

    def getStatusTypeList(self):
        return StatusTypeList

    def getLastInvoiceNr(self,InvType):
        if InvType == 0:
            general = "A"
            type = "UltimaFactA"
        elif InvType >0 and InvType <3 :
            general = "A"
            type = "UltimaFactB"
        dic = self.statusRequest("C")
        pos = dic.get("PuntoDeVta","")
        nr  = dic.get(type,"")
        print ret
        return (str(pos) + str(nr))

