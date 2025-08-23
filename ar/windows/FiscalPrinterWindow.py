#encoding: utf-8
from OpenOrange import *
from MasterWindow import *
from FiscalPrinter import FiscalPrinter

ParentFiscalPrinterWindow = SuperClass("FiscalPrinterWindow","MasterWindow",__file__)
class FiscalPrinterWindow(ParentFiscalPrinterWindow):

   def fiscalClose(self,closeType):
        from GenericReport import GenericReport
        self.gr = GenericReport()
        self.gr.open(True)
        self.gr.startTable()
        self.gr.header("Cierre %s" % closeType)
        self.gr.endTable()
        self.gr.startTable()
        self.gr.header("Seteo","Valor")
        fp = self.getRecord()
        #if not fp.configureOpenPort():
        #    message("No se puede abrir el puerto de la Impresora Fiscal ")
        #    return
        answer = fp.dailyClose (closeType,True)
        for field in answer.keys():
           self.gr.row(field,answer.get(field,""))
        self.gr.endTable()
        self.gr.getView().resize(460,300)
        self.gr.render()


   def fiscalCloseX(self):
        self.fiscalClose("X")

      
   def fiscalCloseZ(self):
        self.fiscalClose("Z")


   def getFiscalStatus(self):
        fp = self.getRecord()
        if not fp.configureOpenPort():
          message("No se puede abrir el puerto de la Impresora Fiscal")
          return
        from GenericReport import GenericReport
        self.gr = GenericReport()
        self.gr.open(True)
        self.gr.startTable()
        self.gr.header("Estado Impresora Fiscal")
        self.gr.endTable()
        self.gr.startTable()
        answer = fp.statusRequest(None)         #returns a dictionary 
        types = answer.keys()
        for type in types:
            self.gr.header("Seteo "+ type,"Valor")
            fields = answer[type].keys()
            fields.sort()
            for field in fields:
                self.gr.row(field,answer[type].get(field,""))
        self.gr.endTable()
        self.gr.getView().resize(460,300)
        self.gr.render()


   def testNonFiscalDoc(self):
        fp = self.getRecord()
        fp.testNonFiscalDoc()

   def forwardPaper(self):
        fp = self.getRecord()
        if not fp.configureOpenPort():
          message("No se puede abrir el puerto de la Impresora Fiscal")
          return
        #fp.getFiscalandPrinterStatus("2600","0600")
        #return
        fp.forwardPaper()

   def getTimeDate(self):
        fp = self.getRecord()
        (d,t) = fp.getTimeDate()
        message("Fecha & Hora de la Impresora Fiscal son %s, %s" % (d,t))

   def setTimeDate(self):
        fp = self.getRecord()
        fp.setTimeDate()

   def getHeaderInfo(self):
        fp = self.getRecord()
        if not fp.configureOpenPort():
          message("No se puede abrir el puerto de la Impresora Fiscal ")
          return
        from GenericReport import GenericReport
        res = fp.getHeaders()
        if not res: return 
        self.gr = GenericReport()
        self.gr.open(True)
        self.gr.startTable()
        self.gr.header("Informacion de encabezado y pie")
        self.gr.endTable()
        self.gr.startTable()
        l=0
        for t in res:
            self.gr.row(l,t)
            l+=1
        self.gr.endTable()
        self.gr.getView().resize(460,300)
        self.gr.render() 


   def setHeaderInfo(self):
        fp = self.getRecord()
        if not fp.configureOpenPort():
          message("No se puede abrir el puerto de la Impresora Fiscal ")
        invNr = getInteger("Test on Invoice Nr:")
        from Invoice import Invoice
        inv = Invoice.bring(invNr)
        if not inv: return
        o = fp.createAppropriateObject()
        o.printHeaderTrailer(inv)
        o.clearHeaders()
        varspace = {}
        from Customer import Customer
        cust = Customer.bring(inv.CustCode)
        for fname in cust.fieldNames():
           varspace[fname] = cust.fields(fname).getValue()
        if (inv.OriginType == inv.Origin["Reservation"]) and (inv.OriginNr):
          from Reservation import Reservation
          res = Reservation.bring(inv.OriginNr)
          for fname in res.fieldNames():
             key= "Res"+fname
             varspace[key] = res.fields(fname).getValue()
          rooms = []
          for rrow in res.RoomRows:
             rooms.append(rrow.Room)
          varspace["ResRooms"] = ",".join(rooms)
        from User import User
        us = User.bring(inv.User)
        if us:
          varspace["UserName"] = us.Name
        hlist = []
        fields = ["Header1","Header2","Header3","Footer1","Footer2","Footer3","Footer4"]
        for field in fields:
            formula = fp.fields(field).getValue()
            try:
                res = eval(formula,varspace)
            except:
                res = ""
            hlist.append(res)
        o.writeHeaders(hlist)
