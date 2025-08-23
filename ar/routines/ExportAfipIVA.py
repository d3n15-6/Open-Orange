#encoding: utf-8
from Routine import Routine
from OurSettings import OurSettings
from TaxSettings import TaxSettings
from OpenOrange import *
from Retencion import Retencion

Resoluciones = ["234","",""]
filename = ["AfipIVARet.txt","AfipIVAPer.txt"]
RetencionAgropecuaria = [785, 786, 787, 794, 795,796] #Sacadas de la pagina afip

class ExportAfipIVA(Routine):
    def run(self):
        record = self.getRecord()
        if (record.Option == 0 ): #RETENCION
            RQuery = Query()
            RQuery.sql  = "SELECT 'Receipt' as RecordType,Ret.TaxOfficeCode as Regime, RPMr.PayMode as PayMode, C.TaxRegNr as CUIT, R.TransDate as TransDate, \n"
            RQuery.sql += "RPMr.ChequeNr RetDocNr, RPMr.Amount as Amount \n"
            RQuery.sql += "FROM ReceiptPayModeRow RPMr \n"
            RQuery.sql += "INNER JOIN Receipt R ON (RPMr.masterId = R.internalId) \n"
            RQuery.sql += "INNER JOIN Customer C ON R.CustCode = C.Code \n" 
            RQuery.sql += "INNER JOIN PayMode PM ON RPMr.PayMode = PM.Code \n"
            RQuery.sql += "INNER JOIN Retencion Ret ON PM.RetCode = Ret.Code \n"
            RQuery.sql += "WHERE?AND PM.PayType = i|9| \n" # 9 = Tipo Cobro Rentencion
            RQuery.sql += "WHERE?AND Ret.Type = 0 AND Ret.RetType = i|2| \n" # 2 = Retencion Tipo IVA
            RQuery.sql += "WHERE?AND R.Status = i|1| \n"
            RQuery.sql += "WHERE?AND ( R.Invalid = i|0| OR R.Invalid IS NULL ) \n"
            if (record.FromDate and record.ToDate):
                RQuery.sql += "WHERE?AND R.TransDate BETWEEN d|%s| AND d|%s|  " %(record.FromDate, record.ToDate)

            IQuery = Query()
            IQuery.sql  = "SELECT 'Invoice' as RecordType,Ret.TaxOfficeCode as Regime, IPMr.PayMode as PayMode, C.TaxRegNr as CUIT, I.TransDate as TransDate, \n"
            IQuery.sql += "IPMr.ChequeNr as RetDocNr, IPMr.Paid as Amount \n"
            IQuery.sql += "FROM InvoicePayModeRow IPMr \n"
            IQuery.sql += "INNER JOIN Invoice I ON (IPMr.masterId = I.internalId ) \n"
            IQuery.sql += "INNER JOIN Customer C ON I.CustCode = C.Code \n"
            IQuery.sql += "INNER JOIN PayMode PM ON IPMr.PayMode = PM.Code \n"
            IQuery.sql += "INNER JOIN Retencion Ret ON PM.RetCode = Ret.Code \n"
            IQuery.sql += "WHERE?AND PM.PayType = i|9| \n" # 9 = Tipo Cobro Rentencion
            IQuery.sql += "WHERE?AND Ret.Type = 0 AND Ret.RetType = i|2| \n" # 2 = Retencion Tipo IVA
            IQuery.sql += "WHERE?AND I.Status = i|1| \n"
            IQuery.sql += "WHERE?AND (I.{Internalflag} = 0 OR I.{Internalflag} IS NULL) "
            IQuery.sql += "WHERE?AND ( I.Invalid = i|0| OR I.Invalid IS NULL ) \n"
            if (record.FromDate and record.ToDate):
                IQuery.sql += "WHERE?AND I.TransDate BETWEEN d|%s| AND d|%s| \n" %(record.FromDate, record.ToDate)

            from TaxSettings import TaxSettings
            tset = TaxSettings.bring()
            if (tset):
                TaxOfficeRetencionCode = tset.TaxOfficeRetencionCode
                VATRetencAccount = []
                VATRetencAccount = tset.RetenIVA.split(",")
            else:
                TaxOfficeRetencionCode = "000"
                VATRetencAccount = "000"

            PQuery = Query()
            PQuery.sql  = "SELECT 'PurchaseInvoice' as RecordType,'%s' as Regime, PIr.Account as PayMode, S.TaxRegNr as CUIT, P.TransDate as TransDate, \n" %(TaxOfficeRetencionCode)
            PQuery.sql += "P.InvoiceNr as RetDocNr, PIr.RowTotal as Amount \n"
            PQuery.sql += "FROM PurchaseInvoiceRow PIr \n"
            PQuery.sql += "INNER JOIN PurchaseInvoice P ON (PIr.masterId = P.internalId) \n"
            PQuery.sql += "INNER JOIN Supplier S ON S.Code = P.SupCode \n"
            PQuery.sql += "WHERE?AND PIr.Account IN ('%s')  \n" % ("','".join(VATRetencAccount))
            PQuery.sql += "WHERE?AND P.Status = i|1| "
            PQuery.sql += "WHERE?AND (P.{Internalflag} = 0 OR P.{Internalflag} IS NULL) "
            PQuery.sql += "WHERE?AND ( P.Invalid = i|0| OR P.Invalid IS NULL ) \n"
            PQuery.sql += "WHERE?AND P.TransDate BETWEEN d|%s| AND d|%s| \n" %(record.FromDate, record.ToDate)
            
            BigQuery      = Query()
            BigQuery.sql  = "SELECT T1.RecordType, T1.Regime, T1.PayMode, T1.CUIT, T1.TransDate, T1.RetDocNr, T1.Amount "
            BigQuery.sql += "FROM (%s UNION ALL %s UNION ALL %s) AS T1 " %(RQuery.sql,IQuery.sql,PQuery.sql)
            BigQuery.sql += "ORDER BY T1.TransDate, T1.CUIT "
            #TODO: Control Info
            if (BigQuery.open()):
                fname = getSaveFileName("Please choose filename", DefaultFileName= filename[record.Option])
                if (fname):
                    efile = open(fname,"wb")
                    if (efile):
                        for rline in BigQuery:
                            efile.writelines(rline.Regime.ljust(3,"0"))
                            efile.writelines(rline.CUIT.ljust(13,"0"))
                            efile.writelines(rline.TransDate.strftime("%d/%m/%Y"))
                            if (rline.RecordType !=  "Receipt"):
                                tmp = str(self.getOperationCodeforRetencion(rline.RetDocNr,rline.Regime.ljust(3,"0")))
                                alert(tmp)
                                efile.writelines(tmp)
                            else:
                                efile.writelines(rline.RetDocNr.rjust(16,"0"))
                            efile.writelines(str("%.2f" %rline.Amount).rjust(16,"0"))
                            efile.writelines("\r\n")
                        efile.close()
                else:
                    return False
            message(tr("Export finished"))
        elif (record.Option == 1): #PERCEPCION
            VATPerceptionAccount = self.getRegPercep()
            if (not VATPerceptionAccount):
                message ("No hay percepciones de tipo IVA con Cuenta y Regimen seteados. \n No se hará la exportación")
                return
            PQuery = Query()
            PQuery.sql  = "SELECT PIr.Account, S.TaxRegNr as CUIT, P.TransDate as TransDate, \n" 
            PQuery.sql += "P.InvoiceNr as DocNr, PIr.RowTotal as Amount \n"
            PQuery.sql += "FROM PurchaseInvoiceRow PIr \n"
            PQuery.sql += "INNER JOIN PurchaseInvoice P ON (PIr.masterId = P.internalId) \n" 
            PQuery.sql += "INNER JOIN Supplier S ON (S.Code = P.SupCode) \n"
            PQuery.sql += "WHERE?AND P.TransDate BETWEEN d|%s| AND d|%s|  " %(record.FromDate, record.ToDate)
            PQuery.sql += "WHERE?AND ( P.Invalid = i|0| OR P.Invalid IS NULL ) \n"
            PQuery.sql += "WHERE?AND PIr.Account IN ('%s')  \n" % ("','".join(VATPerceptionAccount.keys()))
            PQuery.sql += "WHERE?AND P.Status = i|1| "
            PQuery.sql += "WHERE?AND (P.{Internalflag} = 0 OR P.{Internalflag} IS NULL) "

            
            if (PQuery.open()):
                fname = getSaveFileName("Please choose filename", DefaultFileName= filename[record.Option])
                if (fname):
                    efile = open(fname,"wb")
                    if (efile):
                        total = 0
                        ncTotal = 0
                        head  = "Siap-IVA Percepcion \n"
                        head +=  "Facturas a Proveedores desde %s " %(record.FromDate.strftime("%d/%m/%Y"))
                        head += " hasta %s \n" %(record.ToDate.strftime("%d/%m/%Y"))
                        head += "....v...10....v...20....v...30....v...40....v...50....v...\n"
                        if (record.ControlInfo):
                            efile.write(head)
                        for rline in PQuery:
                            if (rline.Amount>0):
                                efile.write(VATPerceptionAccount[rline.Account][:3])
                                efile.write(rline.CUIT.ljust(13,"0"))
                                efile.write(rline.TransDate.strftime("%d/%m/%Y"))
                                InvoiceNr = "%s%s" %(str(rline.DocNr)[2:6].rjust(8,"0"),str(rline.DocNr)[7:15].rjust(8,"0"))
                                efile.write(InvoiceNr)
                                efile.write(str("%.2f" %rline.Amount).rjust(16,"0"))
                                efile.write("\r\n")
                                total += rline.Amount
                            else:
                                ncTotal += rline.Amount
                        footer = "Total Siap - IVA Percepciones en Facturas de Compra:  %.2f \n" % (total)
                        footer += "Total Siap - IVA Percepciones en Notas de Credito : %.2f " % (ncTotal)
                        footer += "(No consideradas en la exportacion) "
                        if (record.ControlInfo):
                            efile.write(footer)
                        efile.close()
                else:
                    return False
            message(tr("Export finished"))

    def getRegPercep(self):
        query = Query()
        query.sql  = "SELECT r.Account, r.RetenReg "
        query.sql += "FROM Retencion r "
        #TIPO: PERCEPCION - IMPUESTO: IVA
        query.sql += "WHERE?AND r.Type = i|1| and r.RetType = i|2| \n"
        query.sql += "GROUP BY r.Account \n"
        reten = {}
        if (query.open()):
            for rec  in query:
                if (rec.Account and rec.RetenReg):
                    reten[rec.Account] = rec.RetenReg.rjust(3, "0")
        return reten

#TODO: crear tabla en Open que resuelva este problema
    def getOperationCodeforRetencion(self, docNr, retenCode):
        if (int(retenCode) in RetencionAgropecuaria):
            return "0000120122222222" #hardcode horrible (de la pagina de AFIP)
        else:
            tempString = "%s%s" %(docNr[2:6].rjust(8,"0"),docNr[7:15].rjust(8,"0"))
        return tempString