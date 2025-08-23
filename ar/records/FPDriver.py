#encoding: utf-8
from OpenOrange import *
from Comunication import *
from time import sleep
import string

class FPDriver:
    TRANSTABLE={"‚":97,"‰":97,"‡":97,"Â":97,"·":97,                    # a
              "Í":101,"Î":101,"Ë":101,"È":101,                         # e
              "Ô":105,"Ó":105,"Ï":105,"Ì":105,                         # i
              "Ù":111,"ˆ":111,"Ú":111,"Û":111,                         # o
              "˚":117,"˘":117,"˙":117,                                 # u
              "ƒ":65,"≈":65,                                           # A
              "…":69,                                                  # E
              "÷":79,                                                  # O
              "‹":85,                                                  # U
              "Ò":110,                                                 # Ò
              "—":78}
    InvoiceTypes = ["F","M","D","T"]  # fact, n cred, n deb, ticket-fact
    INSCRIPTION = ["I","F","R","E","R","M"]
    DocTypes = ["A","B","C"]
            
    
    #TODO: esta clase deberia heredar de FiscalPrinter, la cual contiene
    # datos necesarios de la configuracion de impresora necesaria a la
    # hora de imprimir documentos fiscales. Este DFPC es un parche, pero
    # tiene que ser eliminado de inmediato :-).
    # DFPC is Default Fiscal Printer Configuration
    def __init__(self,port,PacketNr,DFPC = None):
       self.port       = port
       self.PacketNr   = PacketNr
       self.ticketflag = False
       self.DFPC       = DFPC
       self.TestMode   = False
       self.logFile   = "FiscalPrinter.log"
       self.PrinterStatus = None
       self.FiscalStatus = None

    def getPrinterConfig (self):
        return self.DFPC

    def ffs(self,text):
        """Translates an spanish string into a standard english character string"""
        res = ""
        for x in text:
          if (ord(x)> 127):             # not in characters NO FUNCIONA con NC Epson !!!!
              res+= chr(self.TRANSTABLE.get(x,ord(" ")))
          else:
            res += x
        return res


    def getStatusString(self,hexStateString):
        bstr_pos = lambda n: n>0 and bstr_pos(n>>1)+str(n&1) or ''
        binstr = lambda n: n>0 and bstr_pos(n>>1)+str(n&1) or ''
        hex2binstr = lambda n: binstr(int(n,16))
        binstr = hex2binstr(hexStateString).rjust(16,"0")
        return binstr[::-1]              # return Backward for Hasar check if Epson behaves the same

    def checkSum(self,text):
        ordlist = map(ord,text)
        s1 = reduce(lambda x,y : x + y, ordlist)
        s2 = "%X" % s1
        return s2.rjust(4,"0")

    def checkSum2(self,intlist):
        s1 = reduce(lambda x,y : x + y, intlist)
        s2 = "%X" % s1
        return s2.rjust(4,"0")

    def incrementPacketNr(self):
        self.PacketNr += 2;
        if ((self.PacketNr<32) or (self.PacketNr>127)):    # 7FH
           self.PacketNr=32  # 20H

    def sentString(self,command):
        if self.PacketNr < 32: self.PacketNr = 32
        buffer = "%s%s%s%s"  % (STX,chr(self.PacketNr),command,ETX)
        buffer += self.checkSum(buffer)
        self.port.write(buffer)
        if self.epsonflag:
          log("Sending Command: %s with P(%s): %s" % (self.commandTable.get(command[1],ord(buffer[1])),self.PacketNr,self.prettyPacketPrint(buffer)) )
        else:
          log("Sending Command: %s with P(%s): %s" % (self.commandTable.get(command[0],ord(buffer[0])),self.PacketNr,self.prettyPacketPrint(buffer)) )
        sleep(0.1) #recommended timeout

    def sentACK(self):
        self.port.write(ACK)
        sleep(0.1)

    def getByteFromFiscalPrinter(self):
        while (True):
          if self.port.bytesWaiting() > 0:
             i = self.port.getByte()
             return chr(i)

    def Sent2FiscPrinter(self,command):
        """ Returns answer from fiscal printer in a list"""
        retries = 0
        timeout = 800
        self.sentString(command)
        if self.TestMode:
           return
        start = now()
        #mensaje de vuelta
        acksents = False
        while (True):
            b = self.getByteFromFiscalPrinter()
            if (b==STX):  # receiving start of data... now read rest
               s = b
               cs = ""; rec = [2]
               csflag = False
               while (True):
                  if (self.port.bytesWaiting()>0):
                    i = self.port.getByte()
                    if (i != None) and (i > 0) and (i < 227):
                      if csflag:
                        cs = cs + chr(i)
                        if len(cs)==4: break
                      else:
                        s = s + chr(i)
                        rec.append(i)
                      if (i == 3): csflag = True # ETX
                  delay = now() - start
                  millisecs = delay.seconds * 1000 + (delay.microseconds / 1000)
                  if (millisecs > timeout):
                    log("TimeOut")
                    return False
               log("Received: %s\n" % self.prettyPacketPrint(s))
               ds = self.checkSum2(rec)
               cs = cs.upper()  # en algunas impresoras/ sys operativos devuelven hex en minuscula !

               csStr = s[s.find(ETX):]
               log("=Found=>%s  total: %s" % (cs,int(cs,16)))
               log("=Calc=>%s   total: %s \n" % (ds,int(ds,16)))
               log(rec)

               if (ds<>cs): #bad checksum
                  self.port.write(NAK)
                  log("Uncorrect data received from Fiscal Printer, sending NAK")
               if (self.PacketNr <> ord(s[1])): #different secuence numbers
                  log("Non corresponding answer received from Fiscal Printer, resenting command. <spec: %i> <rec: %i>" % (self.PacketNr,ord(s[1])))
                  self.sentString(ACK) # cuando la impresora se queda esperando el ack !.
                  log("Enviando ack")
                  self.sentACK() # hasar
                  log("ack enviado")
                  acksents = True
                  start = now()
                  continue
               pars = string.split(s[4:-1],S)     # first 4 are not interesting
               self.sentACK() # hasar
               #el slicing sobre s quita tambien el ultimo caracter, esto porque cierta impresora epson (lx 300 +)
               #en ocaciones retorna mensajes con ausencia de un ultimo separador de campo (S) entre el delimitador
               #de fin de mensaje (0x03Comandos de control fiscal) y el resto del mensaje [MENSAJE<S>0X03]
               self.incrementPacketNr()

               self.PrinterStatus = self.getStatusString(pars[0])
               self.FiscalStatus = self.getStatusString(pars[1])
               log("              : 0123456789012345")
               log("Fiscal Status : %s" % self.FiscalStatus)
               log("Printer Status: %s" % self.PrinterStatus)
               return pars[2:]
            elif (b==DC2):
              timeout += 800
            elif (b==DC4):
              timeout += 800
            elif (b==NAK):            # resent string without incrementing packetnr
              log("Receiving NAK from Fiscal Printer, resenting command")
              retries += 1
              self.sentString(command)
              start = now()
            elif (b== ACK):timeout +=800 # hasar
            delay = now() - start
            millisecs = delay.seconds * 1000 + (delay.microseconds / 1000)
            if (millisecs > timeout) or (retries>3):
              if acksents: #hasar
                retries = 0
                timeout = 800
                self.sentString(command)
                start = now()
                continue
              log("TimeOut")
              return False
        return

    def printNonFiscalDoc(self,rows):
        self.openNonFiscalDoc()
        for row in rows:
            self.printNonFiscalText(row)
        self.closeNonFiscalDoc()

    def NotImplementedYet(self,detail):
        t = self.__class__.__name__
        # TODO: falta una manera mas linda de ver la marca desde self
        # TODO: tambiÈn seria bueno poder ver el modelo de la impresora tambien desde self
        if  t[2:7] == "Epson": vendor = "Epson"
        else: vendor = "Hasar"
        self.DFPC.appendMessage("Funcion TodavÌa no implementada en %s: %s." % (vendor,detail))

    # solo valido para etiquetadoras. retorna True si el documento a imprimir
    # debe ser ticket factura. Los casos puntuales son:
    # - si se debe imprimir nota de credito /debito
    # - el el tipo de documento es A.
    # - si el cliente es Responsable Inscripto o Monotributista.
    # - el monto total del documento alcanza o supera los $ 1000.
    # - si existe algun item cuyo precio con iva incluido supera los $ 1000.
    # - si esta configurado asi (y no se cumple ninguna de las anteriores).
    def forceTicketFactura(self, inv):
        if inv.InvoiceType in (1,2):
            return True
        if inv.DocType  == 0:
            return True
        if inv.TaxRegType in (0,5):
            return True
        if inv.Total >= 1000:
            return True
        if index(lambda item: item.VATPrice >=1000, inv.Items) != -1:
            return True
        return self.DFPC.ForceInvoiceTicket

    def prettyPacketPrint(self,recstr):
        packetnr = 0
        if len(recstr)>2: packetnr = ord(recstr[1])
        res = "Packet %s: " % packetnr
        for b in recstr:
          if b in ComTransTable.keys():
            res += "<%s>" % ComTransTable[b]
          else:
            res += b
        return res

    def dumpStatusDictonary(self,statusDic):
        answer = statusDic
        types = answer.keys()
        for type in types:
            log("Seteo "+ type)
            fields = answer[type].keys()
            fields.sort()
            for field in fields:
                log("%s: %s" % (field,answer[type].get(field,"")))

    # Para generar nros oficiales ya que los que salen directamente desde las
    # impresoras vienen con formatos como: 0000 - 00000000. La idea es que este
    # metodo retorne un numero como 'A-0000-00000000' y adem√°s que el metodo
    # acepte parametros de sernr en varios formatos: 000000000000,
    # 0000 00000000, A 0000 00000000, ...
    # targetSerNr es el nro retornado por la impresora
    # docType es el DocType que maneja el registro Invoice de OpenOrange
    # salesPoint es el punto de venta (este valor es ignorado si el nro ofi
    @classmethod
    def GetStandarizedSerNr(cObj,targetSerNr, docType, invType, salesPoint=None):
        if not docType in (0,1) or not targetSerNr :
            return None
        import re
        pattern = "(?P<tipo>([A,B])?)[ -]*(?P<ptoVenta>([0-9]{4})?)([ ]*-*[ ]*)?(?P<nr>[0-9]{8})"
        res = re.match(pattern, targetSerNr)
        try:
            tipo = res.group("tipo")
        except:
            tipo = None
        try:
            _salesPoint = res.group("ptoVenta")
        except:
            _salesPoint = salesPoint
        try:
            nr = res.group("nr")
        except:
            nr = targetSerNr.rjust(8,"0")
        if not tipo:
            if docType == 0:
                tipo='A'
            elif docType == 1:
                tipo='B'
        #no invoicetype indications        
        #if invType == 1:
        #    tipo="NC" +tipo
        #elif invType ==2:
        #    tipo="ND" +tipo
        if salesPoint:
            salesPoint = utf8(salesPoint).rjust(4,'0')
        if _salesPoint:
            salesPoint=_salesPoint
        if not tipo or not salesPoint or not nr:
            return None
        return "%s-%s-%s" %(str(tipo),str(salesPoint),str(nr))


    def log(self, text):
        f = file(self.logFile, "a+")
        if (f):
            line ="%s: %s\n"%(str(now()),text)
            f.write(line)
            f.flush()
            f.close()

class Command:
    """ Para ayudar con la creacion de comandos de medio nivel """
    def __init__(self,*fields):
        self.data = []
        for f in fields:
            if f != S: self.data.append(str(f))

    def __str__(self):
        return S.join(self.data)

    def appendField(self,field):
        if field != S:
            self.data.append(str(field))

    def simpleLog(self):
        for i in range(0,len(self.data)):
            print "data %i: %s" % (i,self.data[i])

    def log(self,names= None):
        if names is None:
            return self.simpleLog ()
        for i in range(0,len(self.data)):
            try:
                name = names[i]
                value = self.data[i]
                print "field %s: %s" % (name,value)
            except:
                print "error on command log"

