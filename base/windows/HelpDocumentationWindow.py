#encoding: utf-8
from OpenOrange import *
from GlobalTools import *

ParentHelpDocumentationWindow = SuperClass("HelpDocumentationWindow","MasterWindow",__file__)
class HelpDocumentationWindow(ParentHelpDocumentationWindow):

    def afterShowRecord(self):
        ParentHelpDocumentationWindow.afterShowRecord(self)
        record = self.getRecord()
        record.setModified(False)

    def buttonClicked (self, buttonname):
        if buttonname == "Send":
            record = self.getRecord()
            record.Detail = escapeToXml(record.Detail)
            record.setModified(False)
            self.sendDocumentation()

    def sendDocumentation (self):
        try:
            from DocumentationService_client import AppendDocumentationSoapIn, DocumentationServiceSoapSOAP
            record = self.getRecord ()
            proxy = DocumentationServiceSoapSOAP(record.URL)
            reqobj = AppendDocumentationSoapIn()

            auth = reqobj.new_Auth()
            auth.Company     = record.Company
            auth.User        = record.CompanyUserCode
            auth.UserName    = record.CompanyUserName
            auth.Password    = "None"

            reqobj.Auth = auth

            doc = reqobj.new_Data()
            doc.TableName     = record.Record
            doc.FieldName     = record.Field
            doc.Description   = record.Detail
            
            reqobj.Data = doc

            respobj = proxy.AppendDocumentation(reqobj)
            if respobj.Result.Status == 0:
                message ("Documentación enviada correctamente, gracias por tu contribución.")
                self.close()
            else:
                text = "%s: %s" %(respobj.Result.ErrorCode,respobj.Result.Description)
                message(("Error",text))
        except:
            message(tr("Connection Error"))
            message("Intente nuevamente en unos minutos.")

    def afterEdit(self, fieldname):
        afterEdit(self, fieldname)