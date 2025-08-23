#encoding: utf-8
from OpenOrange import *

ParentRecordCheckPolicy = SuperClass("RecordCheckPolicy","Master",__file__)
class RecordCheckPolicy(ParentRecordCheckPolicy):
    buffer = RecordBuffer("RecordCheckPolicy", RecordBuffer.defaulttimeout, True)

    def check(self):
        if (not self.Enabled): return True
        rec = NewRecord(self.Code)
        if not rec:
            return self.FieldErrorResponse("INVALIDVALUEERR","Code")
        for prow in self.FieldsList:
            if prow.HeaderField in rec.detailNames():
               if (not prow.RowField):
                  return prow.FieldErrorResponse("NONBLANKERR","RowField")
               #ds = rec.details("Items")
            elif not rec.hasField(prow.HeaderField):
               return prow.FieldErrorResponse("INVALIDVALUEERR","HeaderField")
        return True

    def getHeaderFieldCases(self):
        blist = {}
        for fline in self.FieldsList:
            if (not fline.RowField):
                if (fline.Case <> 0):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    if (fline.Case <> 0):
                        blist[fline.HeaderField]["Case"] = fline.Case
        return blist

    def getRowFieldsCases(self):
        blist = {}
        for fline in self.FieldsList:
            if (fline.RowField):
                if (fline.Case <> 0):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    blist[fline.HeaderField][fline.RowField] = {}
                    blist[fline.HeaderField][fline.RowField]["Case"] = fline.Case
        return blist

    def getNonBlankHeaderFields(self):
        blist = {}
        for fline in self.FieldsList:
            if (not fline.RowField):
                if (fline.NonBlank):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    if (fline.Message):
                        blist[fline.HeaderField]["Message"] = fline.Message
                    else:
                        blist[fline.HeaderField]["Message"] = tr("NONBLANKERR") + " " + tr(fline.HeaderField)
                    blist[fline.HeaderField]["DontSave"] = fline.DontSave
        return blist


    def getNonBlankRowFields(self):
        blist = {}
        for fline in self.FieldsList:
            if (fline.RowField):
                if (fline.NonBlank):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    blist[fline.HeaderField][fline.RowField] = {}
                    if (fline.Message):
                        blist[fline.HeaderField][fline.RowField]["Message"] = fline.Message
                    else:
                        blist[fline.HeaderField][fline.RowField]["Message"] = tr("NONBLANKERR") + " " +  tr(fline.RowField)
                    blist[fline.HeaderField][fline.RowField]["DontSave"] = fline.DontSave
        return blist

    def getNoEditableHeaderFields(self):
        blist = {}
        for fline in self.FieldsList:
            if (not fline.RowField):
                if (fline.NotEditable):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    if (fline.Message):
                        blist[fline.HeaderField]["Message"] = fline.Message
                    else:
                        blist[fline.HeaderField]["Message"] = None
        return blist

    def getNoEditableRowFields(self):
        blist = {}
        for fline in self.FieldsList:
            if (fline.RowField):
                if (fline.NotEditable):
                    if (not blist.has_key(fline.HeaderField)):
                        blist[fline.HeaderField] = {}
                    blist[fline.HeaderField][fline.RowField] = {}
                    if (fline.Message):
                        blist[fline.HeaderField][fline.RowField]["Message"] = fline.Message
                    else:
                        blist[fline.HeaderField][fline.RowField]["Message"] = None
        return blist

    def getHeaderCheckedFields(self):
        blist = {}
        clist = ["","==","<",">","<=",">="," in ","!="]
        for fline in self.Checks:
            if (fline.Condition):
                blist[fline.HeaderField] = {}
                blist[fline.HeaderField]["Check"] = clist[fline.Condition]
                blist[fline.HeaderField]["Value"] = fline.Value
                blist[fline.HeaderField]["Message"] = fline.Message
        return blist

    def getRowCheckedFields(self):
        blist = {}
        clist = ["","==","<",">","<=",">="," in ","!="]
        for fline in self.Checks:
            if (fline.Condition):
                blist[fline.HeaderField] = {}
                blist[fline.HeaderField][fline.RowField] = {}
                blist[fline.HeaderField][fline.RowField]["Check"] = clist[fline.Condition]
                blist[fline.HeaderField][fline.RowField]["Value"] = fline.Value
                blist[fline.HeaderField][fline.RowField]["Message"] = fline.Message
        return blist


    def checkFieldValue(self, fvalue, cvalue, fcheck):
        try:
            if (fvalue.__class__.__name__ in ("str","unicode","time")):
                fvalue = "'%s'" %(fvalue)
                cvalue = "'%s'" %(cvalue)
            elif (fvalue.__class__.__name__ in ("date")):
                fvalue = "'%s'" %(fvalue.strftime("%d/%m/%Y"))
                cvalue = "'%s'" %(cvalue.replace("-","/"))
            if (fcheck == " in "):
                clist = cvalue.split(",")
                if (fvalue.__class__.__name__ == "str"):
                    cvalue = "(%s)" %("','".join(clist))
                else:
                    cvalue = "(%s)" %(",".join(clist))
            evalstring = "%s %s %s" %(fvalue,fcheck,cvalue)
            evalue = eval(evalstring)
        except Exception, err:
            postMessage("Error evaluating RCP. %s. %s" %(evalstring,err))
            log("Error evaluating RCP. %s. %s" %(evalstring,err))
            evalue = False
        return evalue


ParentRecordCheckPolicyFieldsListRow = SuperClass("RecordCheckPolicyFieldsListRow","Record",__file__)
class RecordCheckPolicyFieldsListRow(ParentRecordCheckPolicyFieldsListRow):
    pass