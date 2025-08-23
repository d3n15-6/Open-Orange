#encoding: utf-8
from Routine import Routine
from OurSettings import OurSettings
from TaxSettings import TaxSettings
from OpenOrange import *
from CredCardType import CredCardType
from FinAccount import FinAccount

class ExportAfipSIFERE(Routine):

    def run(self):
        """from PasteJurisdiction import PasteJurisdiction
        routine = PasteJurisdiction()
        routine.run()"""
        record = self.getRecord()
        if (record.Option == 0):
            fname = "SIFERE_Retenciones %s.txt" % today().strftime("%d-%m")
            filename = getSaveFileName("Please choose filename", DefaultFileName=fname)
            f = file(filename, "w")
            RQuery  = Query()
            RQuery.sql  = "SELECT P.Jurisdiction,C.TaxRegNr CUIT, R.TransDate TransDate, RPMr.ChequeNr RetDocNr, \n"
            RQuery.sql += "[R].{SerNr} DocNr,RPMr.Amount Amount,[O].{ShortCode} as Office, 3 as InvoiceType, 10 DocType,C.Code, \n"
            RQuery.sql += "P.Code AS Province \n"
            RQuery.sql += "FROM [ReceiptPayModeRow] RPMr \n"
            RQuery.sql += "INNER JOIN [Receipt] R ON (RPMr.masterId = R.internalId AND R.Status = i|1|) "
            RQuery.sql += "INNER JOIN [Customer] C ON (R.CustCode = C.Code) "
            RQuery.sql += "INNER JOIN [Office] O ON (O.Code = [R].{Office}) "
            RQuery.sql += "INNER JOIN [PayMode] PM ON (RPMr.PayMode = PM.Code AND PM.PayType = i|9|) " #9 = Formas de Cobro Retenciones
            RQuery.sql += "INNER JOIN [Retencion] Ret ON (PM.RetCode = Ret.Code AND Ret.Type = i|0| AND Ret.RetType = i|1|) " #0 = Retenciones de IIBB
            RQuery.sql += "INNER JOIN [Province] P ON (P.Code = Ret.Jurisdiction ) "
            rString = ""
            if (record.FromDate and record.ToDate):
                rString += "AND (R.TransDate BETWEEN d|%s| AND d|%s| ) " %(record.FromDate,record.ToDate)
            if (record.PayMode):
                rString += "AND PM.Code = s|%s| \n " %(record.PayMode)
            if (rString):
                print rString
                RQuery.sql += "WHERE (%s) \n" %(rString[3:])

            PQuery = Query()
            PQuery.sql  = "SELECT P.Jurisdiction,C.TaxRegNr CUIT, I.TransDate TransDate, IPMr.ChequeNr RetDocNr, \n"
            PQuery.sql += "I.OfficialSerNr DocNr ,IPMr.Paid Amount, [O].{ShortCode} as Office,[I].{InvoiceType},[I].{DocType},C.Code, \n "
            PQuery.sql += "P.Code AS Province \n"
            PQuery.sql += "FROM [InvoicePayModeRow] IPMr "
            PQuery.sql += "INNER JOIN [Invoice] I ON (IPMr.masterId = I.internalId AND I.Status = i|1|) "
            PQuery.sql += "INNER JOIN [Office] O ON (O.Code = [I].{Office})  "
            PQuery.sql += "INNER JOIN [Customer] C ON (I.CustCode = C.Code) "
            PQuery.sql += "INNER JOIN [PayMode] PM ON (IPMr.PayMode = PM.Code AND PM.PayType = i|9|) " #9 = Formas de Cobro Retenciones
            PQuery.sql += "INNER JOIN [Retencion] Ret ON (PM.RetCode = Ret.Code AND Ret.RetType = i|1| AND Ret.Type = i|0|) " #0 = Retenciones de IIBB
            PQuery.sql += "INNER JOIN [Province] P ON (P.Code = Ret.Jurisdiction ) "
            pString = ""
            if (record.FromDate and record.ToDate):
                pString += "AND (I.TransDate BETWEEN d|%s| AND d|%s|) " %(record.FromDate,record.ToDate)
            if (record.PayMode):
                pString += "AND PM.Code = s|%s| \n " %(record.PayMode)
            if (pString):
                PQuery.sql += "WHERE (%s) \n" %(pString[3:])
            BigQuery = Query()
            BigQuery.sql  = "SELECT T1.Jurisdiction, T1.CUIT, T1.TransDate, T1.RetDocNr, T1.DocNr, T1.Amount,T1.Office,T1.InvoiceType,T1.DocType,T1.Code, T1.Province \n"
            BigQuery.sql += "FROM ((%s) UNION ALL (%s)) AS T1 " %(RQuery.sql,PQuery.sql)
            BigQuery.sql += "ORDER BY T1.TransDate "
            custCode = []
            if (BigQuery.open()):
                #sysprint(BigQuery.sql)
                #log(BigQuery.sql)
                for rline in BigQuery:
                    Line = rline.Jurisdiction                     #JURIDISCCION
                    if not Line:
                        Line = "000"
                        if rline.Code not in custCode:
                            custCode.append(rline.Code)
                    Line += rline.CUIT.ljust(13,"0")                ##CUIT
                    Line += rline.TransDate.strftime("%d/%m/%Y")    ##FECHA
                    rdn  = str(rline.RetDocNr).rjust(10,"0")
                    Line += rdn[0:4]
                    Line += rdn[4:10].rjust(16,"0")
                    if rline.InvoiceType == 0: Line += "F"          ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 1: Line += "C"        ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 2: Line += "D"        ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 3:
                        Line += "R"        ##LETRA COMPROBANTE
                        Line += " "
                        Line += str(rline.DocNr).rjust(20,"0")
                    if rline.InvoiceType < 3:
                        if rline.DocType == 0: Line += "A"
                        elif rline.DocType == 1: Line += "B"
                        elif rline.DocType == 2: Line += "C"
                        elif rline.DocType == 3: Line += "E"
                        elif rline.DocType == 5: Line += "M"
                        elif rline.DocType == 6: Line += "L"
                        Line += rline.Office.rjust(4,"0")                 ## SUCURSAL
                        Line += rline.DocNr[-8:].rjust(16,"0")
                    num = "%.2f" % rline.Amount
                    num = num.replace(".",",")
                    Line +=(num.rjust(11,"0"))
                    f.write(Line + "\n")
                f.close()
                if custCode:
                    message("No se encontro provincia de entrega en clientes %s" % custCode)
                message(tr('Exportation Done'))

        elif (record.Option == 1):
            fname = "SIFERE_Percepciones %s.txt" % today().strftime("%d-%m")
            filename = getSaveFileName("Please choose filename", DefaultFileName=fname)
            f = file(filename, "w")
            IQuery = Query()
            IQuery.sql  = "SELECT P.Jurisdiction ,S.TaxRegNr CUIT,PI.TransDate TransDate, \n"
            IQuery.sql += "PIr.ChequeNr RetDocNr, PIr.Paid Amount,RPAD(O.ShortCode,4,0) AS Office,PI.InvoiceType,PI.InvoiceNr as DocNr, Ret.Code  \n"
            IQuery.sql += "FROM PurInvPayModeRow PIr \n"
            IQuery.sql += "INNER JOIN PurchaseInvoice PI ON (PIr.masterId = PI.internalId AND PI.Status = i|1|) "
            IQuery.sql += "INNER JOIN Supplier S ON PI.SupCode = S.Code "
            IQuery.sql += "INNER JOIN Office O ON O.Code = PI.Office "
            IQuery.sql += "INNER JOIN PayMode PM ON (PIr.PayMode = PM.Code AND PM.PayType = i|4|) " #9 = Formas de Cobro Retenciones
            IQuery.sql += "INNER JOIN Retencion Ret ON (PM.RetCode = Ret.Code AND Ret.RetType = i|1| AND Ret.Type = i|0|) " #0 = Retenciones de IIBB
            IQuery.sql += "INNER JOIN Province P ON P.Code = Ret.Jurisdiction "

            iString = ""
            if (record.FromDate and record.ToDate):
                iString += "AND (PI.TransDate BETWEEN d|%s| AND d|%s|) " %(record.FromDate,record.ToDate)
            if (record.PayMode):
                iString += "AND PM.Code = s|%s| \n " %(record.PayMode)

            if (iString):
                IQuery.sql += "WHERE (%s) \n" %(iString[3:])

            PIQuery = Query()
            PIQuery.sql  = "SELECT P.Jurisdiction, \n"
            PIQuery.sql += "S.TaxRegNr CUIT,PI.TransDate TransDate, \n"
            PIQuery.sql += "MID(PI.InvoiceNr,8,8) RetDocNr, PIr.RowTotal Amount,MID(PI.InvoiceNr,3,4) AS Office,PI.InvoiceType,PI.InvoiceNr as DocNr, 0 as Code \n"
            PIQuery.sql += "FROM PurchaseInvoice PI "
            PIQuery.sql += "INNER JOIN Supplier S ON PI.SupCode = S.Code "
            PIQuery.sql += "INNER JOIN PurchaseInvoiceRow PIr ON PI.internalId = PIr.masterId "
            PIQuery.sql += "INNER JOIN Province  P ON P.IngBrutPerAcc = PIr.Account "

            if (record.FromDate and record.ToDate):
                PIQuery.sql += "WHERE?AND PI.TransDate BETWEEN d|%s| AND d|%s| " %(record.FromDate,record.ToDate)
            PIQuery.sql += "WHERE?AND PI.Status = i|1| "
            PIQuery.sql += "WHERE?AND (PI.{Internalflag} = 0 OR PI.{Internalflag} IS NULL) "
            PIQuery.sql += "WHERE?AND P.Jurisdiction <> i|999| "
            ### Se Saca esto ya que el aplicativo tiene que informar las retenciones que le hicieron al cliente.
            #No las que el hizo, estos datos se usan en el arib y arciba
            #"""PQuery = Query()
            #PQuery.sql  = "SELECT P.Jurisdiction Jurisdiction, S.TaxRegNr CUIT,PI.TransDate TransDate, \n"
            #PQuery.sql += "RD.DocNr RetDocNr, PIr.Amount Amount, RPAD(O.ShortCode,4,0) AS Office, 3 as InvoiceType,0 as DocNr, Ret.Code \n"
            #PQuery.sql += "FROM PaymentPayModeRow PIr \n"
            #PQuery.sql += "INNER JOIN Payment PI ON (PIr.masterId = PI.internalId AND PI.Status = i|1|) "
            #PQuery.sql += "INNER JOIN Office O ON O.Code = PI.Office "
            #PQuery.sql += "INNER JOIN Supplier S ON PI.SupCode = S.Code "
            #PQuery.sql += "INNER JOIN RetencionDoc RD ON (RD.PaymentNr = PI.SerNr) " #0 = Retenciones de IIBB
            #PQuery.sql += "INNER JOIN PayMode PM ON (PIr.PayMode = PM.Code AND PM.PayType = i|4|) " #4 = Formas Retenciones
            #PQuery.sql += "INNER JOIN Retencion Ret ON (PM.RetCode = Ret.Code AND Ret.RetType = i|1| AND Ret.Type = i|0|) " #0 = Retenciones de IIBB
            #PQuery.sql += "INNER JOIN Province P ON P.Code = Ret.Jurisdiction "
            #
            #pString = ""
            #if (record.FromDate and record.ToDate):
            #    pString += "AND (PI.TransDate BETWEEN d|%s| AND d|%s|) " %(record.FromDate,record.ToDate)
            #if (record.PayMode):
            #    pString += "AND PM.Code = s|%s| \n " %(record.PayMode)
            #if (pString):
            #    PQuery.sql += "WHERE (%s)" % pString[3:]
            #
            #BigQuery = Query()
            #BigQuery.sql  = "SELECT T1.Jurisdiction, T1.CUIT, T1.TransDate,T1.DocNr, T1.RetDocNr, T1.Amount,T1.Office,T1.InvoiceType,T1.Code "
            #BigQuery.sql += "FROM (%s UNION ALL %s UNION ALL %s) AS T1 " %(IQuery.sql,PQuery.sql, PIQuery.sql)
            #BigQuery.sql += "ORDER BY T1.TransDate "
            #"""
            BigQuery = Query()
            BigQuery.sql  = "SELECT T1.Jurisdiction, T1.CUIT, T1.TransDate,T1.DocNr, T1.RetDocNr, T1.Amount,T1.Office,T1.InvoiceType,T1.Code "
            BigQuery.sql += "FROM (%s UNION ALL %s ) AS T1 " %(IQuery.sql, PIQuery.sql)
            BigQuery.sql += "ORDER BY T1.TransDate "
            juris = []
            if (BigQuery.open()):
                for rline in BigQuery:
                    Line = rline.Jurisdiction
                    if not Line:
                        Line = "000"
                        if rline.Code not in juris:
                            juris.append(rline.Code)
                    Line += rline.CUIT.ljust(13,"0")                ##CUIT
                    Line += rline.TransDate.strftime("%d/%m/%Y")    ##FECHA
                    Line += rline.Office.rjust(4,"0")                 ## SUCURSAL

                    Line += str(rline.RetDocNr).rjust(8,"0")

                    if rline.InvoiceType == 0: Line += "F"          ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 1: Line += "C"        ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 2: Line += "D"        ##LETRA COMPROBANTE
                    elif rline.InvoiceType == 3:
                        Line += "R"        ##LETRA COMPROBANTE
                    if rline.DocNr[0:1].isalpha():
                        Line += rline.DocNr[0:1]#.rjust(,"0")
                    else:
                        Line += " "
                    num = "%.2f" % rline.Amount
                    num = num.replace(".",",")
                    Line += (num.rjust(11,"0"))
                    f.write(Line + "\n")
                f.close()
                if juris:
                    message("No se encontro jurisdiccion en la provincia %s" % juris)
                message(tr('Exportation Done'))
