#encoding: utf-8
from OpenOrange import *
import string
import re

ParentHTMLRecordView = SuperClass("HTMLRecordView","Master",__file__)
class HTMLRecordView(ParentHTMLRecordView):

    def defaults(self):             
        self.RecordRow = "Customer"        
        self.reloadFields()

    def afterLoad(self):        
        self.reloadFields()
        
    def reloadFields(self):        
        if (self.RecordRow):
            self.HTMLRecordViewRows.clear()
            from HTMLRecordViewRow import HTMLRecordViewRow

            record = NewRecord(self.RecordRow)
            rows = {}
            query = Query()
            query.sql = "DESCRIBE [%s]" % self.RecordRow
            if (query.open()):
                for field in query:        
                    rows[record.getFieldLabel(field.Field)] = field.Field
            rows = rows.items()
            rows.sort()
            for key,value in rows:
                rowAux = HTMLRecordViewRow()
                rowAux.Name = "%s" % value
                rowAux.Comment = "%s" % key
                self.HTMLRecordViewRows.append(rowAux)

    def sortDict(self, adict):        
        items = adict.items()
        items.sort()
        
        return [value for key, value in items]

    def Reload(self):
        self.reloadFields()
        
    def addClause(self):
        if (self.Clause):
            self.Message += "$$%s" % self.Clause 

    def addField(self, nr):
        self.Message += "##%s.%s" % (self.RecordRow, self.HTMLRecordViewRows[nr].Name)
        # TODO: se puede llegar a hacer algo por el estilo:
        # self.Message += "<INPUT TYPE=\"hidden\" NAME=\"recipient\" VALUE=\"OCULTO\"/>"

    def getIMGTags(self, html):
        tags = []
        regexp = re.compile("(<img[^>]*>)")
        pos = 0
        while True:
            search = regexp.search(html,pos)
            if search:
                pos = search.end(1) + 1
                for g in search.groups():
                    tags.append(g)                
            else:
                break
        return tags

    def getFilenameFromIMG(self, tag, root=''):
        fn = ""
        regexp = re.compile("src=([^\" >]+)")
        search = regexp.search(tag)
        if search: 
            fn = search.group(1)
        else:
            regexp = re.compile("src=\"([^\">]+)\"")
            search = regexp.search(tag)
            if len(search.groups()): 
                fn = search.group(1)
        originalfn = fn
        if fn.startswith("file:///"): fn = fn[8:]
        fn = fn.replace('|', ':').replace("%20",' ')
        import os.path
        if not os.path.isabs(fn): fn = root + "/" + fn
        return fn, originalfn


    def importHTML(self, html, root):
        tags = self.getIMGTags(html)
        newhtml = html
        for tag in tags:
            imgfn, originalimgfn = self.getFilenameFromIMG(tag,root)
            
            if imgfn != "":
                try:
                    img = file(imgfn, "rb")
                    attachid = self.createMimeImageAttach(img.read())
                    img.close()
                    newtag = tag.replace(originalimgfn, attachid)
                    newhtml = newhtml.replace(tag, newtag)
                except:
                    return ErrorResponse("El archivo %s no se pudo abrir" % imgfn)
        
        self.Message = newhtml
        return self.save()

    @classmethod    
    def replaceNames(classobj, record, msg, tables):
        # Patron de cambio: ##Tabla.Campo => record.Campo, si record es del tipo Tabla
        import re
        msg = re.sub(">", "> ", re.sub("<", " <", msg))        
        toberepl = []
        words = string.split(msg)
        for word in words:            
            l = re.findall("##\w+\.\w+", word)            
            for word in l:                
                toberepl.append(word)
        tables = tables.split(",")
        for fieldname in toberepl:            
            i = fieldname.find(".")
            if (i != -1):
                for table in tables:
                    recName = fieldname[2:i]
                    rec = NewRecord(table)
                    rec.internalId = record.internalId
                    rec.load()
                    if ((fieldname[i+1:] in rec.fieldNames()) and (table == recName)):
                        replText = rec.fields(fieldname[i+1:]).getValue()                        
                        if (replText):
                            replText = HTMLRecordView.replaceEntities(replText)
                            msg = string.replace(msg, fieldname, replText)
                        else:
                            msg = string.replace(msg, fieldname, "")
        msg = re.sub("> ", ">", re.sub(" <", "<", msg))   
        return msg

    @classmethod
    def replaceClauses(objclass, msg):        
        import re
        msg = re.sub(">", "> ", re.sub("<", " <", msg))
        toberepl = []
        words = string.split(msg)
        for word in words:
            if (word[0:2]=="$$"): toberepl.append(word)
        for replaceCode in toberepl:
            from Clauses import Clauses
            replClause  = Clauses()
            replClause.Code = replaceCode[2:]
            replClause.load()
            replText = HTMLRecordView.replaceEntities(replClause.Text)
            msg = string.replace(msg, replaceCode, replText) 
        msg = re.sub("> ", ">", re.sub(" <", "<", msg))
        return msg

    @classmethod    
    def replaceEntities(objclass, msg):
        msg2 = "";        
        for c in str(msg):
            if (ord(c) > 128):
                msg2 += "&#%i;" % ord(c)
            else:
                msg2 += c
        return msg2

    def applyToRecord(self, record):
        return HTMLRecordView.replaceNames(record, self.Message, record.tableName())