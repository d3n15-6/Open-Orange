#encoding: utf-8
from OurSettings import OurSettings
from TaxSettings import TaxSettings
from OpenOrange import *
from Routine import Routine
import string

fileN = ["AfipGanRet","AfipGanPer"]

class ExportAfipGan(Routine):

    def run(self):
        specs = self.getRecord()
        specs.Option = 0
        if (specs.Option==0):
          self.doRetencion()
        elif (specs.Option==1):
          self.doPercepcion()

    def getAfipCodigoComprobante(self,record):
        if record.__class__.name=="Invoice":
          if record.InvoiceType==0: return "=01"
          if record.InvoiceType==1: return "=03"
          if record.InvoiceType==2: return "=04"
        elif record.__class__.name=="Receipt":
          return "02"
        elif record.__class__.name=="Payment":
          return "06"

    def getGanRetencionPayMode(self,PercepGan):
        pm = Query()
        pm.sql  = "SELECT {Code} "
        pm.sql += "FROM [PayMode] "
        pm.sql += "WHERE?AND [Account] = s|%s| \n" % PercepGan
        if (pm.open()):
           return pm[0].Code

    def doPercepcion(self):
        specs = self.getRecord()
        fname = fileN[specs.Option] + ".txt"
        f = file(fname, "w")
        query = Query()
        query.sql  = "SELECT p.{SupCode},p.{TaxRegNr},pir.{InvoiceNr},p.{TransDate}, ppmr.{Amount}, "
        query.sql += "{TaxRegNr},{Total} "
        query.sql += "FROM [PurchaseInvoice] p \n"
        query.sql += "INNER JOIN [PurchaseInvoiceRow] pir ON p.internalId = pir.masterId \n"
        query.sql += "WHERE?AND pir.[Account] = s|%s| \n" % t.PercepIVA
        query.sql += "WHERE?AND p.{TransDate} BETWEEN d|%s| AND d|%s| " % (specs.StartDate,specs.EndDate)
        query.sql += "WHERE?AND (p.{Invalid}<>i|1| OR p.{Invalid} IS NULL)\n"
        query.sql += "WHERE?AND (p.{Status} = i|1| )\n"
        query.sql += "WHERE?AND (p.{Internalflag} = 0 OR p.{Internalflag} IS NULL) "
        query.sql += "ORDER BY p.{TransDate} \n"
        if (query.open()):
          for pay in query:
              regimen = Resoluciones[0]
              Base  = 0
              Total = 0
              f.write(self.SiapLine(True,regimen,pay.TaxRegNr,pay.TransDate,pay.SerNr,pay.Retencion,Base,Total,t.TaxRegNr,os.Name,InvoiceNr,pay.InvoiceType,pay.Total))
        f.close()

    def doRetencion(self):
        specs = self.getRecord()
        from TaxSettings import TaxSettings
        ts = TaxSettings()
        ts.load()
        from OurSettings import OurSettings
        os = OurSettings.bring()
        from Retencion import Retencion
        retpm = Retencion.getPayModes(0)
        fname = fileN[specs.Option] + ".txt"
        filename = getSaveFileName("Please choose filename", DefaultFileName=fname)
        f = file(filename, "w")
        query = Query()
        query.sql  = "SELECT rd.{SupCode},rd.{PaymentNr},rd.{TransDate}, rd.{Amount} as Retencion, "
        query.sql += "s.{TaxRegNr},p.{PayTotal}, rd.{DocNr} as DocNr, r.{RetenReg},rd.[RetType] "
        query.sql += "FROM [RetencionDoc] rd \n"
        query.sql += "INNER JOIN [Payment] p ON rd.{PaymentNr}= p.{SerNr} \n"
        query.sql += "INNER JOIN [Supplier] s ON rd.{SupCode} = s.{Code} \n"
        query.sql += "INNER JOIN [Retencion] r ON r.Code = rd.RetCode\n"
        query.sql += "WHERE?AND rd.[RetType] in (0,2) \n" #% string.join(map(lambda x: "s|%s|" % x, retpm),",")
        query.sql += "WHERE?AND rd.{TransDate} BETWEEN d|%s| AND d|%s| " % (specs.StartDate,specs.EndDate)
        query.sql += "WHERE?AND p.Status = i|1| \n"
        #query.sql += "WHERE?AND (p.{Internalflag} = 0 OR p.{Internalflag} IS NULL) " #Internalflag es un campo de las facturas de compra.
        query.sql += "WHERE?AND (p.Invalid = i|0|  OR p.Invalid IS NULL ) \n"
        query.sql += "ORDER BY rd.{TransDate} \n"
        total = 0.0
        head  = "SICORE - Retenciones IVA-GAN desde %s" %(specs.StartDate.strftime("%d/%m/%Y"))
        head += " hasta %s \n" %(specs.EndDate.strftime("%d/%m/%Y"))
        head += "....v...10....v...20....v...30....v...40....v...50....v...60....v...70....v...80....v...90....v..100....v..110....v..120....v..130....v..140\n"
        if (specs.ControlInfo):
            f.write(head.encode("latin1"))
        if (query.open()):
            for p in query:
              InvoiceNr = ""
              total += p.Retencion
              f.write(self.AfipLine(False,"06",p.TaxRegNr,p.TransDate,p.PaymentNr,p.Retencion,p.PayTotal - p.Retencion,p.PayTotal,ts.TaxRegNr,os.Name,p.DocNr,InvoiceNr,p.RetenReg,p.RetType))
        footer = "Total = %.2f " % total
        if (specs.ControlInfo):
            f.write((footer + "\n").encode("latin1"))
        f.close()
        message('Exportation done')


    def formatFloat(self,valor,align):
       tmp = "%.2f" % valor               # tmp is needed otherwise it doesnt allign !!
       tmp = tmp.replace(".",",")
       return tmp.rjust(align,"0")

    def AfipLine(self,Percepcionf,CompType,TaxRegNr,TransDate,PaymentNr,Retencion,Taxable,PayTotal,OwnTaxRegNr,OwnName,RetDocNr,InvoiceNr,RetReg,RetType):
        Line  = CompType # Código de comprobante [1:2] 2
        Line += TransDate.strftime("%d/%m/%Y") # Fecha de emisión del comprobante (DD/MM/YYYY) [3:12] 10
        Line += str(PaymentNr).rjust(16,"0") # Número del comprobante [13:28] 16 
        Line += self.formatFloat(PayTotal,16) # Importe del comprobante [29:44]  16
        TaxCode = "217"                         # imp ganancias
        if RetType == 2:
            TaxCode = "767"                         # imp IVA
        Line += str(TaxCode).rjust(3,"0") # Código Impuesto [45:47] 3
        Line += str(RetReg).rjust(3,"0") # Código Régimen [48:50] 3
        if (Percepcionf):
            OpCode = "2"
        else:
            OpCode = "1"
        Line += str(OpCode) # Código Operación [51:51] 1
        Line += self.formatFloat(Taxable,14) # Base de cálculo [52:65] 14
        Line += TransDate.strftime("%d/%m/%Y") # Fecha de emisión del boletín [66:75] 10
        Line += "01"  # Código de condición [76:77] 2
        Line += "0" #  Retención practicada a sujetos suspendidos según: [78:78] 1
        Line += self.formatFloat(Retencion,14) # Importe de la retención [79:92] 14 
        Exclusion = 0.00                               # se puede adaptar mas adelante
        Line += self.formatFloat(Exclusion,6) # Porcentaje de exclusión [93:98] 6
        Line += "          " # Fecha emisión del boletín [99:108] 10
        Line += "80"  # Tipo de documento del retenido [109:110] 2 (80=CUIT)
        cuit = filter(lambda x: x.isdigit(),TaxRegNr) 
        Line += cuit.rjust(20, " ") # Número de documento del retenido [111:130] 20
        Line += str(RetDocNr).rjust(14,"0") # Número certificado original [131:144] 14
        Line += "".rjust(30, " ") # Denominación del ordenante [145:174] 30
        Line += "".rjust(1, " ") # Acrecentamiento [175:175] 1
        Line += "".rjust(11, " ") # Cuit del país retenido [176:186] 11
        Line += "".rjust(11, " ") # Cuit del ordenante [187:197] 11
        return (Line + "\n").encode("latin1")