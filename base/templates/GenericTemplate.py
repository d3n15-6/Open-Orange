#encoding: utf-8
from OpenOrange import *
from functions import tr
import Web
import os

class GenericTemplate(RecordTemplate):

    @classmethod
    def getHTML(objclass, record, **kwargs):
        import Web
        fn = objclass.findHTMLFilename("Generic")
        if fn:
            f = open(fn, "rb")
            html = f.read()
            template = objclass()
            template.record = record
            globals()["template"] = template
            template.basepath = kwargs.get("basepath", "")            
            globals()["record"] = record
            from OurSettings import OurSettings
            globals()["oursettings"] = OurSettings.bring()
            return Web.parsePythonTags(html, globals(), locals())
        return ""
        
    def translateText(self, text):
        return Web.escapeXMLValue(tr(text))

        
    def iterateFields(self, content):
        for fn in self.record.fieldNames():
            field = self.record.fields(fn)
            yield Web.parsePythonTags(content, globals(), locals())
