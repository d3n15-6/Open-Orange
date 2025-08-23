#encoding: utf-8
from OpenOrange import *
from Report import Report
from StoredProcedures import StoredProcedures

class TriggerList(Report):

    def run(self):
        record = self.getRecord()
        self.getView().resize(1100,500)
        self.printReportTitle("Trigger List")
        self.startTable()
        self.row("Delete triggers with a click on the event")
        self.endTable()
        self.startTable()
        self.header ("Timing", "Table","Event","Statement","Delete" )
        q = Query()
        q.sql = "Show Triggers;"
        if q.open():
            for sp in q:
               self.startRow()
               self.addValue(sp.Timing)
               self.addValue(sp.Table)
               self.addValue(sp.Event,CallMethod="deleteproc",Parameter=sp.Trigger,Underline=True)
               self.addValue(sp.Statement.replace('\n','<br/>'))
               self.addValue(sp.Trigger)
               self.endRow()

        self.endTable ()
        self.startTable ()
        self.startRow()
        self.addValue("Add NLT Procedure",CallMethod="addNLTproc",Parameter="xx",Underline=True)
        self.endRow()
        self.startRow()
        self.addValue("Remove All Stored Procedures",CallMethod="deleteAllproc",Parameter="xx",Underline=True)
        self.endRow()
        self.startRow()
        self.addValue("Init StockHistory",CallMethod="initStockHist",Parameter="xx",Underline=True)
        self.endRow()
        self.endRow()
        self.endTable ()


    def deleteproc(self, param, value):
        StoredProcedures.removeStoreProcedure(param)
        self.clear()
        self.run()
        self.render()

    def deleteAllproc(self, param, value):
        StoredProcedures.removeStoreProcedures()
        self.clear()
        self.run()
        self.render()

    def initStockHist(self, param, value):
        res = askYesNo(tr("Are you Sure ?"))
        if (res):
          StoredProcedures.fillStockHistory()
          message(tr("Ready!"))


    def addNLTproc(self, param, value):
        noconsistentCases = 0
        query = Query()
        query.sql  = "SELECT count(*) FROM NLT where {SerNr} <> {internalId} \n"
        if query.open():
            noconsistentCases = len(query)
        if (noconsistentCases):
          res = askYesNo(tr("Do you want to equal SerNr = internalId for all NLT History ?"))
          if (res):
              StoredProcedures.initNLT()
        StoredProcedures.loadNLTStoredProcedure()
        message(tr("Ready!"))

