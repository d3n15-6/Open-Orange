#encoding: utf-8
from OpenOrange import *

ParentOOCase = SuperClass("OOCase","Numerable",__file__)
class OOCase(ParentOOCase):

    def defaults(self):
        ParentOOCase.defaults(self)
        self.User = currentUser()
        
    def afterCopy(self):
        ParentOOCase.afterCopy(self)
        self.OOCaseNr = None
        self.User = currentUser()
    
    def beforeInsert(self):
        res = ParentOOCase.beforeInsert(self)
        if not res: return res
        res = self.post()
        if not res: return res
        return True

    def beforeUpdate(self):
        res = ParentOOCase.beforeUpdate(self)
        if not res: return res
        res = self.post()
        if not res: return res
        return True
        
    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentOOCase.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if not res: return res
        if not self.isNew():
            if fieldname in ("Subject",): return False
        return True

   
        
    def post(self):
        import urllib2
        import urllib
        from TaxSettings import TaxSettings
        taxregnr = TaxSettings.bring().TaxRegNr
        if self.isNew():
            params = {}
            params["TaxRegNr"] = taxregnr
            from OurSettings import OurSettings
            oss = OurSettings.bring()
            params["CompanyName"] = oss.Name + ", "+ oss.FantasyName
            params["reclamo"] = self.Message
            params["tema"] = self.Subject
            params["user_code"] = currentUser()
            params["action"] = "genCaseFromOO"
            from User import User
            params["user_name"] = User.bring(currentUser()).Name
            params = urllib.urlencode(params)
            response = urllib.urlopen("http://www.openorange.com.ar/cgi-bin/case.py?"+ params)
            self.OOCaseNr, ttime, msg = response.read().split("|")
            self.TransTime = ttime
            message(msg)
            return True
        else:
            params = {}
            params["TaxRegNr"] = taxregnr
            params["reclamo"] = self.Message
            params["tema"] = self.Subject
            params["caseNr"] = self.OOCaseNr
            params["user_code"] = currentUser()
            params["action"] = "appendToCaseFromOO"
            from User import User
            params["user_name"] = User.bring(currentUser()).Name
            params = urllib.urlencode(params)
            response = urllib.urlopen("http://www.openorange.com.ar/cgi-bin/case.py?"+ params)
            res, msg = response.read().split("|")
            message(msg)
            return res.lower() == "true"
        
