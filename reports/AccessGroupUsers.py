#encoding: utf-8
from OpenOrange import *
from Report import Report

class AccessGroupUsers(Report):

    def run(self):
        record = self.getRecord()
        
        query = Query()
        query.sql  = "SELECT [U].*,[AG].{Comment} {AGName} FROM [User] [U] "
        query.sql  += "LEFT JOIN [AccessGroup] [AG] ON [AG].{Code} = [U].{AccessGroup} "
        if (record.Code):
            query.sql += " WHERE?AND [U].{AccessGroup} = s|%s| " % record.Code
        query.sql += " ORDER BY [U].{AccessGroup}, [U].{Code}"
        
        if (query.open()):
            
            self.printReportTitle("Users by Access Group")

            self.startTable()
            self.header("Code","Name","Sales Group","Person","Office","Stock Depo")
            curGrp = -1
            for rec in query:
                if curGrp <> rec.AccessGroup:
                    header = False
                    curGrp = rec.AccessGroup
                if  not header:
                    self.startRow(Style="B")
                    self.addValue(rec.AccessGroup)
                    self.addValue(rec.AGName)
                    self.addValue(" ",ColSpan=4)
                    self.endRow()
                    header = True
                self.startRow()
                self.addValue(rec.Code ,Window = "UserWindow", FieldName = "Code" )
                self.addValue(rec.Name)
                self.addValue(rec.SalesGroup)
                self.addValue(rec.Person)
                self.addValue(rec.Office)
                self.addValue(rec.StockDepo)
                self.endRow()
                    
            self.endTable()
            query.close()