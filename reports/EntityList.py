#encoding: utf-8
from OpenOrange import *
from Report import Report

class EntityList(Report):
    
    def defaults(self):
        Report.defaults(self)
        
    
    def run(self):
        specs = self.getRecord()
        if (not self.__dict__.has_key("selectedType")):
            self.selectedType = "Customer"

        self.tables = ["Customer","Supplier","Person"]
        self.startTable()
        self.printReportTitle("Entity List")
        self.endTable()

        c = "White"
        self.startTable()
        self.startRow()
        self.addValue("Type",Color="White",BGColor="Gray")
        for ent in self.tables:
          bcol = "#CC6600"
          if (self.selectedType==ent):
             bcol = "orange"
          self.addValue(tr(ent),CallMethod="selectType",Color=c,BGColor=bcol,Parameter=ent)
        self.endRow()
        self.row("")
        self.endTable()

        query = Query()        
        query.sql  = "SELECT Code, \n"
        if self.selectedType == "Person":
            query.sql  += "CONCAT(Name,', ',LastName) AS Name "
        else:
            query.sql  += "Name \n"
        query.sql  += "FROM [%s]\n"  % self.selectedType
        #query.sql += " WHERE?AND U.AccessGroup = s|%s| \n" % r.Code 
        query.sql += " ORDER BY Code"
        if (query.open()):        
            self.startTable()
            self.header("Code","Name")
            for rec in query:                
                self.startRow()
                self.addValue(rec.Code,CallMethod="SelectEntity",Underline="True")
                self.addValue(rec.Name)
                self.endRow()
            self.endTable()    
            query.close()
            
  
  
    def SelectEntity(self,value):
        self.Mail.CustCode = value
        self.Mail.EntityType = self.tables.index(self.selectedType)
        self.Mail.pasteCustCode()
        self.close()

    def selectType(self,param,value):
        self.clear()
        self.selectedType = param
        self.run()
        self.render()

