#encoding: utf-8
from OpenOrange import *
from time import sleep
from FPEpson import FPEpson
from FPEpsonTicket import FPEpsonTicket
from FPEpsonTicketTMU220AF import FPEpsonTicketTMU220AF
from FPHasar import FPHasar

HASAR_SMH_P_320F    =0
HASAR_PL_8F         =1
HASAR_615F_PR4F     =2
EPSON_LX_300F       =3
EPSON_TM_2000AF     =4
EPSON_TM_2002AF     =5
HASAR_SMH_P_330F    =6
EPSON_TM_U220AF     =7
HASAR_SMH_P_715F    =8
OLIVETTI_ARJET_20F  =9

ISEPSON     = [0 ,0 ,0 ,1 ,1 ,1 ,0 ,0 ,0, 0]
ISTICKET    = [0 ,0 ,1 ,0 ,1 ,1 ,0 ,1 ,1, 0]         # check !!!
PAPERCUTTER = [0 ,0 ,1 ,0 ,0 ,0 ,0 ,0 ,1, 0]         # check !!!
MAXDESC     = [40,40,20,50,30,30,40,40,20,40]        # descripcion maxima en una linea de articulos
MAXDESCCUSTOMER     = [40,40,40,50,30,30,40,40,30,40]        # descripcion maxima en una linea de clientes
GETCAI      = [0 ,0 ,0 ,0 ,0 ,0 ,1 ,0 ,0, 0]        # Solo para la hasar SMH/P 330F SMH/P-9F - version 2 de modelos SMH/P-8F y SMH/P-322F

ParentFiscalPrinter = SuperClass("FiscalPrinter","Master",__file__)
class FiscalPrinter(ParentFiscalPrinter):

    buffer = RecordBuffer("FiscalPrinter", RecordBuffer.defaulttimeout, True) #remember nones = True para que no este todo el tiempo tratando de traer impresoras que no existen
    port = None

    def afterLoad(self):
        self.port = None
        # lenght of lines depends on the model of the printer
        self.maxStr         = MAXDESC[self.PrinterModel]
        self.maxStrCustomer = MAXDESCCUSTOMER[self.PrinterModel]
        self.caiflag        = GETCAI[self.PrinterModel]
        self.ticketflag     = bool(ISTICKET[self.PrinterModel])
        self.epsonflag      = bool(ISEPSON[self.PrinterModel])
        self.PaperCutterf   = PAPERCUTTER[self.PrinterModel]
        self.logFile        = "FiscalPrinter.log"
        return True

    def check(self):
        res = ParentFiscalPrinter.check(self)
        if (not res):
            return res
        if (not self.PointOfSales):
            return self.NONBLANKERR("PointOfSales")
        return True
        
    def configureOpenPort(self):
        portname = self.UnixPort
        if not portname: portname = self.WinPort
        self.port = ComPort(portname)
        self.port.setDtr(False)
        self.port.setRts(False)
        self.port.setParity(0)
        self.port.setBaudRate(self.BaudRate)
        self.port.setStopBits(1)
        self.port.setDataBits(8)
        self.port.setTimeout(100)
        of = self.port.open()
        if not of:                         # if port is open close it first
          self.port.close()
          of = self.port.open()
        return of

    def hasHeader(self):
        return (self.Header1 or self.Header2 or self.Header3 or self.Footer1 or self.Footer2 or self.Footer3 or self.Footer4)

    def createAppropriateObject(self,Code = None):
        """ print invoice """
        classes = ["FPHasar","FPHasar","FPHasar",
                   "FPEpson",
                   "FPEpsonTicket",
                   #ANTE TENIA EPSONTICKET PERO NO FUNCIONABA, FUNCIONA COMO LA TMU
                   "FPEpsonTicketTMU220AF",
                   "FPHasar","FPEpsonTicketTMU220AF",
                   "FPHasar","FPHasar"]
        objname = classes[self.PrinterModel]
        if Code:
            DFPC = FiscalPrinter()
            DFPC.Code = Code
            if DFPC.load():
                cmd = "o = %s(self.port,self.PacketNr,DFPC)" % objname
        else:
            cmd = "o = %s(self.port,self.PacketNr)" % objname
        exec(cmd)
        o.PrinterModel = self.PrinterModel
        o.ticketflag   = self.ticketflag
        o.PaperCutterf = self.PaperCutterf
        o.caiflag      = self.caiflag
        o.maxStr       = self.maxStr
        o.maxStrCustomer       = self.maxStrCustomer
        o.hasHeader    = self.hasHeader()
        o.epsonflag    = self.epsonflag
        if self.UnixPort=="Test":
            o.TestMode=True
        return o

    def printInvoice(self,inv):
        """ print invoice """
        # TODO List:
        # Controlar Notas de Credito / Nota de debito
        # Parse Header Footer lines
        # Anticipos / Impuestos internos / Percepciones
        # Items con Despatchos / Nro de serie
        # Manejo de Descuentos, Multimoneda
        # Test all models
        # Mensajes de error
        # El siguiente chequeo evita que se envien montos invalidos a la 
        # impresora. Esto se quiere si por ejemplo se emite un comprante a un
        # consumidor final, sin registrar datos de cliente (CUIT=0).
        # NOTA: Si el monto maximo a imprimir
        # es $ 1000, entonces no puede ir a la impresora ningún item con Price
        # e IVA superando dicho monto, si ocurre entonces la impresora se bloquea!.
        if self.DennyAmountToCustomer and inv.CustCode == self.DennyCustCode:
            denny=False
            if inv.Total >= self.DennyAmount:
                denny=True
            # igualmente es posible que alguna de las lineas de item tenga un total
            # SIN aplicar descuentos mayor que DennyAmount, por lo que chequeo
            # que no se envie a la impresora, si ocurre esto la impresora se bloquea
            # sin dar tiempo a aplicar los descuentos posteriores si los hubiera
            if not denny:
                for item in inv.Items:
                    # no quiero aplicar descuentos porcentuales, porque sería erroneo
                    if item.Qty*item.VATPrice >= self.DennyAmount:
                        denny=True
                        break
            if denny:
                msg ="No puede Imprimir un monto mayor que "+str(self.DennyAmount)
                msg+= " para el cliente " + self.DennyCustCode 
                self.appendMessage(msg)
                return None
        if (self.UnixPort<>"Test"):
          if not self.configureOpenPort():
            self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
            self.port.close()
            return
        o = self.createAppropriateObject(self.Code)
        #ABRIR CAJON DE DINERO
        if (self.OpenDrawer):
            o.OpenDrawer()
        officialNr = o.printInvoice(inv)
        if officialNr:
            if self.StandarizeOfficialNumbers:
                officialNr = o.GetStandarizedSerNr(officialNr, inv.DocType, inv.InvoiceType, self.PointOfSales)
            else:
                officialNr = str(self.PointOfSales) + " - " + officialNr
        if (self.UnixPort<>"Test"):
          self.port.close()
        self.PacketNr = self.getPacketNr()
        self.save() #hay que guardar el último PacketNr en la bd
        self.logInvoice(inv,officialNr )
        return officialNr


    def logInvoice(self, inv, officialNr):
        from Invoice import Invoice
        import codecs
        f = codecs.open(self.logFile, "a+", "utf8")
        if (f):
            line =u"%s: officialNr: %s -- SerNr: %s -- internalId: %s -- custCode: %s\n"%(utf8(now()), utf8(officialNr), utf8(inv.SerNr), utf8(inv.internalId), utf8(inv.CustCode))
            f.write(line)
            f.flush()
            try:
                inv.exportRecord(f)
            except Exception, e:
                f.write("Ocurrio un error al exportar el registro: %s \n"%utf8(e))
            f.close()

    def printDelivery(self,deliv):
        if (self.UnixPort<>"Test"):
          if not self.configureOpenPort():
            self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
            self.port.close()
            return
        o = self.createAppropriateObject(self.Code)
        #ABRIR CAJON DE DINERO
        if (self.OpenDrawer):
            o.OpenDrawer()
        officialNr = o.printDelivery(deliv)
        officialNr = str(self.PointOfSales) + " - " + officialNr
        if (self.UnixPort<>"Test"):
          self.port.close()
        self.PacketNr = self.getPacketNr()
        self.store() #hay que guardar el último PacketNr en la bd
        return officialNr

    def getTimeDate(self):
        self.appendMessage("rev 11:37")
        sysprint("FiscalPrinter.getTimeDate ():1")
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        sysprint("FiscalPrinter.getTimeDate ():2")
        o = self.createAppropriateObject()
        sysprint("FiscalPrinter.getTimeDate ():3")
        pnr = o.getTimeDate()
        sysprint("FiscalPrinter.getTimeDate ():4")
        self.port.close()
        sysprint("FiscalPrinter.getTimeDate ():5")
        return pnr

    def setTimeDate(self):
        sysprint("FiscalPrinter.setTimeDate ():1")
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        sysprint("FiscalPrinter.setTimeDate ():2")
        o = self.createAppropriateObject()
        sysprint("FiscalPrinter.setTimeDate ():3")
        try:
            o.SetDateTime()
        except:
           self.appendMessage("Comando no implementado para este modelo")
        sysprint("FiscalPrinter.setTimeDate ():4")
        self.port.close()
        sysprint("FiscalPrinter.setTimeDate ():5")


    def dailyClose(self,Type,Printflag):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        dic = o.dailyClose(Type,Printflag)
        self.port.close()
        return dic

    def cancelFiscalInvoice(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        dic = o.cancelFiscal()
        self.port.close()

    def getHeaders(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        list = o.getHeaders()
        self.port.close()
        return list

    def testNonFiscalDoc(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        o.printNonFiscalDoc(["Hola","Mundo"])
        self.port.close()
        return list

    def writeHeaders(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        list=[]
        for fn in ["Header1","Header2","Header3","Footer1","Footer2","Footer3","Footer4"]:
            tmp = self.fields(fn).getValue()[0:40]
            list.append(tmp)
        pnr = o.writeHeaders(list)
        self.port.close()
        self.PacketNr = pnr
        self.save() #hay que guardar el último PacketNr en la bd

    def PrintNonFiscalInvoice(self):
        from LocalSettings import LocalSettings
        fp = FiscalPrinter()
        ls = LocalSettings.bring()
        fp.Code = ls.Computer
        if not fp.load(): return False
        if fp.configureOpenPort():
            if ( not fp.epsonflag):
                fp.HasarOpenNonFiscalReceipt()
                for item in self.Items:
                  if (item.ArtCode):
                    line = item.Name[:40]+"......%.2f" % item.RowTotal
                    fp.HasarPrintNonFiscalText(line)
                total="Total........................%.2f" % self.Total
                fp.HasarPrintNonFiscalText(total)
                fp.HasarCloseNonFiscalReceipt()
            else:
                pass
        else: 
            self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")

    def forwardPaper(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        pnr = o.forwardPaper()
        self.port.close()

    def statusRequest(self,type):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        stat= o.statusRequest(type)
        self.port.close()
        return stat

    def getStatusTypeList(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        tl= o.statusRequest(type)
        self.port.close()
        return tl

    def getAllStatusRequest(self):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject()
        tl= o.getAllStatusRequest()
        self.port.close()
        return tl

    def printBarTab(self,barTab,**kwargs):
        if not self.configureOpenPort():
           self.appendMessage("No se puede abrir el puerto de la Impresora Fiscal")
           return
        o = self.createAppropriateObject(self.Code)
        #ABRIR CAJON DE DINERO
        if (self.OpenDrawer):
            o.OpenDrawer()
        officialNr = o.printBarTab(barTab,**kwargs)
        if officialNr:
            officialNr = str(self.PointOfSales) + " - " + officialNr
        self.port.close()
        return officialNr

    def getPacketNr(self):
        try:
            return o.PacketNr
        except NameError,AttributeError:
            return 1
