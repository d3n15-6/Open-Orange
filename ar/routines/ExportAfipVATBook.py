#encoding: utf-8
# Agosto 2009 - Claudia Acosta
from OpenOrange import *
from Routine import Routine

class ExportAfipVATBook(Routine):
    
    """ DISEÑO DEL REGISTRO:
    --------------------------------------------------
        CAMPO                   LONGITUD    FORMATO
        -----------------------------------------------
        FECHA DE COMPROBANTE    8           AAAAMMDD
        TIPO COMPROBANTE        15          ALFANUMERICO
        LETRA COMPROBANTE       1           ALFANUMERICO
        SUCURSAL                4           ALFANUMERICO
        NUMERO DE COMPROBANTE   8           ALFANUMERICO  
        RAZON SOCIAL            30          ALFANUMERICO
        CUIT                    11          ALFANUMERICO
        IMPORTE TOTAL           12          2 DECIMALES
        IMPORTE NETO GRABADO    12          2 DECIMALES
        ALICUTOTA IVA           4           2 DECIMALES
        IMPUESTO LIQUIDADO      12          2 DECIMALES
    """


    def run(self):
        from Currency import Currency
        record = self.getRecord()
        filename = ["AfipIVAVentas","AfipIVAVentas","AfipIVACompras"]
        tipoComprobante = {} #clave: invoiceType, docType
        tipoComprobante[(0,0)] = "FAC"#"01" #factura A
        tipoComprobante[(2,0)] = "ND"#"02" #nota de debito A
        tipoComprobante[(1,0)] = "NC"#"03" #nota de credito A
        tipoComprobante[(0,1)] = "FAC"#"06" #factura B
        tipoComprobante[(2,1)] = "ND"#"07" #nota de debito B
        tipoComprobante[(3,1)] = "NC"#"08" #nota de credito B
        letter = {}
        letter[0] = "A"
        letter[1] = "B"
        docType = {}
        docType["A"] = 0
        docType["B"] = 1
        base1, base2 = Currency.getBases()
        if (record.Option == 0):
            message("No se seleccionó una opción. Se toma por default IVA Ventas")
        if (record.Option == 0 or record.Option == 1): #IVA VENTAS
            from Invoice  import Invoice
            #Invoice.DocTypes[lastrec.DocType])
            query = Query()
            query.sql = "SELECT [i].{SerNr}, [i].{TransDate},[i].{InvoiceType},[i].{DocType}, [i].{OfficialSerNr}, \n"
            query.sql += "[i].{Currency}, [i].{CurrencyRate}, [i].{BaseRate},  \n"
            query.sql += "[i].{TaxRegNr}, [i].{CustName}, [o].{ShortCode}, [vc].{Percent},  \n"
            query.sql += "SUM([ir].{RowNet}) AS RowNet, SUM([ir].{RowTotal}) AS RowTotal ,[ir].{VATCode} \n"
            query.sql += "FROM [InvoiceItemRow] [ir] \n"
            query.sql += "INNER JOIN [Invoice] [i] ON [i].{InternalId} = [ir].{MasterId} \n"
            query.sql += "INNER JOIN [Office] [o] ON [o].{Code} = [i].{Office} \n"
            query.sql += "INNER JOIN [VATCode] [vc] ON [vc].{Code} = [ir].{VATCode} \n"
            query.sql += "WHERE?AND [i].{Status} = i|1| \n"
            query.sql += "WHERE?AND (i.{Internalflag} = 0 OR i.{Internalflag} IS NULL) "
            query.sql += "WHERE?AND ([i].{Invalid} = i|0| OR  [i].{Invalid} IS NULL) \n"
            query.sql += "WHERE?AND ([i].{TransDate} BETWEEN d|%s| AND d|%s|) \n" %(record.FromDate, record.ToDate)
            query.sql += "GROUP BY [i].{SerNr}, [ir].{VATCode} \n"
            #print query.sql
            if (query.open()):
                fname = getSaveFileName("Please choose filename", DefaultFileName= "%s-%s.txt"%(filename[record.Option],now().strftime("%d-%m-%Y")))
                f = file(fname, "w")
                for rline in query:
                    line = rline.TransDate.strftime("%Y%m%d")    ##FECHA
                    #comprobante
                    try:
                        line += tipoComprobante[(rline.InvoiceType, rline.DocType)].rjust(15,"0")
                    except:
                        line += 15 * "0"
                    #letra 
                    try:
                        line += letter[rline.DocType]
                    except:
                        line += "0"
                    line += rline.ShortCode.rjust(4,"0") #sucursal
                    line += rline.OfficialSerNr[7:15].rjust(8,"0") #numero de comprobante
                    
                    line += self.doLine(rline, base1)
                    f.write(line + "\n")
                f.close()
                message("La exportacion finalizó con éxito")

        elif (record.Option ==2): #IVA COMPRAS
            query = Query()
            from PurchaseInvoice import PurchaseInvoice
            query.sql = "SELECT [i].{SerNr}, [i].{TransDate},[i].{InvoiceType}, mid([i].{InvoiceNr},1,1) as DocType,  \n"
            query.sql += "[i].{Currency}, [i].{CurrencyRate},[i].{BaseRate},  \n"
            query.sql += "[i].{TaxRegNr}, [i].{SupName} AS CustName, mid([i].{InvoiceNr},3,4) as ShortCode, [vc].{Percent}, [i].{InvoiceNr} AS OfficialSerNr, \n"
            query.sql += "SUM([ir].{RowNet}) AS RowNet, SUM([ir].{RowTotal}) AS RowTotal ,[ir].{VATCode} \n"
            query.sql += "FROM [PurchaseInvoiceRow] [ir] \n"
            query.sql += "INNER JOIN [PurchaseInvoice] [i] ON [i].{InternalId} = [ir].{MasterId}\n"
            query.sql += "INNER JOIN [VATCode] [vc] ON [vc].{Code} = [ir].{VATCode} \n"
            query.sql += "WHERE?AND [i].{Status} = i|1| \n"
            query.sql += "WHERE?AND (i.{Internalflag} = 0 OR i.{Internalflag} IS NULL) "
            query.sql += "WHERE?AND ([i].{Invalid} = i|0| OR  [i].{Invalid} IS NULL) \n"
            query.sql += "WHERE?AND ([i].{TransDate} BETWEEN d|%s| AND d|%s|) \n" %(record.FromDate, record.ToDate)
            query.sql += "GROUP BY [i].{SerNr}, [ir].{VATCode} \n"
            if (query.open()):
                fname = getSaveFileName("Please choose filename", DefaultFileName= "%s-%s.txt"%(filename[record.Option],now().strftime("%d-%m-%Y")))
                f = file(fname, "w")
                for rline in query:
                    line = rline.TransDate.strftime("%Y%m%d")    ##FECHA
                    #comprobante
                    try:
                        line += tipoComprobante[(rline.InvoiceType, docType[rline.DocType])].rjust(15,"0")
                    except:
                        line += 15 * "0"
                    #letra
                    line += rline.DocType
                    line += rline.ShortCode.rjust(4,"0") #sucursal
                    line += rline.OfficialSerNr[7:15].rjust(8,"0") #numero de comprobante
                    line += self.doLine(rline, base1)
                    f.write(line + "\n")
                f.close()
                message("La exportacion finalizó con éxito")

    def doLine(self, rline, base1):
        from Currency import Currency
        custName = rline.CustName.rjust(30," ")
        line = custName[:30] #Razon Social
        line += filter(lambda x: x.isdigit(),rline.TaxRegNr).ljust(11,"0") #CUIT
        
        rowTotalInBase1 = Currency.convertTo(rline.RowTotal,rline.CurrencyRate, rline.BaseRate,  rline.Currency, base1)
        rowTotalInBase1 *= 100
        rowTotalstr = str(int(abs(rowTotalInBase1))) #total
        line += rowTotalstr.rjust(12,"0")

        rowNetInBase1 = Currency.convertTo(rline.RowNet,rline.CurrencyRate, rline.BaseRate,  rline.Currency, base1)
        rowNetInBase1 *= 100
        rowNetstr = str(int(abs(rowNetInBase1))) #neto grabado
        line += rowNetstr.rjust(12,"0")

        num = abs(rline.Percent) * 100 #alicuota
        strnum = str(int(num))
        line += strnum.rjust(4,"0")

        liq =  abs(rowTotalInBase1 - rowNetInBase1) #impuesto liquidado
        liq *= 100
        strLiq = str(int(liq))
        line += strLiq.rjust(12,"0")

        return line