#encoding: utf-8
from OpenOrange import *
from Report import Report

class ReportUsage(Report):

    def run(self):
        specs = self.getRecord()
        self.printReportTitle("Report Usage")
        q = Query()
        q.sql = "SELECT TableName, COUNT(TableName) as CNT "
        if specs.GroupByUser:
            q.sql += ",User "        
        q.sql += "FROM EventLog "
        q.sql += "WHERE?AND Action = 3 AND TransDate >= d|%s| " % addDays(today(), -90)
        q.sql += "GROUP BY TableName "
        if specs.GroupByUser:
            q.sql += ",User "
        q.sql += "ORDER BY CNT DESC "
        q.open()
        self.startTable()
        for r in q:
            self.startRow()
            self.addValue(r.TableName, CallMethod="openReport", Parameter=r.TableName)
            if specs.GroupByUser:
                self.addValue(r.User)
            self.addValue(r.CNT)
            self.endRow()
        self.endTable()
        
    def openReport(self, param, value):
        exec("from %s import %s as CLS" % (param, param))
        r = CLS()
        r.open()