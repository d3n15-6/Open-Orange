#encoding: utf-8
#only in spanish
from OpenOrange import *
from Report import Report
import time
from Province import Province

class IIBBReport(Report):

    def defaults(self):
        Report.defaults(self)
        record = self.getRecord()
        record.Address = 0
        record.ReportType = 0

    def run(self):
        specs = self.getRecord()
        if (specs.ReportType==2) or (specs.ReportType==3):
            self.ConvenioMultilateral()
            return
        self.SalesPerAct = {}
        self.printReportTitle("Informe Ingresos Brutos")
        qry = Query()
        qry.sql  = "SELECT [I].{TransDate}, [Itm].{TaxCode1}, [I].{SerNr}, [I].{TransDate}, "
        qry.sql += "SUM([IIr].{RowNet}) as {SubTotal}, "
        if (specs.Address==0):
            qry.sql  += "[I].{ProvinceCode} as {Prov} "
        if (specs.Address==1):
            qry.sql  += "[I].{DelProvinceCode} as {Prov} "
        if (specs.Address==2):
            qry.sql += "[C].{ProvinceCode} as {Prov} "
        qry.sql += "FROM [Invoice] [I] "
        qry.sql += "INNER JOIN [InvoiceItemRow] [IIr] ON [I].{internalId} = [IIr].{masterId} "
        qry.sql += "INNER JOIN [Item] [Itm] ON [Itm].{Code} = [IIr].{ArtCode} "
        qry.sql += "INNER JOIN [VATCode] [VC] ON [IIr].{VATCode} = [VC].{Code} "
        if (specs.Address==2):
            qry.sql += "INNER JOIN [Customer] [C] ON [C].{Code} = [I].{CustCode} "
        qry.sql += "WHERE?AND [I].{TransDate} BETWEEN d|%s| AND d|%s| " % (specs.FromDate,specs.ToDate)
        qry.sql += "WHERE?AND [I].{Status} = i|1| "
        qry.sql += "WHERE?AND ([I].{Internalflag} = 0 OR [I].{Internalflag} IS NULL) "
        qry.sql += "WHERE?AND ([I].{Invalid} = 0 OR [I].{Invalid} IS NULL) "
        qry.sql += "WHERE?AND [I].{TaxRegType} <> i|6| "
        qry.sql += "WHERE?AND ([I].InvoiceType <> i|2| OR ([I].InvoiceType = 2 AND VC.Percent <> 0.0)) "
        if (specs.Office):
            qry.sql += "WHERE?AND [I].{Office} = s|%s| " %(specs.Office)

        if (specs.ReportType==0):
            #Resumido
            qry.sql += "GROUP BY {Prov},{TaxCode1} "
        if (specs.ReportType==1):
            #Detallado
            qry.sql += "GROUP BY [I].{SerNr} "
        if qry.open():
            tot = 0.0
            self.startTable()
            if (specs.ReportType==0):
                self.startHeaderRow()
                self.addValue(tr("Province"))
                self.addValue(tr("Activity"))
                self.addValue(tr("Total"))
                self.endHeaderRow()
                for row in qry:
                    self.startRow()
                    pr = Province.bring(row.Prov)
                    if pr:
                        self.addValue(pr.Name)
                    else:
                        self.addValue(row.Prov)
                    self.addValue(row.TaxCode1)
                    self.addValue(row.SubTotal)
                    tot += row.SubTotal
                    self.endRow()
                self.startHeaderRow()
                self.addValue(tr("Total"))
                self.addValue("")
                self.addValue(tot)
                self.endHeaderRow()
                self.endTable()
                qry.close()
            if (specs.ReportType==1):
                self.startHeaderRow()
                self.addValue(tr("Number"))
                self.addValue(tr("Date"))
                self.addValue(tr("Activity"))
                self.addValue(tr("Province"))
                self.addValue(tr("Total"))
                self.endHeaderRow()
                for row in qry:
                    self.startRow()
                    pr = Province.bring(row.Prov)
                    self.addValue(row.SerNr,Window="InvoiceWindow", FieldName="SerNr")
                    self.addValue(row.TransDate)
                    self.addValue(row.TaxCode1)
                    if pr:
                        self.addValue(pr.Name)
                    else:
                        self.addValue(row.Prov)
                    self.addValue(row.SubTotal)
                    tot += row.SubTotal
                    self.endRow()
                self.startHeaderRow()
                self.addValue(tr("Total"))
                self.addValue("")
                self.addValue("")
                self.addValue("")
                self.addValue(tot)
                self.endHeaderRow()
                self.endTable()
                qry.close()

    def getProvinceList(self):
        plist = {}
        query = Query()
        query.sql = "SELECT {Code},{Name},{TaxCoef} FROM [Province] "
        if query.open():
          for rec in query:
             plist[rec.Code] = (rec.Name,rec.TaxCoef)
        return plist

    def getActivityCoef(self):
        actCoef = {}
        query = Query()
        query.sql = "SELECT {Province},{ItemTaxGroup},{TaxPercent} FROM [IIBBPercep] "
        if query.open():
          for rec in query:
             if rec.ItemTaxGroup not in actCoef.keys():
                actCoef[rec.ItemTaxGroup] = {}
             actCoef[rec.ItemTaxGroup][rec.Province] = rec.TaxPercent
        return actCoef

    def ConvenioMultilateral(self):
        specs = self.getRecord()
        Total = 0
        plist = self.getProvinceList()
        alist = self.getActivityCoef()
        aSales = {}
        self.SalesPerAct = {}
        specs = self.getRecord()
        qry = Query()
        qry.sql  = "SELECT [Itm].{TaxCode1},SUM([IIr].{RowNet}) as {SubTotal} "
        qry.sql += "FROM [Invoice] [I] "
        qry.sql += "INNER JOIN [InvoiceItemRow] [IIr] ON [I].{internalId} = [IIr].{masterId} "
        qry.sql += "INNER JOIN [Item] [Itm] ON [Itm].{Code} = [IIr].{ArtCode} "
        qry.sql += "WHERE?AND [I].{TransDate} BETWEEN d|%s| AND d|%s| " % (specs.FromDate,specs.ToDate)
        qry.sql += "WHERE?AND [I].{Status}=i|1| "
        qry.sql += "WHERE?AND [I].{TaxRegType} <> i|6| "
        qry.sql += "WHERE?AND [I].{Invalid}<>i|1| "
        if (specs.Office):
            qry.sql += "WHERE?AND [I].{Office} = s|%s| " %(specs.Office)
        qry.sql += "GROUP BY {TaxCode1} "
        if qry.open():
            for rec in qry:
               aSales[rec.TaxCode1] = rec.SubTotal
               Total += rec.SubTotal
        self.startTable()

        self.startHeaderRow()
        self.addValue(tr("Province"))
        self.addValue(tr("CM"))
        self.addValue(tr("Total"))
        for igroup in alist.keys():
            self.addValue(igroup)
        self.endHeaderRow()

        for prov in plist.keys():
            pcoef = plist[prov][1]
            provinceSales = pcoef * Total
            self.startRow()
            self.addValue(plist[prov][0])
            self.addValue(plist[prov][1])
            self.addValue(provinceSales)
            for igroup in alist.keys():
               coef = (alist[igroup].get(prov,0) / 100.00)
               ProvActSales = aSales.get(igroup,0) * pcoef
               if (specs.ReportType==2):
                 self.addValue(ProvActSales)
               else:
                 self.addValue(coef*ProvActSales)
            self.endRow()

        self.startHeaderRow()
        self.addValue(tr("Total"))
        self.addValue("")
        self.addValue(Total)
        for igroup in alist.keys():
          self.addValue(aSales.get(igroup,0))
        self.endHeaderRow()


