# encoding: utf-8
from OpenOrange import *
from string import *
from GeneralTools import formatValue
from ReportTools import *
from Palette import *
from GlobalTools import *
import sys
import Web
from core.database.Database import DBError
from xml.sax import handler, saxutils
from DelayCleaner import DelayCleaner

def PythonReportToReport(*args):
    return args[0].toReport()

class Report(Embedded_Report, Palette):
    SCREENMODE = 0
    FILEMODE = 1
    WEBMODE = 2
    imageid = 1
    linecolor = False
    tablenames = [""] # A tablenames le asigno un valor vacio en la posicion 0 para se lo sume a tr y td cuando no estan en ninguna tabla.
    rowstyles = []
    efields,dfields,fieldLabels = [],[],{}
    Styles = {}

    DefaultReportImage = "reportopenlogo.png"

    ## Embeded methods ##
    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

    def __init__(self, *args):
        Embedded_Report.__init__(self)
        self.reportmode = Report.SCREENMODE
        self.fields = ""
        from Currency import Currency
        self.defaultdecimals = Currency.getRoundOff(Currency.getBase1())
        self._delaycleaner = DelayCleaner()

        self.Styles["A"] = (self.LevelABackColor,self.LevelAForeColor)
        self.Styles["B"] = (self.LevelBBackColor,self.LevelBForeColor)
        self.Styles["C"] = (self.LevelCBackColor,self.LevelCForeColor)
        self.Styles["D"] = (self.LevelDBackColor,self.LevelDForeColor)
        self.Styles["H"] = (self.HeaderBackColor,self.HeaderForeColor)
        self.Styles["I"] = (self.InvalidBackColor,self.InvalidForeColor)
        self.Styles["L"] = (self.LinkBackColor,self.LinkForeColor)

        from SystemSettings import SystemSettings
        sset = SystemSettings.bring()
        self.SystemDateFormat = sset.getDateFormat()

    def delayClean(self, *args):
        self._delaycleaner.appendObjects(*args)

    def __addString(self, v, insideTD, preVal, postVal, htmlclass=None):
        if not htmlclass:
            htmlclass = "tdString" + self.tablenames[-1]
        self.addHTML("<td class=\"%s\" %s>%s%s%s</td>\n" % (htmlclass ,insideTD , preVal, v, postVal))

    def __addInteger(self, v, insideTD, preVal, postVal, htmlclass=None):
        if not htmlclass:
            htmlclass = "tdInteger" + self.tablenames[-1]
        self.addHTML("<td class=\"%s\" %s>%s%s%s</td>\n" % (htmlclass, insideTD , preVal, v, postVal))

    def __addFloat(self, v, insideTD, preVal, postVal, precision=2, htmlclass=None):
        if not htmlclass:
            htmlclass = "tdFloat" + self.tablenames[-1]
        self.addHTML("<td class=\"%s\" align=right%s>%s%s%s</td>\n" % (htmlclass, insideTD , preVal, formatValue(v, precision), postVal))

    def name(self):
        return self.__class__.__name__

    def refresh(self, message=None):
        try:
            self.setTitle(tr("Calculating") + " " + self.getOriginalTitle() + "...")
            #processEvents() hace colgar open
        except:
            pass
        if not message:
            self.startNewDBTransaction()
            self.clear()
            self.run()
            self.render()
            self.logEvent()
        else:
            self.clear()
            self.addHTML(message)
            self.render()
            #processEvents() hace colgar open
            self.startNewDBTransaction()
            self.clear()
            self.run()
            self.render()
            self.logEvent()
        try:
            self.setTitle(self.getOriginalTitle())
        except:
            pass

    ## Report Methods ##
    def defaults(self):
        self.reportid = None #Web reports need this field
        self.ShowReportTitle = True
        record = self.getRecord()
        if record and record.hasField("FromDate"):
            record.FromDate = date(today().year, today().month, 1)
        if record and record.hasField("ToDate"):
            if today().month == 12:
                record.ToDate = addDays(date(today().year+1,1,1),-1)
            else:
                record.ToDate = addDays(date(today().year, today().month+1,1),-1)

    def afterDefaults_fromC(self):
        try:
            self.applyUserReportSpec()
            return True
        except DBError, e:
            processDBError(e, {}, utf8(e))

    def afterDefaults(self):
        self.applyUserReportSpec()

    def startNewDBTransaction(self):
        rollback() # para que inicie una nueva transaccion

    def beforeStartRun_fromC(self):
        try:
            self.beforeStartRun()
            return True
        except DBError, e:
            from functions import utf8
            processDBError(e, {}, uft8(e))
        return False

    def beforeStartRun(self):
        linecolor = False
        from SystemSettings import SystemSettings
        sset = SystemSettings.bring()
        if (sset.ShowEditingFieldName):
            sysprint("Running Report: %s" %(self.__class__.__name__))
        self.startNewDBTransaction()
        from User import User
        user = User.bring(currentUser())
        if user:
            try:
                if user.DefaultReportFontSize: self.setDefaultFontSize(user.DefaultReportFontSize)
            except:
                pass # temporal for linux and mac
        if not hasattr(self, "reportmode"): self.reportmode = Report.SCREENMODE
        self.report_outputfilename = self.getFileOutput()
        self.report_outputfile = None
        if self.report_outputfilename:
            self.reportmode = Report.FILEMODE
            try:
                import codecs
                self.report_outputfile = codecs.open(self.report_outputfilename, "w", "utf8")
            except:
                pass
        try:
            self.setTitle(tr("Calculating") + " " + self.getOriginalTitle() + "...")
            #processEvents() hace que se cuelgue open
        except:
            pass


    def runToExternalApp(self, format=None):
        import os
        import tempfile
        self.beforeStartRun()
        formats = {}
        formatList = []
        if (getPlatform() == "windows"):
            formats["xls"] = "Excel Sheet"
            formatList = ["xls","ods","ooreport","txt","pdf"]
        else:
            formatList = ["ods","ooreport","txt","pdf"]
        formats["txt"] = "Plain Text"
        formats["pdf"] = "PDF"
        formats["ods"] = "OpenOffice Sheet"
        formats["ooreport"] = "OpenOrange External Report"
        if (not format):
            ftype = getSelection(tr("Select Format"), tuple(["%s (%s)" %(tr(formats[x]),x) for x in formatList]))
            if not ftype: return
            import re
            ftype = re.compile(".* \(?(.*)\)").search(ftype).groups()[0]
            #for ff in formats.keys():
            #    if (ftype == "%s (%s)" %(tr(formats[ff]),ff)):
            #        ftype == ff
            #        break
        else:
            ftype = format
        if (format and not format in formats.keys()):
            return
        if ftype == "ooreport":
            filename= tempfile.NamedTemporaryFile().name + ".html"
        else:
            #filename = "%s_%s_%s.%s"   % (self.name(),today().strftime("%d-%m-%y"),now().strftime("%H-%M-%S"),ftype)
            filename = "%s.%s"   % (tempfile.NamedTemporaryFile(suffix="%s_%s_%s" % (self.name(),today().strftime("%d-%m-%y"),now().strftime("%H-%M-%S")), prefix='').name, ftype)
        import codecs
        self.report_outputfile = codecs.open(filename, 'w', "utf8")
        self.report_outputfilename = self.report_outputfile.name
        self.reportmode = Report.FILEMODE
        oldbases = self.__class__.__bases__
        try:
            if (ftype=="txt"):
               from TxtReport import TxtReport
               self.__class__.__bases__ = (TxtReport,)
               self.call_run()
            elif (ftype=="pdf"):
               from PdfReport import PdfReport
               self.__class__.__bases__ = (PdfReport,)
               self.call_run()
            #elif (ftype=="xls"):   #Replaced by Excel format
            #   from XlsReport import XlsReport
            #   self.__class__.__bases__ = (XlsReport,)
            #   self.call_run()
            elif (ftype=="ods" or ftype== "xls"):
                #from XlsReport import XlsReport
                #self.__class__.__bases__ = (XlsReport,)
                self.call_run()
                try:
                    self.setTitle(self.getOriginalTitle())
                except:
                    pass
                self.report_outputfile.close()
                try:
                    if (getPlatform() == "windows"):
                        os.startfile(self.report_outputfilename)
                    else:
                        os.system("oocalc %s>./tmp/error.log" %(self.report_outputfilename))
                except Exception, e:
                    mstring = "%s, (%s)" %(tr("OpenOrange Can't Open The Report in The External Application"),utf8(e))
                    message(mstring)
            elif (ftype=="ooreport"):
                self.call_run()
                try:
                    self.setTitle(self.getOriginalTitle())
                except:
                    pass
                try:
                    import subprocess
                    import sys
                    if sys.platform.startswith("win"):
                        subprocess.Popen(("OOReport.exe", self.getOriginalTitle(), self.report_outputfilename), shell=False);
                    elif sys.platform.startswith("linux"):
                        subprocess.Popen(("wine", "OOReport", self.getOriginalTitle(), self.report_outputfilename), shell=False);
                    #os.system('OOReport.exe "%s" "%s"' % (self.getOriginalTitle(), self.report_outputfilename))
                except Exception, e:
                    mstring = "%s, (%s)" %(tr("OpenOrange Can't Open The Report in The External Application"),utf8(e))
                    message(mstring)
                self.report_outputfile.close()
            self.close()
            self.report_outputfilename = None
        finally:
            self.__class__.__bases__ = oldbases

    def runToPDF(self):
        import os
        import tempfile
        self.beforeStartRun()
        tmpfile = tempfile.NamedTemporaryFile()
        import codecs
        self.report_outputfile = open(tmpfile.name + '.html', 'w', "utf8")
        self.report_outputfilename = self.report_outputfile.name
        self.reportmode = Report.FILEMODE
        self.call_run()
        try:
            self.setTitle(self.getOriginalTitle())
        except:
            pass
        self.report_outputfile.close()
        source = codecs.open(self.report_outputfilename, "rb", "utf8")
        tmpfile = tempfile.NamedTemporaryFile().name + '.pdf'
        pdf = convertHTMLToPDF("<html><body>"+source.read()+"</body></html>", ".")
        open(tmpfile, 'w').write(pdf)
        try:
            os.startfile(tmpfile)
        except:
            message("Open Orange can not open the report in the external application.")
        self.close()
        self.report_outputfilename = None

    def call_run(self):
        try:
            self.startReport()
            self.run()
            self._delaycleaner.clean()
            self.endReport()
            return True
        except AppException, e:
            message(e)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            processUnexpectedError(e)
        return False

    def afterFinishRun_fromC(self):
        try:
            self.afterFinishRun()
            return True
        except DBError, e:
            processDBError(e, {}, utf8(e))
        return False

    def startReport(self):
        """ Things to be done at the start of the report before starting writing to the file """
        pass

    def endReport(self):
        """ Things to be done at the end of the report before closing the file """
        pass

    def afterFinishRun(self):
        try:
            self.setTitle(self.getOriginalTitle())
        except:
            pass
        if self.report_outputfile:
            self.report_outputfile.close()
            if self.report_outputfilename:
                res = getSelection("Informe terminado. Desea abrirlo en el navegador?", ("SI", "NO"))
                if res == "SI":
                    try:
                        import webbrowser
                        webbrowser.open(self.report_outputfilename)
                    except:
                        message("OpenOrange can not open web browser.")
            #self.close()
        self.report_outputfilename = None
        self.logEvent()

    def __reduce__(self):
        from PythonReport import PythonReport
        return (PythonReportToReport, (PythonReport(self),))

    def logEvent(self):
        if self.name() != "EventLog":
            from EventLog import EventLog
            eventlog = EventLog()
            eventlog.TableName = self.name()
            eventlog.Action = 3 #report run
            eventlog.TransDate = today()
            eventlog.TransTime = now()
            eventlog.User = currentUser()
            from LogSettings import LogSettings
            ls = LogSettings.bring()
            if ls.shouldLogReportEvents(self.name()):            
                eventlog.Data = cPickle.dumps(self)
            res = eventlog.store()
            if res:
                commit()



    def sendByMail(self):
        record = self.getRecord()
        from MailWindow import MailWindow
        from Mail import Mail
        import StringIO
        self.beforeStartRun()
        self.report_outputfile = StringIO.StringIO()
        self.reportmode = Report.FILEMODE
        self.run()
        messagebody = utf8(self.report_outputfile.getvalue())
        self.report_outputfile = None #very important... dont now why.
        self.reportmode = Report.SCREENMODE # ver si esto funciona... sino hacer un close del report.
        self.afterFinishRun()
        mail = Mail()
        mail.defaults()
        if record.hasField("CustCode"):
            mail.EntityType = 0
            mail.CustCode = record.CustCode
            mail.pasteCustCode()
        elif record.hasField("SupCode"):
            mail.EntityType = 1
            mail.CustCode = record.SupCode
            mail.pasteCustCode()
        if record.hasField("Contact"):
            from Person import Person
            pers = Person.bring(record.Contact)
            if pers and pers.Email:
                mail.MailTo = pers.getMail()
        #se guarda para poder incluir imagenes
        res = mail.save()
        commit()
        mail.importHTML(messagebody ,True)
        res = mail.save()
        commit()
        if not res:
            rollback()
        window = MailWindow()
        window.setRecord(mail)
        window.open()

    def pageHeader(self):
        pass

    ## Report Name and Filters Methods ##
    def startFilterHeader(self):
        self.startTable()
        self.startHeaderRow()

    def endFilterHeader(self):
        self.endHeaderRow()
        self.addHTML("<hr/>")
        self.endTable()

    def printReportName(self, reportname=None, htmlclass=None, image=None, RowSpan=None):
        if reportname is None:
            reportname = self.getLabel()
        if htmlclass is None:
            self.startTable()
        else:
            self.startTable(htmlclass=htmlclass)
        if image is None:
            image = self.DefaultReportImage
        self.startHeaderRow()
        if RowSpan is None:
            self.addImage(image,BGColor=self.DefaultBackColor)
        else:
            self.addImage(image,BGColor=self.DefaultBackColor, RowSpan=RowSpan)
        self.addValue(tr(reportname),Bold=True,Size=5,BGColor=self.DefaultBackColor,Color=self.ReportTitleColor,Align="left")
        self.endHeaderRow()
        self.endTable()

    def printReportTitle(self, reportname=None):
        if not hasattr(self, "ShowReportTitle") or self.ShowReportTitle:
            if reportname is None:
                reportname = self.getLabel()
            self.startTable(Width="100%")
            self.startRow(BGColor=self.DefaultBackColor)
            self.startCell()
            self.printReportName(reportname)
            self.endCell()
            self.startCell(Align="right")
            self.startTable()
            self.printHeaderCompanyData()
            self.endTable()
            self.endCell()
            self.endRow()
            self.endTable()
            he = not self.isHeaderEnabled() # Esto tiene que cambiarse desde C para que no haga falta el if not
            from SystemSettings import SystemSettings
            sset = SystemSettings.bring()
            if (sset.NoReportHeaderAsDefault):
                he = self.isHeaderEnabled()
            if he:
                self.printFilterHeader()

        self.startTable()
        self.startRow(BGColor=self.DefaultBackColor)
        self.addValue("")
        self.endRow()
        self.endTable()

        #self.addHTML("<TABLE width=100% border=1>")
        #self.addHTML(" <TR>")
        #self.addHTML("  <TD>")
        #self.addHTML("  </TD>")
        #self.addHTML("  <TD RowSpan=2>")
        #self.printHeaderCompanyData()
        #self.addHTML("  </TD>")
        #self.addHTML(" </TR>")
        #self.addHTML(" <TR>")
        #self.addHTML("  <TD>")
        #self.addHTML("  </TD>")
        #self.addHTML(" </TR>")
        #self.addHTML("</TABLE>")
        #self.startTable()
        #self.endTable()

    def printHeaderCompanyData(self):
        from OurSettings import OurSettings
        our = OurSettings.bring()
        time = today()
        hour = now()
        self.startRow(BGColor=self.DefaultBackColor)
        self.addValue(tr("Company Name")+": %s" %our.Name,Size=2,Align="right")
        self.endRow()
        self.startRow(BGColor=self.DefaultBackColor)
        self.addValue(tr("Emision Date")+": %s / %s: %s" %(time.strftime(self.SystemDateFormat),tr("Time"),hour.strftime ("%H:%M:%S")),Size=2,Align="right")
        self.endRow()
        self.startRow(BGColor=self.DefaultBackColor)
        if (self.reportmode == Report.WEBMODE):
            self.addValue("Powered by OpenOrange",Size=2,Align="right")
        else:
            from Office import Office
            self.addValue("%s: %s, %s: %s" % (tr("Office"),Office.default(),tr("Printed by"),currentUser()) ,Size=2,Align="right")
        self.endRow()

    def convertDate(self, cdate):
        if (str(cdate) == "0000-00-00"):
            return "00/00/0000"
        return cdate.strftime(self.SystemDateFormat)

    def printFilterHeader(self):
        self.startTable()
        record = self.getRecord()
        if record:
            fieldsdata = self.getWindowFieldsData()
            from SystemSettings import SystemSettings
            ss = SystemSettings.bring()
            if ss.ReportHeaderDescriptionsFlag:
                for fd in fieldsdata:
                    f = record.fields(fd)
                    if f and f.getLinkTo() and f.getValue():
                        lk = NewRecord(f.getLinkTo())
                        linked_record = lk.bring(f.getValue())
                        for desc_fn in ("Name", "Description", "Comment"):
                            if hasattr(linked_record, desc_fn):
                                lab = getattr(linked_record, desc_fn)
                                break
                        if lab:
                            fieldsdata[fd]["Description"] = lab
            self.startRow(BGColor=self.DefaultBackColor)
            col2 = False
            for field in fieldsdata["ListOfIndexedFields"]:
                if (not col2):
                    self.startRow()
                if (fieldsdata[field]["Type"] in ("text") ):
                    if fieldsdata[field].has_key("Description"):
                        value = fieldsdata[field]["Description"]
                    else:
                        value = record.fields(field).getValue()
                    if (value):
                        self.addValue("%s: %s" % (fieldsdata[field]["Label"],value))
                        col2 = not col2
                elif (fieldsdata[field]["Type"] in ("date") ):
                    value = self.convertDate(record.fields(field).getValue())
                    if (value):
                        self.addValue("%s: %s" % (fieldsdata[field]["Label"],value),CallMethod="changeFilterDate",Parameter="%s" %(field))
                        col2 = not col2
                elif (fieldsdata[field]["Type"] in ("time") ):
                    value = record.fields(field).getValue().strftime("%H:%M")
                    if (value):
                        self.addValue("%s: %s" % (fieldsdata[field]["Label"],value),CallMethod="changeFilterTime",Parameter="%s" %(field))
                        col2 = not col2
                elif (fieldsdata[field]["Type"] == "period"):
                    fromdate = self.convertDate(record.fields(fieldsdata[field]["FromDate"]).getValue())
                    todate = self.convertDate(record.fields(fieldsdata[field]["ToDate"]).getValue())
                    self.addValue("%s: %s - %s" % (fieldsdata[field]["Label"],fromdate,todate),CallMethod="changeFilterPeriod",Parameter="%s,%s" %(fieldsdata[field]["FromDate"],fieldsdata[field]["ToDate"]))
                    col2 = not col2
                elif (fieldsdata[field]["Type"] == "checkbox"):
                    value = record.fields(field).getValue()
                    option = [tr("No"),tr("Yes")]
                    self.addValue("%s: %s" % (fieldsdata[field]["Label"],option[value]),CallMethod="toogleFilterCheckBox",Parameter="%s" %(field))
                    col2 = not col2
                elif (fieldsdata[field]["Type"] == "options"):
                    value = utf8(record.fields(field).getValue())
                    if (value in fieldsdata[field]["OptionValues"]):     # sometimes checkboxes or combos dont have the 0 value option and this generate and error
                        idx = fieldsdata[field]["OptionValues"].index(value)
                        label = fieldsdata[field]["OptionLabels"][idx]
                        self.addValue("%s: %s" % (fieldsdata[field]["Label"],label),CallMethod="toogleFilterOptions",Parameter="%s" %(field))
                        col2 = not col2
                else:
                    self.addValue("%s" % (fieldsdata[field]["Label"]))
                    col2 = not col2
                if (not col2):
                    self.endRow()
        self.endTable()

    def changeFilterDate(self, param, value):
        record = self.getRecord()
        fieldsdata = self.getWindowFieldsData()
        label = fieldsdata[param]["Label"]
        res = getString(label)
        if (res):
            res = stringToDate(res)
            if (res):
                record.fields(param).setValue(res)
            else:
                return
        self.refresh()

    def changeFilterTime(self, param, value):
        record = self.getRecord()
        fieldsdata = self.getWindowFieldsData()
        label = fieldsdata[param]["Label"]
        res = getString(label)
        if (res):
            record.fields(param).setValue(res)
        self.refresh()

    def changeFilterPeriod(self, param, value):
        fromdate, todate = param.split(",")
        record = self.getRecord()
        res = getString(tr("From Date"))
        if (res):
            res = stringToDate(res)
            if (res):
                record.fields(fromdate).setValue(res)
            else:
                return

        res = getString(tr("To Date"))
        if (res):
            res = stringToDate(res)
            if (res):
                record.fields(todate).setValue(res)
            else:
                return
        self.refresh()

    def toogleFilterOptions(self, param, value):
        fieldsdata = self.getWindowFieldsData()
        label = fieldsdata[param]["Label"]
        res = getSelection(label, tuple(fieldsdata[param]["OptionLabels"]))
        if (res):
            idx = fieldsdata[param]["OptionLabels"].index(res)
            value = fieldsdata[param]["OptionValues"][idx]
            record = self.getRecord()
            record.fields(param).setValue(value)
            self.refresh()

    def toogleFilterCheckBox(self, param, value):
        record = self.getRecord()
        value = record.fields(param).getValue()
        record.fields(param).setValue(not value)
        self.refresh()

    def printFilterLine(self, headertext, fieldname):
        record = self.getRecord()
        if (not record.fields(fieldname).isNone()):
            self.startRow()
            if (record.fields(fieldname).__class__.__name__ == "date"):
                self.addValue("%s: " %tr(headertext),Bold=True)
                self.addValue(record.fields(fieldname).getValue().strftime(self.SystemDateFormat))
            else:
                if (record.fields(fieldname).getValue()):
                    self.addValue("%s: " %tr(headertext),Bold=True)
                    self.addValue(record.fields(fieldname).getValue())
            self.endRow()

    def printFilterText(self, text):
        self.startTable()
        self.startRow()
        self.addValue(tr(text),Bold=True)
        self.endRow()
        self.endTable()

    def printFilterPeriod(self, headertext):
        record = self.getRecord()
        if (not record.fields("FromDate").isNone() ) or (not record.fields("ToDate").isNone):
            self.endTable()
            self.startTable()
            self.startRow()
            self.addValue("%s: " %tr(headertext),Bold=True)
            self.addValue(record.FromDate)
            self.addValue(record.ToDate)
            self.endRow()
            self.endTable()
            self.startTable()

    def printFilterOption(self, headertext, fieldname, optionlist):
        record = self.getRecord()
        self.startRow()
        self.addValue(tr(headertext),Bold=True)
        self.addValue(tr(optionlist[record.fields(fieldname).getValue()]) )
        self.endRow()

    def showHelp(self):
        from OpenOrangeHelpCenter import OpenOrangeHelpCenter
        oohc = OpenOrangeHelpCenter()
        oohc.viewMode = "index"
        oohc.open(False)

    def SQLRangeFilter(self,TableName,FieldName,Value):
        if not Value: return ""
        setList = [x.strip() for x in Value.split(",")]
        # soporta: 1,3,10:11,4:22:
        qstr = ""
        inList = []
        #AGREGO ESTO PORQUE PUEDE SER LLAMADO DESDE TRANSFILTER SIN EL ALIAS DE LA TABLA
        if (TableName):
            TableName = "[%s]."%TableName
        if len(setList) == 1 and Value:   # only added for speed & readability considerations
            if (":" in Value):
                fv,tv = Value.split(":")
                return "WHERE?AND (%s{%s} BETWEEN s|%s| AND s|%s|) "  % (TableName, FieldName, fv,tv)
            else:
                return "WHERE?AND %s{%s} = s|%s| "  % (TableName, FieldName, Value)
        for set in setList:
            range = [x.strip() for x in set.split(":")]
            if len(range) == 2:
                if not range[0] and range[1]:
                    qstr += "OR ( %s{%s} <= s|%s| ) " % (TableName, FieldName, range[1])
                elif not range[1] and range[0]:
                    qstr += "OR ( %s{%s} >= s|%s| ) " % (TableName, FieldName, range[0])
                elif (range[0] and range[1]):
                    qstr += "OR ( %s{%s} BETWEEN s|%s| AND s|%s| ) " % (TableName, FieldName, range[0],range[1])
            else:
                if set: inList.append(set)
        if (len(inList) > 0):
            qstr += "OR ( %s{%s} in (%s) ) " % (TableName, FieldName, ','.join(["s|%s|" % x for x in inList]))
        if (qstr):
            qstr = "WHERE?AND (%s) "%qstr[2:]
        return qstr

    def listDictionary(self,dicc,table):
        sumar = lambda a,b: a + b
        exec("from %s import %s" % (table,table))
        exec("codeNames = %s.getNames()" % table)
        self.startTable()
        self.header(tr(table)+" "+tr("Statistics"))
        self.header("Value","Name","Qty","Percentage")
        tot = reduce(sumar,dicc.values())
        for gkey in dicc.keys():
            per = 0.0
            if tot: per = (dicc[gkey] * 100.0/tot)
            self.startRow()
            self.addValue(gkey)
            self.addValue(codeNames.get(gkey,""))
            self.addValue(dicc[gkey])
            self.addValue(per)
            self.endRow()
        self.endTable()

    ## Content Methods ##
    def startTable(self, *vargs, **kwargs):
        if kwargs.has_key("htmlclass"):
            htmlclass = kwargs["htmlclass"]
        else:
            htmlclass = "table"
        self.tablenames.append(htmlclass)
        insideTD = ""
        if kwargs.has_key("BGColor"):
            insideTD += " bgcolor=%s" % kwargs["BGColor"]
        if kwargs.has_key("Border"):
            insideTD += " border=%s" % kwargs["Border"]
        if kwargs.has_key("Width"):
            insideTD += " width=%s" % kwargs["Width"]
        if kwargs.has_key("Height"):
            insideTD += " height=%s" % kwargs["Height"]
        if kwargs.has_key("Align"):
            insideTD += " align=%s" % kwargs["Align"]
        if kwargs.has_key("CellSpacing"):
            insideTD += " cellspacing=%s" % kwargs["CellSpacing"]
        if kwargs.has_key("CellPadding"):
            insideTD += " cellpadding=%s" % kwargs["CellPadding"]
        self.addHTML("<table class=\"%s\"%s>\n" % (htmlclass, insideTD))


    def endTable(self):
        self.addHTML("</table>\n")
        if len(self.tablenames) > 0:
            self.tablenames.pop()

    def startRow(self, *vargs, **kwargs):
        from SystemSettings import SystemSettings
        if kwargs.has_key("htmlclass"):
            htmlclass = kwargs["htmlclass"]
        elif self.tablenames:
            htmlclass = "tr" + self.tablenames[-1]
        else:
            htmlclass = "tr"
        insideTD = ""
        sColor = kwargs.get("Style",None)
        bColor = kwargs.get("BGColor",None)
        fColor = kwargs.get("Color",None)
        self.startRowStyle(sColor,bColor,fColor)
        if kwargs.has_key("BGColor"):
            insideTD += " bgcolor=%s" % bColor
        #sysprint("start "+str(self.rowstyles))
        self.addHTML("<tr class=\"%s\" %s>\n" % (htmlclass, insideTD))

    def endRow(self):
        self.addHTML("</tr>\n")
        self.endRowStyle()
        #sysprint("end "+str(self.rowstyles))

    def blankRow(self):
        self.startRow()
        self.addValue("",BGColor=self.DefaultBackColor)
        self.endRow()

    def startCell(self, *vargs, **kwargs):
        if kwargs.has_key("htmlclass"):
            htmlclass = kwargs["htmlclass"]
        else:
            htmlclass = "td"
        insideTD = ""
        if kwargs.has_key("BGColor"):
            insideTD += " bgcolor=%s" % kwargs["BGColor"]
        if kwargs.has_key("RowSpan"):
            insideTD += " rowspan=%s" % kwargs["RowSpan"]
        if kwargs.has_key("ColSpan"):
            insideTD += " colspan=%s" % kwargs["ColSpan"]
        if kwargs.has_key("Align"):
            insideTD += " align=%s" % kwargs["Align"]
        self.addHTML("<td class=\"%s\" %s>" %(htmlclass, insideTD))

    def endCell(self):
        self.addHTML("</td>\n")

    def header(self, *vargs):
        self.startHeaderRow()
        for arg in vargs:
            self.addValue(tr(arg))
        self.endHeaderRow()

    def headerA(self, *vargs):
        self.startHeaderRow()
        for arg in vargs:
            self.addValue(tr(arg),Color=self.LevelAForeColor,BGColor=self.LevelABackColor)
        self.endHeaderRow()

    def headerB(self, *vargs):
        self.startHeaderRow()
        for arg in vargs:
            self.addValue(tr(arg),Color=self.LevelBForeColor,BGColor=self.LevelBBackColor)
        self.endHeaderRow()

    def headerC(self, *vargs):
        self.startHeaderRow()
        for arg in vargs:
            self.addValue(tr(arg),Color=self.LevelCForeColor,BGColor=self.LevelCBackColor)
        self.endHeaderRow()

    def headerD(self, *vargs):
        self.startHeaderRow()
        for arg in vargs:
            self.addValue(tr(arg),Color=self.LevelDForeColor,BGColor=self.LevelDBackColor)
        self.endHeaderRow()

    def row(self, *vargs):
        self.startRow()
        for arg in vargs:
            self.addValue(arg)
        self.endRow()

    def startHeaderRow(self, htmlclass=None):
        if not htmlclass:
            htmlclass = "trHeaderRow"
        self.startRowStyle("H")
        self.addHTML("<tr class=\"%s\"> \n" %(htmlclass))
        #sysprint("start "+str(self.rowstyles))
        self.inRow = True

    def endHeaderRow(self):
        self.addHTML("</tr>\n")
        self.endRowStyle()
        #sysprint("end "+str(self.rowstyles))

    def addHTML(self,v):
        if (self.reportmode == Report.WEBMODE):
            print v
        else:
            if self.reportmode == Report.FILEMODE:
                self.report_outputfile.write(v)
            else:
                Embedded_Report.addHTML(self, v)

    def getDefaultDecimals(self):
        return self.defaultdecimals

    def setDefaultDecimals(self, d):
        self.defaultdecimals = d

    def addImage(self, v, **kwargs):
        if kwargs.has_key("htmlclass"):
            htmlclass = kwargs["htmlclass"]
        else:
            htmlclass = "td" + self.tablenames[-1]
        if self.reportmode != Report.WEBMODE:
            imgpath = getImagePath(v)
        else:
            imgpath = "../img/" + v
        insideTD = ""
        imgparams = ""
        if kwargs.has_key("BGColor"):
            insideTD += " bgcolor=%s" % kwargs["BGColor"]
        if kwargs.has_key("ColSpan"):
            insideTD += " colspan=%s" % kwargs["ColSpan"]
        if kwargs.has_key("RowSpan"):
            insideTD += " rowspan=%s" % kwargs["RowSpan"]
        if kwargs.has_key("Align"):
            insideTD += ' align="%s"' % kwargs["Align"]
        if kwargs.has_key("VAlign"):
            insideTD += " valign=%s" % kwargs["VAlign"]
        if kwargs.has_key("CellWidth"):
            insideTD += " width=%s" % kwargs["CellWidth"]
        if kwargs.has_key("CellHeight"):
            insideTD += " height=%s" % kwargs["CellHeight"]
        if kwargs.has_key("Width"):
            imgparams += ' width="%s"' % kwargs["Width"]
            #insideTD += " width=%s" % kwargs["Width"]
        if kwargs.has_key("Height"):
            imgparams += ' height="%s"' % kwargs["Height"]
        if kwargs.has_key("VSpace"):
            imgparams += ' vspace="%s"' % kwargs["VSpace"]
        if kwargs.has_key("HSpace"):
            imgparams += ' hspace="%s"' % kwargs["HSpace"]
        preVal = ""
        postVal = ""
        if kwargs.has_key("CallMethod"):
            if kwargs.has_key("Parameter"):
                param = utf8(kwargs["Parameter"])
                param = param.replace(" ", "!#%%$!")
                param = param.replace("\t", "!%#%$!")
                vx = v
                if isinstance(vx, str):
                    vx = v.replace(" ", "!#%%$!");
                    vx = vx.replace("\t", "!%#%$!");
                if self.reportmode != Report.WEBMODE:
                    preVal += "<a name=""!cmp|%s|%s|%s"">" % (kwargs["CallMethod"], param,vx)
                else:
                    preVal += "<a href=\"\" onclick=\"callMethodParam('%s', '%s', '%s', '%s', '%s'); return false;\">" % (self.session.getId(), self.reportid, kwargs["CallMethod"], utf8(param),utf8(v))
                postVal += "</a>"
            else:
                if self.reportmode != Report.WEBMODE:
                    vx = v
                    if isinstance(vx, str):
                        vx = v.replace(" ", "!#%%$!");
                        vx = vx.replace("\t", "!%#%$!");
                    preVal += "<a name=""!cm|%s|%s""><u>" % (kwargs["CallMethod"], vx)
                else:
                    preVal += "<a href=\"\" onclick=\"callMethod('%s', '%s', '%s', '%s'); return false;\">" % (self.session.getId(), self.reportid, kwargs["CallMethod"], utf8(v))
                postVal += "</u></a>"

        self.addHTML("<td class=\"%s\" %s>%s<img src=""%s"" %s/>%s</td>\n" % (htmlclass, insideTD, preVal, imgpath, imgparams, postVal))

    def addValue(self, v, *vargs, **kwargs):
        from SystemSettings import SystemSettings
        if kwargs.has_key("htmlclass"):
            htmlclass = kwargs["htmlclass"]
        else:
            htmlclass = "td"
        insideTD = ""
        preVal= ""
        postVal = ""

        if (self.reportmode == self.WEBMODE) and (kwargs.has_key("WebLink")) :
            preVal= '<a href="%s">' % kwargs["WebLink"]
            postVal = "</a>"

        if (kwargs.get("Invalid",0) == 1):
            kwargs["Style"] = "I"

        if (kwargs.has_key("Style")):
            bColor,fColor = self.getStyleColors(kwargs.get("Style",""))
            kwargs["BGColor"] = kwargs.get("BGColor",bColor)
            kwargs["Color"] = kwargs.get("Color",fColor)
        else:
            bColor,fColor = self.getRowStyle()
            kwargs["BGColor"] = kwargs.get("BGColor",bColor)
            kwargs["Color"] = kwargs.get("Color",fColor)

        if kwargs.has_key("Window") and kwargs.has_key("FieldName"):
            if self.reportmode != Report.WEBMODE:
                if kwargs.has_key("Underline") and (kwargs["Underline"] == False):
                  preVal += "<a name=""!orw|%s|%s|%s"">" % (kwargs["Window"], kwargs["FieldName"], v)
                else:
                  preVal += "<a name=""!orw|%s|%s|%s""><u>" % (kwargs["Window"], kwargs["FieldName"], v)
            elif self.reportmode == Report.WEBMODE:
                preVal += "<a href=\"window.py?windowname=%s&_field_%s=%s&__sessionid__=%s\" target=\"_blank\"><u>" % (kwargs["Window"], kwargs["FieldName"], utf8(v), self.session.getId())
            if kwargs.has_key("Underline") and (kwargs["Underline"] == False):
                postVal += "</a>"
            else:
                postVal += "</u></a>"
        elif kwargs.has_key("CallMethod"):
            if kwargs.has_key("Parameter"):
                param = utf8(kwargs["Parameter"]);
                param = param.replace(" ", "!#%%$!");
                param = param.replace("\t", "!%#%$!");
                vx = v
                if isinstance(vx, str):
                    vx = v.replace(" ", "!#%%$!");
                    vx = vx.replace("\t", "!%#%$!");
                if self.reportmode != Report.WEBMODE:
                    try:
                        preVal += "<a name=""!cmp|%s|%s|%s"">" % (kwargs["CallMethod"],param,vx)
                    except UnicodeDecodeError, e:
                        preVal += "<a name=""!cmp|%s|%s|%s"">" % (kwargs["CallMethod"],utf8(param),vx)                    
                else:
                    preVal += "<a href=\"\" onclick=\"callMethodParam('%s', '%s', '%s', '%s', '%s'); return false;\">" % (self.session.getId(), self.reportid, kwargs["CallMethod"], utf8(param),utf8(v))
                postVal += "</a>"
            else:
                if self.reportmode != Report.WEBMODE:
                    vx = v
                    if isinstance(vx, str):
                        vx = v.replace(" ", "!#%%$!");
                        vx = vx.replace("\t", "!%#%$!");
                    preVal += "<a name=""!cm|%s|%s""><u>" % (kwargs["CallMethod"], vx)
                else:
                    preVal += "<a href=\"\" onclick=\"callMethod('%s', '%s', '%s', '%s'); return false;\">" % (self.session.getId(), self.reportid, kwargs["CallMethod"], utf8(v))
                postVal += "</u></a>"

        if kwargs.has_key("Color") or kwargs.has_key("Size"):
            color = ""
            size = ""
            if kwargs.has_key("Color"): color = "color="+kwargs["Color"]
            if kwargs.has_key("Size"): size = "size=%s" % kwargs["Size"]
            preVal += "<font class=\"%s\" %s %s>" % (htmlclass, color, size)
            postVal += "</font>"

        if kwargs.has_key("Wrap") and not kwargs["Wrap"]:
            preVal += "<nobr>"
            postVal += "</nobr>"

        if kwargs.has_key("Bold"):
            if (kwargs["Bold"] == True):
                preVal += "<b>"
                postVal += "</b>"

        if kwargs.has_key("Italic"):
            if (kwargs["Italic"] == True):
                preVal += "<i>"
                postVal += "</i>"

        if kwargs.has_key("Underline"):
            if (kwargs["Underline"] == True):
                preVal += "<u>"
                postVal += "</u>"

        if kwargs.has_key("Width"):
            insideTD += " width='%s'" % kwargs["Width"]

        if kwargs.has_key("Height"):
            insideTD += " height='%s'" % kwargs["Height"]

        if kwargs.has_key("Align"):
            insideTD += " align=%s" % kwargs["Align"]

        if kwargs.has_key("VAlign"):
            insideTD += " valign=%s" % kwargs["VAlign"]

        if kwargs.has_key("Border"):
            insideTD += " border=%s" % kwargs["Border"]

        if kwargs.has_key("BGColor"):
            insideTD += " bgcolor=%s" % kwargs["BGColor"]

        if kwargs.has_key("FontFamily"):
            insideTD += " style='font-family:%s'" % kwargs["FontFamily"]

        if kwargs.has_key("RowSpan"):
            insideTD += " rowspan=%s" % kwargs["RowSpan"]
        if kwargs.has_key("ColSpan"):
            insideTD += " colspan=%s" % kwargs["ColSpan"]
        if v is None:
           self.__addString("",insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,unicode):
            self.__addString(v,insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,str):
            self.__addString(v,insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,int):
            self.__addInteger(v,insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,float):
            decimals = self.defaultdecimals
            if kwargs.get("Currency", None):
                from Currency import Currency
                currency = Currency.bring(kwargs["Currency"])
                if currency:
                    decimals = currency.RoundOff
            decimals = kwargs.get("Decimals", decimals)                                    
            self.__addFloat(v,insideTD, preVal, postVal, decimals, htmlclass)
        elif isinstance(v,date):
            if v.year >= 1900:
                self.__addString(v.strftime(self.SystemDateFormat), insideTD, preVal, postVal, htmlclass)
            else:
                self.__addString("", insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,bool):
            if v:
                self.__addInteger(1,insideTD, preVal, postVal, htmlclass)
            else:
                self.__addInteger(0,insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,time):
            self.__addString("%s:%s" %(utf8(v.hour).rjust(2,"0"),utf8(v.minute).rjust(2,"0")),insideTD, preVal, postVal, htmlclass)
        elif isinstance(v,datetime):
            self.__addString("%s:%s" %(utf8(v.hour).rjust(2,"0"),utf8(v.minute).rjust(2,"0")),insideTD, preVal, postVal, htmlclass)
        if isinstance(v,EmbeddedImage):
            import tempfile
            filename= tempfile.NamedTemporaryFile().name + ".png"
            v.save(filename)
            self.addImageLink("%s" % Report.imageid, filename)
            if self.reportmode != Report.SCREENMODE:
                self.__addString("<img src=\"%s\">" % filename,insideTD, preVal, postVal, htmlclass)
            else:
                self.__addString("<img src=\"%s\">" % (Report.imageid),insideTD, preVal, postVal, htmlclass)
            #import os
            #os.remove("tmp.png")
            Report.imageid += 1
        if isinstance(v,Image.Image):
            try:
                v.save("tmp.png")
                self.addImageLink("%s" % Report.imageid, "tmp.png")
                self.__addString("<img src=\"%s\">" % (Report.imageid) ,insideTD, preVal, postVal, htmlclass)
                import os
                os.remove("tmp.png")
                Report.imageid += 1
            except Exception, e:
                #catching interlaced error from PIL library
                if utf8(e).lower().find("interlaced") >= 0:
                    self.addValue("Image Error: " + utf8(e))
                else:
                    raise

    def ReportHeader(self,Title,FromDate,ToDate):
        from OurSettings import OurSettings
        os = OurSettings()
        os.load()
        if not hasattr(self,"pageNr"):
            self.pageNr = 1
        else:
            self.pageNr += 1
        self.startTable()
        self.headerB("%s "  % os.Name)
        hstr = "%s, " % (Title)
        hstr += tr("Generation Date") + ": %s, " % today().strftime(self.SystemDateFormat)
        hstr += tr("Page") + " %d" % (self.pageNr)
        self.headerB(hstr)
        if (FromDate != ToDate):
           self.headerB(tr("From") + ": " + FromDate.strftime(self.SystemDateFormat)  + " " + tr("To") + ": " + ToDate.strftime(self.SystemDateFormat))
        else:
           self.headerB(tr("To Date") + ": " +  ToDate.strftime(self.SystemDateFormat))
        self.endTable()
        self.addHTML("<hr/>")
        self.startTable()
        self.row(" ")
        self.endTable()

    def transFilterNew(self, record, **args):
        return self.transFilter(record, **args)

    #########################################################################
    #   Este metodo reemplazará al TransFilter actual. Este es genérico.
    #########################################################################
    def transFilter(self, record, **args):
        filterinfo = {}
        for alias in args.keys():
            if (not alias in filterinfo.keys()):
                filterinfo[alias] = {}
            for fname in args[alias]:
                if (isinstance(fname,str)):
                    if (fname in record.fieldNames()):
                        filterinfo[alias][fname] = record.fields(fname).getValue()
                    else:
                        filterinfo[alias][fname] = ""
                if (isinstance(fname,dict)):
                    filterinfo[alias][fname.keys()[0]] = fname.values()[0]
        whereand = "WHERE "
        qstring = ""
        #alert(filterinfo)
        for alias in filterinfo.keys():
            for fname in filterinfo[alias].keys():
                fvalue = filterinfo[alias][fname]
                if (fname == "TransDate"):
                    fromdate  = record.fields("FromDate").getValue()
                    todate    = record.fields("ToDate").getValue()
                    if ("DateType" in record.fieldNames()):
                        datetype = record.fields("DateType").getValue()
                    else:
                        datetype = "TransDate"
                    if (fname == "TransDate"):
                        qstring += "%s (%s.%s BETWEEN d|%s| AND d|%s|) " %(whereand,alias,datetype,fromdate, todate)
                        whereand = "AND "
                elif (fname == "TransTime"):
                    starttime = record.fields("StartTime").getValue()
                    endtime   = record.fields("EndTime").getValue()
                    if (fname == "TransTime" and record.UseTimeFilter):
                        qstring += "%s (%s.TransTime BETWEEN t|%s| AND t|%s|) " %(whereand,alias, starttime, endtime)
                        whereand = "AND "
                elif (fname in ("Status","Invalid","Closed")):
                    if (fvalue != 2):
                        qstring += "%s (IFNULL(%s.%s,0) = i|%s|) " %(whereand, alias, fname, fvalue)
                        whereand = "AND "
                else:
                    if (not fvalue):
                        continue
                    if (isinstance(fvalue,int)):
                        fvalue = utf8(fvalue)
                        if ("," in fvalue):
                            qstring += "%s (IFNULL(%s.%s,0) in (%s)) " %(whereand,alias,fname,",".join(fvalue.split(",")))
                            whereand = "AND "
                        else:
                            qstring += "%s (IFNULL(%s.%s,0) = i|%s|) " %(whereand,alias,fname,fvalue)
                            whereand = "AND "
                    else:
                        if ("," in fvalue):
                            qstring += "%s (IFNULL(%s.%s,'') in ('%s')) " %(whereand,alias,fname,"','".join(fvalue.split(",")))
                            whereand = "AND "
                        else:
                            qstring += "%s (IFNULL(%s.%s,'') = s|%s|) " %(whereand,alias,fname,fvalue)
                            whereand = "AND "
        return qstring

    ## Other methods ##
    #POR FAVOR NO CAMBIAR LA CABECERA DEL METODO, AVISAR ANTES A MSP
    def TransFilter(self,FromDate,ToDate,Status,Office,Shift,ShiftNr,User,Computer,alias="",DateType="TransDate"):
        """ Filter should be used on all transaction reports """
        tablename = ""
        if (alias):
            tablename = "[%s]." %alias
        qstr = "WHERE?AND ( %s{%s} BETWEEN d|%s| AND d|%s| ) " % (tablename,DateType,FromDate,ToDate)      # always used therefore : where
        if (Status == 1):
           finalset = getFinalStatus(tablename)
           fset = "%s" %(finalset)
           if len(finalset)==1: fset = "(%s)" % finalset[0]   # SQL cannot handle pythonlists like (1,)
           qstr += " WHERE?AND %s{Status} IN %s " % (tablename,fset)
        elif (Status==2):
           pass #both
        elif (Status==0):                #
           qstr += " WHERE?AND %s{Status}=i|0| " %tablename
        if False:   # user has restricted access: we need a setting for this
           from User import User
           us = User.bring(currentUser())
           if us:
             Office = us.Office
             Shift  = us.Shift
        if Office:
            qstr += self.SQLRangeFilter(alias, "Office" ,Office)
        if User:
            qstr += self.SQLRangeFilter(alias, "User" ,User)
        if Computer:
            qstr += self.SQLRangeFilter(alias, "Computer" ,Computer)
        if Shift:
            qstr += self.SQLRangeFilter(alias, "Shift" ,Shift)
        if ShiftNr:
            qstr += self.SQLRangeFilter(alias, "ShiftNr" ,ShiftNr)
        return qstr

    def declareFields(self,allfields,stdfields):
        self.efields = stdfields
        self.dfields = [x for x in allfields if x not in stdfields ]

    def declareRecordFields(self,recordName,stdfields):
        exec("from %s import %s" % (recordName,recordName))
        exec("rec = %s()" % recordName)
        self.recordName = recordName
        techfields = ["internalId","attachFlag","syncVersion","SerNrf"]
        allfields = [x for x in rec.fieldNames() if x not in techfields ]
        self.declareFields(allfields,stdfields)
        for field in allfields:
            self.fieldLabels[field] = rec.getFieldLabel(field)


    def publishTitles(self):
        for field in self.efields:
            self.addValue(self.fieldLabels[field])

    def publishFields(self,rec,display=True):
        for field in self.efields:
            if (display):
                tmp = rec.getFieldDisplayValue(field)
            else:
                tmp = rec.fields(field).getValue()
            if field in ("Code","SerNr") and hasattr(self,"recordName"):
                self.addValue(tmp,Window="%sWindow" % self.recordName ,FieldName=field)
            else:
                self.addValue(tmp)

    def openColumnsSpec(self):
        if (self.efields):
            from FieldSelectWidgetWindow import FieldSelectWidgetWindow
            from FieldSelectWidget import FieldSelectWidget
            win = FieldSelectWidgetWindow()
            fsw = FieldSelectWidget()
            win.efields = self.efields
            win.dfields = self.dfields
            win.fieldLabels = self.fieldLabels
            win.report = self
            win.setRecord(fsw)
            win.open()
        else:
            message(tr("Feature Not Enabled for This Report Yet"))


    def getLabel(self):
        mi = getModulesInfo()
        for mname in mi:
            mod = mi[mname]
            repsinfo = filter(lambda x: x["Name"] == self.__class__.__name__, mod["Reports"])
            if len(repsinfo):
                return repsinfo[0]["Label"]
        return ""

    def getWindowFileName(self):
        import os
        gsd = getScriptDirs()
        res = ""
        for sdir in gsd:
            if os.path.isdir("%s/interface" %(sdir)):
                for filename in os.listdir("%s/interface" %(sdir)):
                    if "%s.reportwindow.xml" % (self.__class__.__name__) == filename:
                        res = "%s/interface/%s" % (sdir,filename)
                        return res
        return res

    def getWindowFieldsData(self):
        self.rwflist = {}

        from xml.sax import make_parser
        from xml.sax.handler import feature_namespaces
        parser = make_parser()
        parser.setFeature(feature_namespaces, 0)
        xmlhandler = XMLReportWindowHandler()
        xmlhandler.rwflist = self.rwflist
        parser.setContentHandler(xmlhandler)
        parser.parse(open(self.getWindowFileName()))
        return self.rwflist

    def getUserReportSpecRecord(self):
        from UserReportSpec import UserReportSpec
        res = UserReportSpec.bring(currentUser(),self.__class__.__name__)
        if res:
            return res
        return None

    def applyUserReportSpec(self):
        urspec = self.getUserReportSpecRecord()
        record = self.getRecord()
        if urspec:
            urspec.refreshDateValues()
            for uline in urspec.Fields:
                if (uline.FieldName in record.fieldNames()):
                #try:
                    if (uline.Type == "date"):
                        record.fields(uline.FieldName).setValue(stringToDate(uline.Value))
                    else:
                        if (uline.Value == "True"):
                            record.fields(uline.FieldName).setValue(True)
                        elif (uline.Value == "False"):
                            record.fields(uline.FieldName).setValue(False)
                        else:
                            record.fields(uline.FieldName).setValue(uline.Value)
                #except Exception, e:
                #    pass

    def openUserReportSpec(self):
        from UserReportSpec import UserReportSpec
        urspec = self.getUserReportSpecRecord()
        if (urspec):
            urspec.CurrentReport = self
            openWindow(urspec)
        else:
            urspec = UserReportSpec()
            urspec.fillReportFields(self)
            urspec.CurrentReport = self
            openWindow(urspec)

    def setProgress(self, done, total=None):
        pass

    def startRowStyle(self, style="", bColor=None, fColor=None):
        if (style):
            bColor, fColor = self.getStyleColors(style)
            self.rowstyles.append((bColor,fColor))
        else:
            from SystemSettings import SystemSettings
            sset = SystemSettings.bring()
            if (not bColor):
                dbColor = self.DefaultBackColor
            else:
                dbColor = bColor
            if (not fColor):
                dfColor = self.DefaultForeColor
            else:
                dfColor = fColor
            if (sset.InterpolateReportLines):
                if (self.linecolor):
                    dbColor = self.ReportLineLightColor
                    dfColor = self.DefaultForeColor
                self.linecolor = not self.linecolor
            if (not bColor): bColor = dbColor
            if (not fColor): fColor = dfColor
            self.rowstyles.append((bColor,fColor))

    def endRowStyle(self):
        try:
            self.rowstyles.pop()
        except:
            sysprint("Report Error: self.EndRow() sin self.StartRow() ")

    def getRowStyle(self):
        if (self.rowstyles):
            return self.rowstyles[len(self.rowstyles)-1]
        return (self.DefaultBackColor,self.DefaultForeColor)

    def getStyleColors(self, style=""):
        #alert(style)
        #alert(self.Styles.keys())
        if (style in self.Styles.keys()):
            bColor,fColor = self.Styles[style]
        else:
            bColor,fColor = self.getRowStyle()
        return (bColor,fColor)

    def makeSetFieldFilter(self, table, field, value):
        likestr = " %s.%s = s|%s| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%%,%s| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%s,%%| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%%,%s,%%| " %(table,field,value)
        return likestr

    def addPageBreak(self):
        self.addHTML("<div STYLE='page-break-after: always'></div>")

    @checkCommitConsistency
    def call_zoomIn_fromC(self, methodname, value):
        try:
            method = getattr(self, methodname)
            if method:
                method(value)
            else:
                message("Method %s not found in report" % methodname)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            raise

    @checkCommitConsistency
    def call_zoomInWithParam_fromC(self, methodname, param, value):
        try:
            method = getattr(self, methodname)
            if method:
                method(param, value)
            else:
                message("Method %s not found in report" % methodname)
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            raise

    @classmethod
    def defaultLoggingVersionsQty(objclass):
        return 0

    def showHistory_fromC(self):
        try:
            self.showHistory()
        except DBError, e:
            processDBError(e, {}, utf8(e))
        except Exception, e:
            raise

    def showHistory(self):
        from LogSettings import LogSettings
        ls = LogSettings.bring()
        if not ls.shouldLogReportEvents(self.__class__.__name__):
            message(tr("Report History has not been configured, check Settings/Register logging"))
        else:
            from RecordHistoryReport import RecordHistoryReport
            report = RecordHistoryReport()
            report.getRecord().TableName = self.__class__.__name__
            report.getRecord().FromDate = date(1900,1,1)
            report.getRecord().ToDate = date(2100,1,1)
            report.getRecord().Type = 1 #reports
            report.open(False)

    def addFieldFilters(self,alias,specs,fieldList,like=False):
        sqlstr = ""
        for fieldname in fieldList:
            filterValue = specs.fields(fieldname).getValue()
            if (not filterValue): continue
            if (not like):
                sqlstr += self.SQLRangeFilter(alias, fieldname , filterValue )
            else:
                sqlstr += " WHERE?AND LOWER({%s}) like s|%s|\n" % (fieldname, "%%"+filterValue.lower()+"%%")
        return sqlstr

    def addClassificationFilter(self,table,alias=""):
        record = self.getRecord()
        sqlstr = ""
        if (not alias):
            alias = table
        if ("Classification" in record.fieldNames()):
            if not record.fields("Classification").getValue(): return ""
            sqlstr =  " INNER JOIN [%sClas] ON [%sClas].{masterId} = [%s].{internalId} " % (table,table,alias)
            sqlstr += " WHERE?AND [%sClas].{Value} = s|%s| \n" % (table, record.fields("Classification").getValue() )
        return sqlstr

class XMLReportWindowHandler(handler.ContentHandler):
    accumchar = ""

    def startElement(self, name, attrs):
        rwflist = self.rwflist
        if (not rwflist.has_key("ListOfIndexedFields")):
            rwflist["ListOfIndexedFields"] = []
        if (name in ("text","integer")):
            fname = utf8(attrs.get("fieldname",""))
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "text"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist[fname]["PasteWindow"] = utf8(attrs.get("pastewindow",""))
            rwflist["ListOfIndexedFields"].append(fname)
        elif (name in ("date")):
            fname = utf8(attrs.get("fieldname",""))
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "date"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist["ListOfIndexedFields"].append(fname)
        elif (name in ("time")):
            fname = utf8(attrs.get("fieldname",""))
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "time"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist["ListOfIndexedFields"].append(fname)
        elif (name in ("checkbox")):
            fname = utf8(attrs.get("fieldname",""))
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "checkbox"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist["ListOfIndexedFields"].append(fname)
        elif (name in ("radiobutton","combobox")):
            fname = utf8(attrs.get("fieldname",""))
            self.curOptions = fname
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "options"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist[fname]["OptionValues"] = []
            rwflist[fname]["OptionLabels"] = []
            rwflist["ListOfIndexedFields"].append(fname)
        elif (name in ("radiooption","combooption")):
            value = attrs.get("value","").encode("ascii","xmlcharrefreplace")
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[self.curOptions]["OptionValues"].append(value)
            rwflist[self.curOptions]["OptionLabels"].append(tr(label))
        elif (name == "period"):
            fname = "%s-%s" %(utf8(attrs.get("fromfieldname","")),utf8(attrs.get("tofieldname","")))
            rwflist[fname] = {}
            rwflist[fname]["Type"] = "period"
            label = attrs.get("label","").encode("ascii","xmlcharrefreplace")
            rwflist[fname]["Label"] = tr(label)
            rwflist[fname]["FromDate"] = utf8(attrs.get("fromfieldname",""))
            rwflist[fname]["ToDate"] = utf8(attrs.get("tofieldname",""))
            rwflist["ListOfIndexedFields"].append(fname)

    def endElement(self, name):
        rwflist = self.rwflist
        if (name in ("radiobutton","combobox")):
            self.curOptions = ""

    def characters(self, chars):
        pass


