#encoding: utf-8
from OpenOrange import *

YesNoColors = ["#FF3300","#339900"]
YesNoStatus = [tr("No"),tr("Yes")]
DeliveryStatus = [tr("Approved"),tr("Picking"),tr("Finished")]
AbleDisableColors = ["#C0C0C0","#0000FF"]
EventLogActions = [tr("Create"),tr("Modify"),tr("Delete")]
YesNoImages = ["switchoff.png","switchon.png"]
ClosedStatus = [tr("Open"),tr("Closed")]
BooleanStatus = [tr("False"),tr("True")]
QuoteStatus= [tr("Open"),tr("Being Negociated"),tr("Accepted"),tr("Bounced"),tr("Expired")]
RecordStatus = [tr("Not approved"),tr("Approved")]
TransactionStatus = [tr("Not approved"),tr("Approved")]
ReserveStatus = [tr("Not reserved"),tr("Reserved")]
LongDayNames = [tr("Monday"),tr("Tuesday"),tr("Wednesday"),tr("Thursday"),tr("Friday"),tr("Saturday"),tr("Sunday")]
LongMonthNames = [tr("None"),tr("January"),tr("February"),tr("March"),tr("April"),tr("May"),tr("June"),tr("July"),tr("August"),tr("September"),tr("October"),tr("November"),tr("December")]
InvalidStatus = [tr(""),tr("Invalidated")]

def getSettingRecordField(tablename, field):
    exec("from %s import %s" %(tablename,tablename))
    exec("res = %s.bring()" %(tablename))
    if (res):
        return res.fields(field).getValue()
    else:
        return ""
    return ""

def getFinalStatus(tablename):
    exec("from %s import %s as TRecord " %(tablename,tablename))
    obj = TRecord()
    return obj.finalStatus()

def getStatusNames(tablename):
    exec("from %s import %s as TRecord" %(tablename,tablename))
    obj = TRecord()
    return obj.getStatusNames()

def getMasterRecordField(tablename, field, strcode):
    exec("from %s import %s as TheMaster" %(tablename,tablename))
    res = TheMaster.bring(strcode)
    if (res):
        if (field in res.fieldNames()):
            return res.fields(field).getValue()
        else:
            message("%s. %s" %(tr("Field Does Not Exists"),field))
            return ""
    else:
        return ""
    return ""

def afterEdit(self, fieldname):
    record = self.getRecord()
    if (hasattr(record,"paste%s" %fieldname)):
        exec("record.paste%s()" %fieldname)

def afterEditRow(self, fieldname, rowfieldname, rownr):
    record = self.getRecord()
    exec("wrow = record.%s[rownr]" %fieldname)
    if (hasattr(wrow,"paste%s" %rowfieldname)):
        exec("wrow.paste%s(record)" %rowfieldname)

def openWindow(record):
    classname = record.name()
    exec("from %sWindow import %sWindow" %(classname,classname))
    exec("rwindow = %sWindow() " %(classname))
    rwindow.setRecord(record)
    rwindow.open()

def classImport(classname):
    exec("from %s import %s" %(classname,classname))
    exec("obj = %s()" %(classname))
    return obj

def accumByCurrency(cdict, amount, currency):
    if (not cdict.has_key(currency)):
        cdict[currency] = 0
    cdict[currency] += amount

def bringRecord(classname,rid):
    try:
        exec("from %s import %s" %(classname,classname))
        exec("obj = %s().bring(%s)" %(classname,rid))
        if (obj):
            return obj
    except:
        log("Except in bringRecord from GlobalTools")
    return None

def showSystemOSD(text):
    import os
    path = os.path.abspath(".")
    os.system('notify-send -i "%s/images/OpenOrange_Icon.png" "Open Orange" "%s" ' %(path,text))

def copyFields(ofrom, oto, flist=[]):
    if (flist):
        for fname in flist:
            if (fname in ofrom.fieldNames() and fname in oto.fieldNames()):
                if (not ofrom.fields(fname).isNone()):
                    oto.fields(fname).setValue(ofrom.fields(fname).getValue())
    else:
        for fname in oto.fieldNames():
            if (fname in ofrom.fieldNames()):
                if (not ofrom.fields(fname).isNone()):
                    oto.fields(fname).setValue(ofrom.fields(fname).getValue())
    return oto

def attrlist(object):
    return "\n".join(dir(object))

def getWrappedText(wraptext, wraplimit):
    wraptext = wraptext.split(" ")
    rtext = []
    accum = ""
    for i in range(len(wraptext)):
        accum += "%s " %(wraptext[i])
        if (len(accum) >= wraplimit):
            rtext.append(accum)
            accum = ""
    if (accum):
        rtext.append(accum)
    return rtext
