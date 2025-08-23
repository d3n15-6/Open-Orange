#encoding: utf-8
#only in spanish
from OpenOrange import *
from Report import Report
from TaxSettings import TaxSettings
from Customer import Customer
from OurSettings import OurSettings
from Invoice import Invoice
from VATCode import VATCode
from ItemTaxGroup import ItemTaxGroup
from Currency import Currency

class IIBBHighRiskRegisterList(Report):

    def defaults(self):
        Report.defaults(self)
        specs = self.getRecord()
        specs.ExistingOnly = 1
        specs.Type = 0

    def run(self):
        specs = self.getRecord()
        self.printReportTitle("IIBBHighRiskRegisterList")
        query = Query()
        query.sql ="SELECT c.Code,c.Name,c.TaxRegNr,hr.GrpPercep,hr.AliPercep,hr.GrpRetenc,hr.AliRetenc,FrDate,ToDate "
        query.sql+="FROM [IIBBHighRiskRegister] hr \n"
        if specs.ExistingOnly:
            if specs.Type == 0:
                query.sql+="INNER JOIN [Customer] c ON REPLACE(c.TaxRegNr,'-','') = hr.{Code}\n"
            elif specs.Type == 1:
                query.sql+="INNER JOIN [Supplier] c ON REPLACE(c.TaxRegNr,'-','') = hr.{Code}\n"
        query.sql+="WHERE?AND d|%s| >= hr.{FrDate} AND d|%s| <= hr.{ToDate}  \n" % (specs.FromDate,specs.ToDate)

        self.startTable()
        self.startHeaderRow()
        self.addValue(tr("Code"))
        self.addValue(tr("Name"))
        self.addValue(tr("TaxRegNr"))
        self.addValue(tr("From"))
        self.addValue(tr("To"))
        self.addValue(tr("GrpPercep"))
        self.addValue(tr("AliPercep"))
        self.addValue(tr("GrpRetenc"))
        self.addValue(tr("AliRetenc"))
        self.endHeaderRow()
        
        if query.open():
            for rec in query:
                self.startRow()
                self.addValue(rec.Code,Window="CustomerWindow", FieldName="Code")
                self.addValue(rec.Name)
                self.addValue(rec.TaxRegNr)
                self.addValue(rec.FrDate)
                self.addValue(rec.ToDate)
                self.addValue(rec.GrpPercep)
                self.addValue(rec.AliPercep)
                self.addValue(rec.GrpRetenc)
                self.addValue(rec.AliRetenc) 
                
                self.endRow()
        self.endTable()