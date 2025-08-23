#from OpenOrange import * #No se puede importar OpenOrange porque OpenOrange importa este archivo
import os

class RecordTemplate:

    def __init__(self):
        pass

    def setup(self):
        pass

    def tr(self, text):
        import Web
        from OpenOrange import tr
        return Web.escapeXMLValue(tr(text))

    def label(self, record,field):
        import Web
        return Web.escapeXMLValue( record.getFieldLabel(field,getattr(record,field))   )

    @classmethod
    def findHTMLFilename(objclass, recordname):
        from functions import getScriptDirs
        sdirs = getScriptDirs()
        for sd in sdirs:
            if os.path.exists(os.path.join(sd, "templates", recordname + ".html")):
                return os.path.join(sd, "templates", recordname + ".html")
        return None

    def getImgPath(self, img):
        from OpenOrange import getImagePath
        imgpath = getImagePath(img)
        if self.basepath:
            imgpath = self.basepath + "/" + imgpath
        return imgpath
        
    @classmethod
    def getHTML(objclass, record, **kwargs):
        import Web
        fn = objclass.findHTMLFilename(record.name())
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
            from TaxSettings import TaxSettings
            globals()["taxsettings"] = TaxSettings.bring()
            template.setup()            
            return Web.parsePythonTags(html, globals(), locals())
        return ""

    def getRecordFields(self, RecordName, RecordField, field):
        try:
            exec("from %s import %s" % (RecordName, RecordName))
            if not RecordField:
                exec("rec = %s.bring()" % RecordName)
            elif self.record.fields(RecordField).getType() == "string":
                exec("rec = %s.bring('%s')" % (RecordName, self.record.fields(RecordField).getValue()))
            elif self.record.fields(RecordField).getType() == "integer":
                exec("rec = %s.bring(%i)" % (RecordName, self.record.fields(RecordField).getValue()))
            if rec:
                if field == "TaxRegTypeDescription" and RecordName == "Customer":
                    return Customer.TaxRegTypes[rec.TaxRegType]
                if not rec.fields(field).isNone():
                    return rec.fields(field).getValue()
        except:
            pass
        return ""