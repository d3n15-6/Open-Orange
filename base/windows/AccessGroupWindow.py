#encoding: utf-8
from OpenOrange import *

ParentAccessGroupWindow = SuperClass("AccessGroupWindow","MasterWindow",__file__)
class AccessGroupWindow(ParentAccessGroupWindow):
        
    def afterEdit(self, fieldname):
        record = self.getRecord()
        if (fieldname == "ContactCode"):
            record.pasteContact()
        elif (fieldname == "CustCode"):
            record.pasteCustomer()
        elif (fieldname == "FromTime"):
            record.pasteFromTime()
        elif (fieldname == "ToTime"):
            record.pasteToTime()
        elif (fieldname == "Consultant"):
            record.pasteConsultant()

    def fillPasteWindow(self, pastewindowname, fieldname):
        if (pastewindowname == "XPasteWindow"):
                query = []
                for info in getModulesInfo().values():
                    z = NewRecord("X")
                    z.Code = info["Code"]
                    z.Name = info["Label"]
                    query.append(z)
                    query.sort(key = lambda x: x.Name)
                return query  

    def fillPasteWindowRow(self, pastewindowname, fieldname, rowfieldname,rownr):
        if pastewindowname == "XPasteWindow":
            if fieldname == "Records":
                query = []
                wininfo = getWindowsInfo()
                for wInfo in wininfo.values():
                    z = NewRecord("X")
                    z.Code = wInfo["RecordName"]
                    z.Name = wInfo["Title"]
                    query.append(z)
                query.sort(key = lambda x: x.Name)
                return query
            elif fieldname == "Reports":
                query = []
                lists = map(lambda m: m["Reports"], getModulesInfo().values())
                for lst in lists:
                    for info in lst:
                        z = NewRecord("X")
                        z.Code = info["Name"]
                        z.Name = info["Label"]
                        query.append(z)
                    query.sort(key = lambda x: x.Name)
                return query 
            elif fieldname == "Routines":
                query = []
                lists = map(lambda m: m["Routines"], getModulesInfo().values())
                for lst in lists:
                    for info in lst:
                        z = NewRecord("X")
                        z.Code = info["Name"]
                        z.Name = info["Label"]
                        query.append(z)
                query.sort(key = lambda x: x.Name)
                return query            
            elif fieldname == "Modules":
                query = []
                for info in getModulesInfo().values():
                    z = NewRecord("X")
                    z.Code = info["Code"]
                    z.Name = info["Label"]
                    query.append(z)
                    query.sort(key = lambda x: x.Name)
                return query  
        elif (pastewindowname == "FunctionalityPasteWindow"):
            from AccessGroup import AccessGroup
            from X import X

            funcs = map(lambda x: (x, tr(x)), AccessGroup.getFunctionalities())
            res = []
            for func in funcs:
                x = X()
                x.Code = func[0]
                x.Name = func[1]
                res.append(x)
            return res
        return None

    def showUsers(self):
    	record = self.getRecord()
    	from AccessGroupUsers import AccessGroupUsers
    	rep = AccessGroupUsers()
    	recrep = rep.getRecord()
    	recrep.Code = record.Code
    	rep.open(False)