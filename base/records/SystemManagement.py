#encoding: utf-8
# Agosto 2007 - Martin Salcedo
from OpenOrange import *
from xml.sax import handler, saxutils
from GlobalTools import *
import string
import os

ParentSystemManagement = SuperClass("SystemManagement","Setting",__file__)
class SystemManagement(ParentSystemManagement):

    def loadCompanies(self):
        def makeList(line):
            res = line.replace("\n","").split("\t")
            return res
        self.Companies.clear()
        cdata = open("local/Company.data","r")
        filelines = cdata.readlines()
        header = makeList(filelines[1])
        for linenr in range(2,len(filelines)):
            curline = makeList(filelines[linenr])
            crow = SystemManagementCompanyRow()
            for colnr in range(0,len(curline)):
                curheader = header[colnr]
                curvalue  = curline[colnr]
                if (curheader in crow.fieldNames()):
                    crow.fields(curheader).setValue(curvalue)
                #crow.internalId = linenr - 1
            self.Companies.append(crow)

    def beforeInsert(self):
        res = ParentSystemManagement.beforeInsert(self)
        if not res: return res
        self.assignSettingsXMLLevels()
        self.assignCompanyDataInternalId()
        return res

    def beforeUpdate(self):
        res = ParentSystemManagement.beforeUpdate(self)
        if (not res): return res
        self.assignSettingsXMLLevels()
        self.assignCompanyDataInternalId()
        return res

    def assignCompanyDataInternalId(self):
        for rline in self.Companies:
            rline.internalId = rline.rowNr + 1

    def check(self):
        res = ParentSystemManagement.check(self)
        if (not res): return res
        for rline in self.Modules:
            if (not os.path.exists(rline.Directory) and rline.Enabled):
                rline.Enabled = False
                return rline.FieldErrorResponse("La ruta %s, no existe, verifique directorio" %os.path.realpath(rline.Directory),"Directory")
        return res

    def afterUpdate(self):
        res = ParentSystemManagement.afterUpdate(self)
        if (not res): return res
        self.writeSettingsXML()
        self.writeCompanyData()
        return res

    def afterInsert(self):
        res = ParentSystemManagement.afterInsert(self)
        if (not res): return res
        self.writeSettingsXML()
        self.writeCompanyData()
        return res

    def assignSettingsXMLLevels(self):
        for rline in self.Modules:
            rline.Level = rline.rowNr

    def refreshFromSettingsFile(self):
        self.Modules.clear()
        fname = getSettingsFileName()
        self.readSettingsFile(fname)
        return self

    def readSettingsFile(self, fname):
        from xml.sax import make_parser
        from xml.sax.handler import feature_namespaces
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        xmlfile = XMLSettingsHandler()
        xmlfile.srecord = self
        parser.setContentHandler(xmlfile)
        parser.parse(open(fname))
        return

    def addScriptDir(self, dname, afterd):
        for mline in self.Modules:
            if (mline.Directory == "standard"):
                srow = SystemManagementModuleRow()
                srow.Directory = dname
                srow.Enabled = True
                self.Modules.insert(srow.rowNr+2,srow)
                break

    def updateFromServer(self):
        if (self.AskBeforeChange):
            res = getSelection("Desea actualizar su settings.xml?", ("No", "Si"))
            if (res == "Si"):
                self.writeSettingsXML()
        else:
            self.writeSettingsXML()

    def writeCompanyData(self):
        if (self.Companies.count() > 0):
            flist = []
            flist.append("ApplicationType")
            flist.append("Code")
            flist.append("DBName")
            flist.append("DefaultUser")
            flist.append("DefaultUserPassword")
            flist.append("Host")
            flist.append("Name")
            flist.append("Password")
            flist.append("Port")
            flist.append("User")
            flist.append("attachFlag")
            flist.append("internalId")
            flist.append("syncVersion")
            companydata = open("local/Company.data","wb")
            companydata.writelines('CompanyData\n')
            companydata.writelines("%s\n" %("\t".join(flist)))
            for cline in self.Companies:
                vlist = []
                for colname in flist:
                    vlist.append("%s" %(cline.fields(colname).getValue()))
                companydata.writelines("%s\n" %("\t".join(vlist)))
            companydata.flush()
            companydata.close()

    @runOnClient
    def writeSettingsXML(self):
        if (self.Modules.count() > 0):
            settings = open(getSettingsFileName(),"wb")
            settings.writelines('<settings>\n')
            settings.writelines('    <dbserver>%s</dbserver>\n' %self.DbServer)
            settings.writelines('    <skin>%s</skin>\n'%self.Skin)
            settings.writelines('    <logqueries>%s</logqueries>\n'%self.LogQueries)
            settings.writelines('    <beep_on_queries>%s</beep_on_queries>\n'%self.BeepOnQueries)
            settings.writelines('    <language>%s</language>\n' %self.Language)
            settings.writelines('    <webdir>%s</webdir>\n' %self.WebDir)
            settings.writelines('    <defaultcompany>%s</defaultcompany>\n' %self.DefaultCompany)
            level = 0
            Error = False
            for rline in self.Modules:
                if (len(rline.Directory.strip()) > 0):
                    if (not os.path.exists(rline.Directory)):
                        self.appendMessage("La ruta %s, no existe, verifique directorio" %os.path.realpath(rline.Directory))
                        rline.Enabled = False
                        Error = True
                    if (not rline.Enabled):
                        comment = "<!--"
                        comment2 = "-->"
                    else:
                        comment = ""
                        comment2 = ""

                    settings.writelines('    %s<scriptdir level="%s" path="%s" />%s\n' %(comment,level,rline.Directory,comment2))
                    level = level + 1
            settings.writelines('</settings>')
            settings.flush()
            settings.close()
            #setLanguage(self.Language)
            if (not Error):
                postMessage("Su archivo settings.xml fue actualizado con las opciones de la base de datos")
                #self.close()

    def sortCompanies(self, fieldname=""):
        fd = {}
        fd[tr("Code")] = "Code"
        fd[tr("Description")] = "Name"
        fd[tr("Database")] = "DBName"
        fd[tr("Host")] = "Host"

        if (fieldname):

            rowslist = []
            for crow in self.Companies:
                rowslist.append(crow)
            exec("rowslist.sort(cmp=lambda x,y: cmp(x.%s.lower(), y.%s.lower()) )" %(fd[fieldname],fd[fieldname]))
            
            
            self.Companies.clear()
            counter = 1
            for crow in rowslist:
                crow.internalId = counter
                self.Companies.append(crow)
                counter += 1

ParentSystemManagementModuleRow = SuperClass("SystemManagementModuleRow","Record",__file__)
class SystemManagementModuleRow(ParentSystemManagementModuleRow):
    pass

ParentSystemManagementCompanyRow = SuperClass("SystemManagementCompanyRow","Record",__file__)
class SystemManagementCompanyRow(ParentSystemManagementCompanyRow):
    pass

class XMLSettingsHandler(handler.ContentHandler):
    accumchar = ""

    def startElement(self, name, attrs):
        record = self.srecord
        if (name == "scriptdir"):
            srow = SystemManagementModuleRow()
            srow.Directory = "%s" %(attrs.get("path",""))
            srow.Level = "%s" %(attrs.get("level",""))
            srow.Enabled = True
            record.Modules.append(srow)

    def endElement(self, name):
        record = self.srecord
        if (name == "dbserver"):
            record.DbServer = self.accumchar
        elif (name == "skin"):
            record.Skin = self.accumchar
        elif (name == "logqueries"):
            if (self.accumchar.lower() == "true"):
                record.LogQueries = True
            else:
                record.LogQueries = False
        elif (name == "beep_on_queries"):
            if (self.accumchar.lower() == "true"):
                record.BeepOnQueries = True
            else:
                record.BeepOnQueries = False
        elif (name == "language"):
            record.Language = self.accumchar
        elif (name == "webdir"):
            record.WebDir = self.accumchar
        elif (name == "autosynctables"):
            record.AutoSyncTables = self.accumchar
        elif (name == "defaultcompany"):
            record.DefaultCompany = self.accumchar
        self.accumchar = ""

    def characters(self, chars):
        self.accumchar += ("%s" %(chars)).strip()

