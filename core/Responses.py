#coding: utf-8

class ServerError(Exception): pass
class ErrorResponse:

    def __init__(self, errorCode="", errorParams={}):
        from functions import utf8
        self.errorCode = utf8(errorCode)
        self.errorParams = errorParams
        self.doFocus()

    def doFocus(self):
        if self.errorParams:
            fieldname = self.errorParams.get("FieldName", None)
            rowfieldname = self.errorParams.get("RowFieldName", "")
            rownr = self.errorParams.get("RowNr", -1)
            record = self.errorParams.get("Record",None)
            if record and fieldname:
                record.setFocusOnField(fieldname,rowfieldname,rownr)

    def __nonzero__(self):
        return False

    def __str__(self):
        from functions import tr, utf8
        #return tr(self.errorCode)
        record = self.errorParams.get("Record",None)
        fname = self.errorParams.get("FieldName","").strip()
        rfname = self.errorParams.get("RowFieldName","").strip()
        fieldlabel = ""
        if (record): 
            fieldlabel = record.getFieldLabel(fname,"",rfname)
        if not fieldlabel:
            fieldlabel = fname
        s ='<font color="red">%s</font>' % tr(self.errorCode)
        done = False
        for key in self.errorParams.keys():
            from Embedded_OpenOrange import sysprint
            #sysprint("KEY: " + key)
            val = utf8(self.errorParams[key])
            if val:
                value = "%s" %(self.errorParams[key])
                errorString = "%s %s" %(key,value)
                if (key == "Record"):
                    #errorString = "%s %s" %(tr("Record"), utf8(record.getTitle()))
                    pass
                elif (key == "FieldName" ):
                    if (not self.errorParams.get("RowFieldName","")):
                        errorString = "%s: %s " %(tr("Field"),fieldlabel)
                    else:
                        errorString = "%s: %s " %(tr("Matrix"),tr(fname))
                elif (key == "RowFieldName"):
                    errorString = "%s: %s " %(tr("Column"),fieldlabel)
                elif (key == "RowNr"):
                    if (self.errorParams["RowNr"] > 0):
                        try:
                            value = str(int(value)+1)
                        except:
                            pass
                        errorString = "%s: %s" %(tr("Row"),value)
                    else:
                        errorString = ""
                elif (key == "Value"):
                    errorString = "%s: %s" %(tr("Value"),value)
                if (errorString):
                    s = s + "<br>%s" % errorString
                done = True
        if not done:
            for p in self.errorParams.keys():
                if isinstance(self.errorParams[p],str):
                    if str(self.errorParams[p]):
                        s += "<br>%s:%s" % (tr(p), str(self.errorParams[p]))
                        done = True
        return utf8(s)

class StoreErrorResponse:

    def __init__(self, record = ""):
        self.record = record

    def __nonzero__(self):
        return False

    def __str__(self):
        from functions import tr
        return "%s<br>" % str(self.record) + tr("The Record could not be saved. May be other user has changed it.")

class AppException(Exception):

    def __init__(self, *vargs, **kwargs):
        self.args = vargs
        self.kwargs = kwargs

    def shouldBeProcessed(self):
        return self.kwargs.get("ShouldBeProcessed", True)

class RecordNotFoundException(AppException):

    def __init__(self, classobj, *vargs, **kwargs):
        AppException.__init__(self, *vargs, **kwargs)
        self.classobj = classobj

    def __str__(self):
        from functions import tr
        return "%s %s %s." % (tr(self.classobj.__name__), self.kwargs.get("Key",""), tr("not found"))

    def __repr__(self):
        from functions import tr
        return "<RecordNotFoundException (%s %s %s.)>" % (tr(self.classobj.__name__), self.kwargs.get("Key",""), tr("not found"))