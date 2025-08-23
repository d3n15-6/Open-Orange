#encoding: utf-8
from OpenOrange import *
from GlobalTools import *

ParentHelpDocumentation = SuperClass("HelpDocumentation","Master",__file__)
class HelpDocumentation(ParentHelpDocumentation):

    def defaults(self):
        from OurSettings import OurSettings
        os = OurSettings.bring ()
        if os:
            self.Company = os.Name
        self.URL = "http://www.openorange.com.ar:11001/WSActions/DocumentationServices.py"
        #self.URL = "http://127.0.0.1:11001/WSActions/DocumentationServices.py"
        self.User = currentUser()
        self.pasteUser()

    def pasteRecord(self):
        self.Code = "%s.%s" %(self.Record,self.Field)

    def pasteField(self):
        self.Code = "%s.%s" %(self.Record,self.Field)
        exec("from %s import %s" %(self.Record,self.Record))
        exec("rec = %s()" %self.Record)
        exec("self.Label = rec.getFieldLabel('%s') " %self.Field)
        gri = getRecordsInfo()
        if (self.Field and self.Record):
            ftype = gri["%s" %(self.Record)]["Fields"]["%s" %(self.Field)]["Type"]
            length = 0
            if (ftype == "string"):
                length = gri["%s" %(self.Record)]["Fields"]["%s" %(self.Field)]["Length"]
            self.Type = ftype
            self.Length = length

    def pasteUser(self):
        self.UserName = getMasterRecordField("User","Name",self.User)
