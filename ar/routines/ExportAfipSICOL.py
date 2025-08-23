#encoding: utf-8
from Routine import Routine
from OurSettings import OurSettings
from TaxSettings import TaxSettings
from OpenOrange import *
from CredCardType import CredCardType
from FinAccount import FinAccount


class ExportAfipSICOL(Routine):

    def run(self):
        record = self.getRecord()
        if (record.Option == 0):
            RQuery  = Query()
            RQuery.sql  = "SELECT C.TaxRegNr CUIT, R.TransDate TransDate, RPMr.ChequeNr RetDocNr, "
            RQuery.sql += "RIr.InvoiceNr DocNr ,RPMr.Amount Amount, RIr.InvoiceAmount Base "
            RQuery.sql += "FROM ReceiptPayModeRow RPMr "
            RQuery.sql += "INNER JOIN Receipt R ON RPMr.masterId = R.internalId AND R.Status = i|1| "
            RQuery.sql += "INNER JOIN Customer C ON R.CustCode = C.Code "
            RQuery.sql += "LEFT JOIN ReceiptInvoiceRow RIr ON RIr.masterId = R.internalId AND RIr.rownr = i|0| "
            RQuery.sql += "INNER JOIN PayMode PM ON (RPMr.PayMode = PM.Code AND PM.PayType = i|9|) " #9 = Formas de Cobro Retenciones
            RQuery.sql += "INNER JOIN Retencion Ret ON (PM.RetCode = Ret.Code AND Ret.Type = i|0| AND Ret.RetType = i|1|) " #0 = Retenciones de IIBB
            RQuery.sql += "WHERE (R.{Invalid}<>i|1| OR R.{Invalid} IS NULL) \n"
            RQuery.sql += "AND (R.{Status} = i|1|) \n"
            if (record.FromDate and record.ToDate):
                RQuery.sql += "AND R.TransDate BETWEEN d|%s| AND d|%s| " %(record.FromDate,record.ToDate)
            
            IQuery = Query()
            IQuery.sql  = "SELECT S.TaxRegNr CUIT,PI.TransDate TransDate,RIGHT(PI.InvoiceNr,8) RetDocNr, " #toma los ultimos 8 numeros de la factura como numero generador del comprobante
            IQuery.sql += "PI.InvoiceNr DocNr, PIr.RowTotal Amount, PI.Total Base "
            IQuery.sql += "FROM PurchaseInvoiceRow PIr "
            IQuery.sql += "INNER JOIN PurchaseInvoice PI ON (PIr.masterId = PI.internalId AND PI.Status = i|1|) "
            IQuery.sql += "INNER JOIN Supplier S ON PI.SupCode = S.Code "
            IQuery.sql += "INNER JOIN Province Prov ON Prov.IngBrutRetAcc = PIr.Account "
            IQuery.sql += "WHERE?AND (PI.{Invalid}<>i|1| OR PI.{Invalid} IS NULL) \n"
            IQuery.sql += "AND (PI.{Status} = i|1|) \n"
            IQuery.sql += "WHERE?AND (PI.{Internalflag} = 0 OR PI.{Internalflag} IS NULL) "
            if (record.FromDate and record.ToDate):
                IQuery.sql += "AND PI.TransDate BETWEEN d|%s| AND d|%s| " %(record.FromDate,record.ToDate)

            BigQuery = Query()
            BigQuery.sql  = "SELECT T1.CUIT, T1.TransDate, T1.RetDocNr, T1.DocNr, T1.Amount, T1.Base "
            BigQuery.sql += "FROM (%s UNION ALL %s ) AS T1 " %(RQuery.sql,IQuery.sql)
            BigQuery.sql += "ORDER BY T1.TransDate "

            if (BigQuery.open()):
                fname = getSaveFileName()
                if (fname):
                    efile = open(fname,"wb")
                    if (efile):
                        for rline in BigQuery:
                            #efile.writelines(rline.Jurisdiction.ljust(3,"0"))
                            efile.writelines(rline.CUIT.ljust(13,"0"))
                            efile.writelines(str("0").rjust(5,"0"))
                            efile.writelines(str("0").rjust(1,"0"))
                            efile.writelines(rline.TransDate.strftime("%d/%m/%Y"))
                            #Office = str(rline.RetDocNr).rjust(12,"0")[8:11]
                            #if (Office == "0000"): Office = "0001" 
                            #efile.writelines(Office)
                            efile.writelines(str(rline.RetDocNr).rjust(8,"0"))
                            #efile.writelines("FA")
                            #InvoiceNr = str(rline.DocNr)
                            #A 1234-12345678
                            #012345678901234
                            #if (InvoiceNr[0:1].isalpha()):
                            #    InvoiceNr = "%s%s"%(str(rline.DocNr[2:5]).rjust(4,"0"),str(str(rline.DocNr[7:14]).rjust(16,"0")))
                            #efile.writelines(InvoiceNr.rjust(20,"0"))
                            efile.writelines(str("%.2f" %rline.Amount).rjust(16,"0"))
                            efile.writelines(str("%.2f" %rline.Base).rjust(16,"0"))
                            efile.writelines("\r\n")
                        efile.close()
                else:
                    return False
            message(tr("Export finished"))

        elif (record.Option == 1):
            IQuery = Query()
            IQuery.sql  = "SELECT Prov.FiscalNr Jurisdiction,S.TaxRegNr CUIT,PI.TransDate TransDate,PI.InvoiceNr RetDocNr, "
            IQuery.sql += "     PI.InvoiceNr DocNr, PIr.RowTotal Amount, PI.Total Total, PI.VATTotal Iva  "
            IQuery.sql += "FROM PurchaseInvoiceRow PIr "
            IQuery.sql += "INNER JOIN PurchaseInvoice PI ON (PIr.masterId = PI.internalId AND PI.Status = i|1|) "
            IQuery.sql += "INNER JOIN Supplier S ON PI.SupCode = S.Code "
            IQuery.sql += "INNER JOIN Province Prov ON Prov.IngBrutPerAcc = PIr.Account "
            IQuery.sql += "WHERE?AND (PI.{Invalid}<>i|1| OR PI.{Invalid} IS NULL)\n"
            IQuery.sql += "WHERE?AND (PI.{Internalflag} = 0 OR PI.{Internalflag} IS NULL) "
            IQuery.sql += "AND (PI.{Status} = i|1|)\n"
            if (record.FromDate and record.ToDate):
                IQuery.sql += "AND PI.TransDate BETWEEN d|%s| AND d|%s| " %(record.FromDate,record.ToDate)

            if (IQuery.open()):
                fname = getSaveFileName()
                if (fname):
                    efile = open(fname,"wb")
                    if (efile):
                        for rline in IQuery:
                            #efile.writelines(str(rline.Jurisdiction).ljust(3,"0"))
                            efile.writelines(rline.CUIT.ljust(13,"0"))
                            efile.writelines(str("0").rjust(5,"0"))
                            efile.writelines(str("0").rjust(1,"0"))
                            efile.writelines(rline.TransDate.strftime("%d/%m/%Y"))
                            efile.writelines("F")
                            efile.writelines(str(rline.DocNr)[0:1].rjust(1,"0"))
                            efile.writelines(str(rline.DocNr)[2:6].rjust(4,"0"))
                            efile.writelines(str(rline.DocNr)[7:15].rjust(8,"0"))
                            efile.writelines(str("%.2f" %rline.Amount).rjust(16,"0"))
                            Base = rline.Total - rline.Amount - rline.Iva
                            efile.writelines(str("%.2f" %Base).rjust(16,"0"))
                            efile.writelines("\r\n")
                        efile.close()
                else:
                    return False
            message(tr("Export finished"))