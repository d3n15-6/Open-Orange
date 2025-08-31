#encoding: utf-8
from OpenOrange import *
from Report import Report
from StoredProcedures import StoredProcedures

class OOCaseReport(Report):

    def run(self):
        self.case, usernames = self.getOOCase()
        self.startTable()
        self.startHeaderRow()
        self.addValue(tr("User"))
        self.addValue(tr("Date"))
        self.addValue(tr("Time"))
        self.addValue(tr("Description"))
        self.addValue(tr("Asignee"))
        self.endHeaderRow()        
        if self.case:
            oldstatus = self.window.getRecord().isModified()
            self.window.getRecord().Closed = bool(self.case.Status)
            self.window.getRecord().setModified(oldstatus)
            for rownr in range(self.case.Events.count()-1,-1,-1):
                crow = self.case.Events[rownr]
                self.startRow()
                self.addValue(usernames[crow.User])
                self.addValue(crow.Date)
                self.addValue(crow.Time)
                self.addValue(crow.Comment)
                self.addValue(usernames[crow.Asignee])
                self.endRow()
        self.endTable()
        

    def getOOCase(self):
        if not self.OOCaseNr: return None, None
        import urllib2
        import urllib
        params = {}
        params["caseNr"] = self.OOCaseNr
        params["action"] = "getCaseDetailFromOO"
        from User import User
        params["user_name"] = User.bring(currentUser()).Name
        params["T"] = self.CaseTransTime.strftime("%H.%M.%S")
        params = urllib.urlencode(params)
        response = urllib.urlopen("http://www.openorange.com.ar/cgi-bin/case.py?"+ params)
        pickle = response.read()
        import cPickle
        p = cPickle.loads(pickle)
        if p["response"]:
            return p["case"], p["usernames"]
        else:
            return None, None
        
