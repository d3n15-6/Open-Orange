#coding: utf-8
from Embedded_OpenOrange import *
from Query import Query
import new
import sys
from core.Responses import *
from datetime import timedelta, time
import __builtin__
import cPickle
from Log import log
from BasicFunctions import now, today
from core.database.Database import Database, DBError, DBConnectionError

__standard_import__ = __builtin__.__import__

messagesQueue = {}
modules_index = None
__langdict = None

#Experimental begins here
__standard_import__ = __builtin__.__import__
__builtin__.standard_import = __builtin__.__import__
def __redefined_import__(name, globals=None, locals=None, fromlist=None, level=-1):
    if modules_index and modules_index.has_key(name):
        try:
            return __standard_import__(modules_index[name][-1], globals, locals, fromlist, level)
        except:
            return __standard_import__(name, globals, locals, fromlist, level)
    return __standard_import__(name, globals, locals, fromlist, level)


__builtin__.__import__ = __redefined_import__

#Experimental ends here

def serverside(func):
    def wrapper(*args, **kwargs):
        if getApplicationType() == 1:
            #client application
            from core.AppServerConnection import AppServerConnection
            return AppServerConnection.getConn().call(func.__name__, *args, **kwargs)
        else:
            return func(*args, **kwargs)
    wrapper.__dict__ = func.__dict__
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def createModuleAndClass(name, baseclassname):
    #temporal for mac and linux
    from core.Record import Record
    classobject = new.classobj(name, (Record,),{})
    mod = new.module(name)
    mod.__dict__[name] = classobject
    sys.modules[name] = mod

def createRecordModuleAndClass(name, baseclassname):
    from core.Record import Record
    classobject = new.classobj(name, (Record,),{})
    mod = new.module(name)
    mod.__dict__[name] = classobject
    sys.modules[name] = mod

def createWindowModuleAndClass(name, baseclassname):
    from core.Window import Window
    classobject = new.classobj(name, (Window,),{})
    mod = new.module(name)
    mod.__dict__[name] = classobject
    sys.modules[name] = mod

def getSaveFileName(msg="", **kwargs):
    defaultfilename = kwargs.get("DefaultFileName", "")
    filterstr = kwargs.get("Filter", "*.*")
    return embedded_getSaveFileName(msg, defaultfilename, filterstr)

class PrintToLog:
    def write(self, msg):
            log(msg)

if not hasConsole():
    import sys
    sys.stdout = PrintToLog()

def langdict():
    global __langdict
    if __langdict is None:
        import os.path
        exec("from languages.lang_%s import lang_dict" % getLanguage())
        __langdict = lang_dict
        sdirs = getScriptDirs(99999)
        for sd in reversed(sdirs):
            if os.path.exists(os.path.join(sd, "languages/lang_%s.py" % getLanguage())):
                exec("from %s.languages.lang_%s import lang_dict" % (sd.replace('/','.'), getLanguage()))
                __langdict.update(lang_dict)
        for k,v in __langdict.items():
            if not isinstance(k, unicode): k = unicode(k,'utf-8', 'replace')
            if not isinstance(v, unicode): v = unicode(v,'utf-8', 'replace')        
            __langdict[k] = v
    return __langdict


def tr(*args):        # old definition was tr(msg, default=-1):
    lang = getLanguage()
    eles = []
    for ele in args:
        if isinstance(ele, unicode):
            sele = ele
        else:
            if hasattr(ele, "__str__"):
                sele = ele.__str__() #__str__ funciona mejor cuando el objeto es un errorresponse
            else:
                sele = str(ele)
        eles.append({True: langdict().get(ele,ele), False: sele}[bool(langdict().get(ele,ele))])
    res = " ".join(eles)
    if isinstance(res, unicode): return res
    return unicode(res, 'utf8', 'replace')

def setCurrentUser(usercode):
    import threading
    threading.currentThread().currentUser = usercode
    sysprint("\nsetcurrentuser: %s\n" %usercode)

def currentUser():
    import threading
    currentthread = threading.currentThread()
    if hasattr(currentthread, "currentUser") and currentthread.currentUser:
        return currentthread.currentUser
    else:
        return curUser()

def currentComputer():
    from LocalSettings import LocalSettings
    ls = LocalSettings.bring()
    return ls.Computer

def currentOffice():
    from OurSettings import OurSettings
    oset = OurSettings.bring()
    if (oset):
        if (oset.OfficeDeterminator == 0):
            from User import User
            usr = User.bring(currentUser())
            if (usr):
                return usr.Office
        elif (oset.OfficeDeterminator == 1):
            from LocalSettings import LocalSettings
            lset = LocalSettings.bring()
            if (lset):
                comp = lset.getComputerRecord()
                if (comp):
                    return comp.Office
        return oset.DefOffice
    return None

def currentShift():
    from User import User
    usr = User.bring(currentUser())
    if (usr):
        return usr.Shift
    return Noneo

def clientMessage(msg):
    import threading
    import core.AppCommand
    cmd = core.AppCommand.AppCommand_ClientMessage()
    cmd.message = msg
    threading.currentThread().clientHandler.sendObject(cmd)

def message(msg, *args):
    import threading
    if hasattr(threading.currentThread(), "clientHandler"):
        import core.AppCommand
        cmd = core.AppCommand.AppCommand_ClientMessage()
        cmd.message = msg
        threading.currentThread().clientHandler.sendObject(cmd)
    else:
        s = ""
        if len(args):
            s = ": " + args[0]
            for arg in args[1:]:
                s += ", " + utf8(arg)
        try:
            from SystemSettings import SystemSettings
            if (SystemSettings.bring().LogVisualMessages):
                log("Visual Message: " + tr(msg) + s)
        except Exception, err:
            postMessage("Error Consulting SystemSettings. Logging anyway.")
            log("Error Consulting SystemSettings. Logging anyway.")
            log("Visual Message: " + tr(msg) + s)
        if messagesEnabled():
            displaymessage(tr(msg) + s, "messageIcon")
        else:
            threadname = threading.currentThread().getName()
            if not messagesQueue.has_key(threadname): messagesQueue[threadname] = []
            messagesQueue[threadname].append(tr(msg) + s)

def showError(msg, *args):
    import threading
    if hasattr(threading.currentThread(), "clientHandler"):
        import core.AppCommand
        cmd = core.AppCommand.AppCommand_ClientMessage()
        cmd.message = msg
        threading.currentThread().clientHandler.sendObject(cmd)
    else:
        s = ""
        if len(args):
            s = ": " + args[0]
            for arg in args[1:]:
                s += ", " + str(arg)
        if messagesEnabled():
            displaymessage(tr(msg) + s, "errorIcon")
        else:
            threadname = threading.currentThread().getName()
            if not messagesQueue.has_key(threadname): messagesQueue[threadname] = []
            messagesQueue[threadname].append(tr(msg) + s)

def alert(msg):
    """ Only for debugging """
    from SystemSettings import SystemSettings
    # Translating messages that are only 4 programmers is hardly important 
    #if SystemSettings.bring().LogVisualMessages:
    #    log("Visual Alert: " + tr(msg))  # doesnt show dictionaries anymore !!
    if messagesEnabled():
        displaymessage(msg, "messageIcon")
    else:
        import threading
        threadname = threading.currentThread().getName()
        if not messagesQueue.has_key(threadname): messagesQueue[threadname] = []
        messagesQueue[threadname].append(msg)

""" do not exist anymore please access directly globals
def monthName(nro):
    return tr(globals.MonthNames[nro])

def dayName(gdate):
    return tr(globals.DayNames[gdate.weekday()])
"""

@serverside
def serverNow():
    from datetime import datetime
    return datetime.now()

server_time_difference = None

#Este metodo se debe eliminar y usar el formato de Opciones de Sistema
def formatDate(myDate, formatstr=None):
    from SystemSettings import SystemSettings
    sset = SystemSettings.bring()
    if myDate.year < 1900: 
        return ""
    return myDate.strftime(sset.getDateFormat())

def addDays(myDate, days):
    try:
        myDate += timedelta(days)
    except:
        pass
    return myDate

def roundedEqual(v1, v2):
    return (abs(v1 - v2) < 0.00000001)

def roundedZero(v1):
    return roundedEqual(v1,0.0)

def addTime(myTime1, myTime2):
    # a ver si puede ser mas elegante y generico
    d1 = timedelta(hours=myTime1.hour,minutes = myTime1.minute,seconds=myTime1.second)
    d2 = timedelta(hours=myTime2.hour,minutes = myTime2.minute,seconds=myTime2.second)
    d3 = d1 + d2
    mins = d3.seconds // 60
    secs = d3.seconds % 60
    hrs = mins // 60
    mins = mins - hrs * 60
    myTime = time(hrs,mins,secs)
    return (myTime)

def addMinutes(myTime, minutes):
    td = timedelta(hours=myTime.hour,minutes = (myTime.minute + minutes),seconds=myTime.second)
    mins = td.seconds // 60
    secs = td.seconds % 60
    hrs = mins // 60
    mins = mins - hrs * 60
    return time(hrs,mins,secs)

def subTime(myTime1, myTime2):
    # a ver si puede ser mas elegante y generico
    d1 = timedelta(hours=myTime1.hour,minutes = myTime1.minute,seconds=myTime1.second)
    d2 = timedelta(hours=myTime2.hour,minutes = myTime2.minute,seconds=myTime2.second)
    d3 = d1 - d2
    mins = d3.seconds // 60
    secs = d3.seconds % 60
    hrs = mins // 60
    mins = mins - hrs * 60
    myTime = time(hrs,mins,secs)
    return (myTime)

def timeDiff(myTime1, myTime2):
    d1 = timedelta(hours=myTime1.hour,minutes = myTime1.minute,seconds=myTime1.second)
    d2 = timedelta(hours=myTime2.hour,minutes = myTime2.minute,seconds=myTime2.second)
    return d1-d2

def integerToTimeDelta(int):
    from datetime import timedelta
    hs = (int - (int % 3600)) / 3600
    min = ((int % 3600) - ((int % 3600) % 60 )) / 60
    sg = int - (hs * 3600) - (min * 60)
    #time = ("%02.f" % hs) + ":" + ("%02.f" % min) + ":" + ("%.0f" % sg)
    res = timedelta(0,sg,0,0,min,hs)
    return res

def timeToInteger(time):
    return (time.hour * 3600) + (time.minute * 60) + time.second

def dateDiff(StartDate, EndDate):
    res = EndDate - StartDate
    return res.days

def daterange(sdate,edate, step = timedelta(1)):
    """ Para iterar sobre rangos de fechas"""
    if not isinstance(step, timedelta):
        step = timedelta(step)
    ZERO = timedelta(0)
    if sdate < edate:
        if step <= ZERO:
            raise StopIteration
        test = edate.__gt__
    else:
        if step >= ZERO:
            raise StopIteration
        test = edate.__lt__
    while test(sdate):
        yield sdate
        sdate += step

def isWorkday(myDate):
    if myDate.weekday() in (6,7):
        return False
    from PublicHoliday import PublicHoliday
    PublicHoliday.loadAll()
    if myDate in PublicHoliday.dates.keys():
        return False
    return True

def lastworkday():
    d = today()
    from PublicHoliday import PublicHoliday
    PublicHoliday.loadAll()
    while (myDate.weekday() in (6,7) or myDate in PublicHoliday.dates.keys()):
        d = addDays(d,-1)
    return d

def isLeapYear(yycur):
    if ((yycur % 4 == 0 and yycur % 100 !=0) or yycur % 400 == 0):
        return True
    return False

def addYears(myDate, years):
    from datetime import date
    myDate = date(myDate.year+years,myDate.month,myDate.day)
    return myDate

def getQuarter(myDate):
    from datetime import date
    return ((myDate.month - 1) // 3) + 1

def addQuarter(myDate):
    from datetime import date
    nyear  = myDate.year + (myDate.month + 3) // 12
    nmonth = (myDate.month + 3)
    if (nmonth > 12):
        nmonth = nmonth % 12
    myDate = date(nyear,nmonth,myDate.day)
    return myDate

def isLastDay(CurYY, CurMM, CurDD, fulldate=None):
    if (fulldate):
        CurYY = fulldate.year
        CurMM = fulldate.month
        CurDD = fulldate.day
    lastday = False
    if (CurMM in (4,6,9,11)):
        if (CurDD == 30):
            lastday = True
    if (CurMM in (1,3,5,7,8,10,12)):
        if (CurDD == 31):
            lastday = True
    if (CurMM == 2):
        if (not isLeapYear(CurYY) and CurDD == 28):
            lastday = True
        if (isLeapYear(CurYY) and CurDD == 29):
            lastday = True
    return lastday

def getLastDay(CurYY, CurMM, fulldate=None):
    if (fulldate):
        CurYY = fulldate.year
        CurMM = fulldate.month
    if (CurMM in (4,6,9,11)):
        return 30
    if (CurMM in (1,3,5,7,8,10,12)):
        return 31
    if (CurMM == 2):
        if (not isLeapYear(CurYY)):
            return 28
        if (isLeapYear(CurYY)):
            return 29

def addMonths(myDate, months):
    from datetime import date

    CurDD = myDate.day
    CurMM = myDate.month
    CurYY = myDate.year
    AddDD = 0
    AddMM = months
    AddYY = 0
    SumDD = CurDD + AddDD
    SumMM = CurMM + AddMM
    SumYY = CurYY + AddYY

    while SumMM > 12:
        SumMM -=  12
        SumYY += 1
    while SumMM < 1:
        SumMM +=  12
        SumYY -= 1
    #print "isLastDay(CurYY,CurMM,CurDD)", CurDD,CurMM,CurYY, isLastDay(CurYY,CurMM,CurDD)
    if (isLastDay(CurYY,CurMM,CurDD) or SumDD > getLastDay(SumYY,SumMM)):
        SumDD = getLastDay(SumYY,SumMM)
    myDate = date(SumYY,SumMM,SumDD)
    return myDate

def stringToDate(dstring):
    from datetime import date
    if ("-" in dstring):
        a,b,c = dstring.split("-")
    elif ("/" in dstring):
        a,b,c = dstring.split("/")
    elif ("." in dstring):
        a,b,c = dstring.split(".")
    else:
        if (len(dstring) in (6,8)):
            a = dstring[0:2]
            b = dstring[2:4]
            c = dstring[4:]
        else:
            return ""
    a = int(a)
    b = int(b)
    c = int(c)
    if (a > 31):
        year = a
        month = b
        day = c
    elif (c > 31):
        day = a
        month = b
        year = c
    else:
        day = a
        month = b
        year = 1900 + c
    try:
        myDate = date(year,month,day)
    except:
        myDate = None
    return myDate

def StartOfMonth(myDate):
    return addDays(myDate,(-myDate.day+1))

def StartOfYear(myDate):
    from datetime import date
    ydate = date(myDate.year,1,1)
    return ydate

def StartOfWeek(myDate):
    return addDays(myDate,(-(myDate.isoweekday()-1)))

def weekBoundaries(year, week):
    from datetime import date
    startOfYear = date(year, 1, 1)
    week0 = startOfYear - timedelta(days=startOfYear.isoweekday())
    sun = week0 + timedelta(weeks=week)
    sat = sun + timedelta(days=6)
    return sun, sat

def EndOfMonth(myDate):
    #Estuve usando esta función y creo que no funciona bien. MSP
    return addDays(addMonths(myDate,1),-(myDate.day))
    #return datetime(myDate.year, myDate.month, monthrange(myDate.year, myDate.month)[1])

def EndOfYear(myDate):
    from datetime import date
    ydate = date(myDate.year,12,31)
    return ydate

def import_parent_package(rootpackage, name, fromlist):
    name = rootpackage + '.' + name
    mod = __import__(name, globals(), locals(), fromlist)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def currentUserCanDo_fromC(actionname, default):
    #temporal
    if (currentUser() == "OO" and actionname == "CanSynchronizeRecords" ):
        try:
           open("force.sync", "r")
           return True
        except:
           pass
    try:
        if not currentUser() or currentUser() == "_NoUser_": return True
        from User import User
        if default is False: default = ErrorResponse("User is not authorized")
        res = User.currentCanDo(actionname,default)
        return res
    except DBError, e:
        processDBError(e, {}, str(e))
        return False

def currentUserCanDo(actionname, default=True):
    if (currentUser() == "OO" and actionname == "CanSynchronizeRecords" ):
        try:
           open("force.sync", "r")
           return True
        except:
           pass
    if not currentUser() or currentUser() == "_NoUser_": return True
    from User import User
    if default is False: default = ErrorResponse("User is not authorized")
    res = User.currentCanDo(actionname,default)
    return res

def getNextCol(columns, row, col, fieldname):
    cnt = 0
    if fieldname and fieldname in columns:
        for each in columns:
            if each == fieldname:
                return row, cnt
            cnt += 1
    else:
        col += 1
        if col >= len(columns):
            col = 0
            row += 1
    return row, col

def unicodeToStr(value):
    res = ""
    try:
      res = str(value)
    except:
      res = repr(value)
    return res

def getScriptDirs(level=None):
    import Embedded_OpenOrange
    return Embedded_OpenOrange.getScriptDirs()

def getWindowFileName(windowname):
    res = ""
    sdirs = getScriptDirs()
    recname = windowname
    if recname.endswith("Window"): recname = recname[:-6]
    for sd in sdirs:
      try:
        f = open(sd + "/interface/" + recname + ".window.xml")
        f.close()
        res = sd + "/interface/" + recname + ".window.xml"
        break
      except:
        pass
    return res

def getWindowXML(windowname):
    fname = getWindowFileName(windowname)
    if fname:
      try:
        return open(fname,'r').read()
      except:
        pass
    return None

def splitSet(text):
    return filter(lambda y: y != "", map(lambda x: x.strip(), text.split(',')))

def bringSetting(name):
    exec("from %s import %s" % (name, name))
    exec("res = %s.bring()" % name)
    return res

def clearBuffers():
    from core.Buffer import RecordBuffer
    RecordBuffer.reset()

def processExpectedError(e, context={}, do_rollback=True):
    if (do_rollback): rollback()
    if e.shouldBeProcessed():
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        selection = [tr("Continue"), tr("Show Technical Detail")]
        res = getSelection(str(e), tuple(selection))
        if res == selection[1]:
            if hasattr(e, "server_traceback"):
                err = "<b>Server Traceback</b><hr/><br>\n"
                err += '<font color="blue">'
                err += e.server_traceback.replace("<","&lt;")
                err += '</font>'
            else:
                import traceback
                import StringIO
                s = StringIO.StringIO()
                traceback.print_exc(file=s)
                err = s.getvalue().replace("<","&lt;")
            showError(err)

def processUnexpectedError(e, context={}, msg=None, do_rollback=True):
    if (do_rollback): rollback()
    if graphicModeEnabled():
        from LocalSettings import LocalSettings
        ls = LocalSettings.bring()
        if ls.UserMode == 0: #normal user
            if not msg: msg = "OpenOrange has detected an error, in the case of repeated appearances please contact our Support.<br>We apologize for the inconveniences."
            if runningInBackground():
                postMessage(msg)
            else:
                prompt = tr(msg)
                selections = [tr("Continue"), tr("Show Technical Detail"), tr("Send Information to Support")]
                res = getSelection(prompt, tuple(selections))
                if res == selections[1] :
                    if hasattr(e, "server_traceback"):
                        err = "<b>Server Traceback</b><hr/><br>\n"
                        err += '<font color="blue">'
                        err += e.server_traceback.replace("<","&lt;")
                        err += '</font>'
                    else:
                        import traceback
                        import StringIO
                        s = StringIO.StringIO()
                        traceback.print_exc(file=s)
                        err = s.getvalue().replace("<","&lt;")
                    showError(err)
                elif res == selections[2]:
                    import Web
                    from Mail import Mail
                    import traceback
                    import StringIO
                    s = StringIO.StringIO()
                    traceback.print_exc(file=s)
                    mail = Mail()
                    mail.defaults()
                    mail.MailTo = "info@openorange.com.ar"
                    mail.Subject = "Error captured by OpenOrange"              # always use plain english
                    mail.MessageBody = "<p><b>Context Information:</b></p>"
                    for ctx in context:
                        mail.MessageBody += "<li>%s: %s</li>" % (Web.escapeXMLValue(ctx),Web.escapeXMLValue(context[ctx]))
                    mail.MessageBody += "<p><b>Error Information:</b></p><p>%s</p>" % s.getvalue()
                    mail.MessageBody += "<p><b>Settings Information:</b></p><p>%s</p>" % Web.escapeXMLValue(open(getSettingsFileName()).read()).replace('\n','<br>')
                    from MailWindow import MailWindow
                    w = MailWindow()
                    w.setRecord(mail)
                    w.open()
                    try:
                        if w.send():
                            w.close()
                    except Exception, e:
                        showError("An unexpected error occurred")
        elif ls.UserMode == 1: #developer
                import traceback
                import sys
                import StringIO
                s = StringIO.StringIO()
                lastframe = sys.exc_info()[2]
                while lastframe.tb_next: lastframe = lastframe.tb_next
                import os
                traceback.print_exc(file=s)
                err = s.getvalue()
                try:
                    open("./tmp/last_python_error.txt","wb").write(err)
                except:
                    pass
                if sys.platform.startswith("win") or sys.platform.startswith("lin"):
                    try:
                        from DevelopLocalSettings import DevelopLocalSettings
                        ds = DevelopLocalSettings.bring()
                        if ds.Editor == 0: raise
                        if askYesNo("<p><b>Error!</b></p><p>%s</p><p>Abrir archivo?</p>" % err):
                            if ds.Editor == 1: #textpad
                                os.spawnl(os.P_NOWAIT , os.path.join(ds.EditorPath, "textpad.exe"), "textpad.exe", "%s(%i,1)" % (lastframe.tb_frame.f_code.co_filename, lastframe.tb_frame.f_lineno))
                                showError("<p><b>Error</b></p><p>%s</p>" % err)
                    except Exception, e:
                        if askYesNo("<p><b>Error</b></p><p>%s</p><p>Abrir archivo?</p>" % err):
                            os.startfile("%s" % lastframe.tb_frame.f_code.co_filename)
                            showError("<p><b>Error</b></p><p>%s</p>" % err)
                else:
                    showError("<p><b>Error</b></p><p>%s</p>" % err)
    else:
        import traceback
        import StringIO
        s = StringIO.StringIO()
        traceback.print_exc(file=s)
        #print s.getvalue()


def processDBError(e, context={}, msg=None):
    try:
        processUnexpectedError(e, context, msg, True) #intento manejar el error y hacer rollback
    except DBConnectionError, ee:
        processUnexpectedError(e, context, msg, False) #hubo un problema de conexion, manejo el error sin hacer el rollback
    if isinstance(e, DBConnectionError):
        import threading
        db = Database.getCurrentDB(False)
        if db: db.releaseConnection(threading.currentThread(), DROP_CONNECTION=True)

def getMaxSQLQueryLength():
    q = Query()
    q.sql = "show variables like 'max_allowed_packet'"
    if q.open():
        return int(q[0].Value)

def setMaxSQLQueryLength(v):
    try:
        q = Query()
        q.sql = "set global max_allowed_packet=%i" % v
        return q.execute()
    except DBError, e:
        return False

# ifNone(x,y) => y if x is None else x
def ifNone(x,y):
    if x is None:
        return y
    return x

# ifNoneDo(x,fcn,*data) => fcn(*data) if x is None else x
def ifNoneDo(p1, fcn, *data):
    if p1 != None:
        return p1
    return fcn(*data)

# ifException (default, fcn, *params) => fcn (*params), o default si ocurre excepcion.
def ifException(default, fcn, *params):
    try:
        ret = fcn (*params)
    except:
        ret = default
    return ret

# retorna la primer coincidencia.
def index(function, sequence):
    """ index (function, sequence) => index or -1
    Parametros:
        function: function(e) =>boolean.
        sequence: a sequence.
    Retorna el indice del primer elemento en que function retorna True. """
    return ifException(-1,(i for i,e in enumerate(sequence) if function(e)).next)

# taskIsRunning (tname) => True if the routine named "tname" is running.
def taskIsRunning(tname):
    list = getThreadsList()
    for name in (t[1] for t in list):
        if name == tname:
            return True
    return False

def logAction(s):
    try:
        open("./tmp/actions.log","a+").write("%s [%s:%s]: %s\n" % (now(), currentUser(), currentCompanyHost(), s))
    except:
        try:
            open("./tmp/actions.log","w+").write("%s [%s:%s]: %s\n" % (now(), currentUser(), currentCompanyHost(), s))
        except:
            pass

def escapeToXml(string):
    """ Genera una representación transportable en xml del string """
    # interpreto el string, si es que ya no es unicode.
    if type(string) == str:
        string = string.decode (getDefaultStringCodec())
    # genero una representación ascii, escapeando los caracteres no soportados.
    if string:
        string = string.encode ('ascii', 'xmlcharrefreplace')
    return string

def beforeExit():
    from HistoryManager import HistoryManager
    HistoryManager.saveHistory()

def beforeRecompile():
    from HistoryManager import HistoryManager
    HistoryManager.saveHistory()
    from Company import Company
    try:
        cPickle.dump(Company.getLoguedCompanies(), open("./tmp/lc.tmp","wb"))
    except IOError, e:
        pass

def afterRecompile():
    from Company import Company
    c = Company.getCurrent()
    if c.isApplicationServerCompany():
        from ServerEventListener import ServerEventListener
        sel = ServerEventListener()
        sel.start()


def getPlatform():
    """ Retorna la plataforma actual:
        - linux
        - mac
        - windows
    """
    import sys
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("darwin"):
        return "mac"
    elif sys.platform.startswith("win"):
        return "windows"
    return None

#jaa. Para abrir un archivo con su aplicacion asociada en el sistema.
def __startCMD():
    from OpenOrange import getPlatform
    platform = getPlatform ()
    cmdByPlatform = {"windows":"start","linux":"xdg-open","mac":"open"}
    return cmdByPlatform.get (getPlatform ())

def openFile(filename):
    import os
    platform = getPlatform ()
    if (platform in ("linux")):
        filename = filename.replace(" ",r"\ ")
    os.system (__startCMD ()+" "+filename)

__trace__ = []
__trace_files__ = {}
def doTrace(frame, event, args):
    global __trace__
    global __trace_files__
    try:
        if not __trace_files__.has_key(frame.f_code.co_filename):
            __trace_files__[frame.f_code.co_filename] = open(frame.f_code.co_filename).readlines()
        locs = {}
        for var in frame.f_locals:
            if var != "globals":
                try:
                    cPickle.dumps(frame.f_locals[var])
                    locs[var] = frame.f_locals[var]
                except cPickle.PicklingError, e:
                    locs[var] = frame.f_locals[var].__class__.__name__ + ": " + str(frame.f_locals[var])
        __trace__.append((now().strftime("%H:%M:%S"), str(event), frame.f_code.co_filename, frame.f_code.co_name, frame.f_lineno-1, locs))
    except Exception, e:
        #print e
        pass
    return doTrace

def toggleTracing():
    global __trace__
    if len(__trace__):
        endTracing()
    else:
        startTracing()

def startTracing():
    #print "starting trace"
    global __trace__
    __trace__ = []
    __trace_files = {}
    sys.settrace(doTrace)

def endTracing():
    sys.settrace(None)
    global __trace__
    from Mail import Mail
    mail = Mail()
    mail.defaults()
    t = []
    for r in __trace__:
        source_line = ""
        try:
          source_line = __trace_files__[r[2]][r[4]].replace('\n','')
        except:
            pass
        t.append("%s\t%s\t%s\t%s" % (r[1], r[2], r[3], source_line))
    from TraceRecorder import TraceRecorder
    from TraceRecorderWindow import TraceRecorderWindow
    tr = TraceRecorder()
    tr.Date = today()
    tr.Time = now()
    tr.User = currentUser()
    import cPickle
    tr.Data = cPickle.dumps((__trace__, __trace_files__))
    trw = TraceRecorderWindow()
    trw.setRecord(tr)
    trw.open()
    __trace__ = []
    __trace_files = {}
    #print "trace ended"

    
#def setCurrentCompany(companycode):
#    from Company import Company
#    company = Company.bring(companycode)
#    if not company: return company
#    q = Query()
#    q.sql = "USE %s" % company.getDatabaseName()
#    return q.execute()

def switchCompanyClicked():
    from Company import Company
    options = []
    loguedcompanies = filter(lambda x: x[0] != currentCompany() or x[2] != currentUser(), Company.getLoguedCompanies())
    for lc in loguedcompanies:
        options.append("%s: %s (%s)" % (lc[0], lc[1], lc[2]))
    if len(options):
        opt = None
        if len(options) == 1:
            opt = options[0]
        else:
            opt = getSelection("Select company", tuple(options))
        if opt:
            i = options.index(opt)
            company = Company.bring(loguedcompanies[i][0])
            if company:
                clearBuffers()
                company.DefaultUser = loguedcompanies[i][2]
                company.DefaultUserPassword = loguedcompanies[i][3]
                company.setCurrent()

def commit():
    Database.getCurrentDB().commit()

def rollback():
    Database.getCurrentDB().rollback()

def rollback_fromC():
    try:
        Database.getCurrentDB().rollback()
        return True
    except DBError, e:
        processDBError(e, {}, str(e))
    except AppException, e:
        #message(e)
        e.kwargs["ShouldBeProcessed"] = True
        processExpectedError(e, {}, False)
        

def printTraceback():
    b = a

def releaseDatabaseFromThread_fromC():
    import threading
    if hasattr(threading.currentThread(), "database"):
        threading.currentThread().database.releaseConnection(threading.currentThread())

def convertHTMLToPDF(htmlstring, path):
      import ho.pisa as pisa
      from StringIO import StringIO
      res = StringIO()
      pdf = pisa.CreatePDF(htmlstring, res, path)
      if not pdf.err:
        return res.getvalue()
      else:
        return None

def getRoutine(routinename, background=False, runOnServer=False, spec=None):
    try:
        from Company import Company
        exec("from %s import %s as cls" % (routinename, routinename))
        routine = cls(spec)
        routine.setRunOnServer(bool(runOnServer and Company.getCurrent().isApplicationServerCompany()))
        routine.setBackground(background)
        return routine
    except DBError, e:
        processDBError(e, {}, utf8(e))

def runRoutine(routinename, background=False, showWindow=False, runOnServer=False, spec=None):
    try:
        routine = getRoutine(routinename, background, runOnServer, spec)
        routine.open(showWindow)
        return routine
    except DBError, e:
        processDBError(e, {}, utf8(e))

def synchronizeRecord(recordname, force=True, silence=False):
    from database.Database import Database
    db = Database.getCurrentDB()
    return db.synchronizeRecord_fromC(recordname, force, silence)
    
def es2en(mystring):
    dic = {233:"e",243:"o",239:"i",225:"a",201:"E",211:"O",205:"I",193:"A",241:"n",209:"N"}
    res = ""
    for letter in mystring:
        res += dic.get(ord(letter),letter)
    return res

__oo_version__ = None
def getVersion():
    global __oo_version__
    if not __oo_version__:
        s = open("version.txt","r").read()
        import re
        mo = re.search(".*(Repo|Develop).*(\d+)\.(\d+)\.(\d+).*", s)
        __oo_version__ = (mo.group(1).lower(), (int(mo.group(2)), int(mo.group(3)), int(mo.group(4))))
    return __oo_version__

def isRepoVersion():
    return getVersion()[0] == "repo"

def isDevelopVersion():
    return getVersion()[0] == "develop"

def setInSet(checkset, intoset, checkall=False):
    cset = map(lambda a: a.strip(), checkset.split(","))
    iset = map(lambda a: a.strip(), intoset.split(","))
    for sset in cset:
        if (sset in iset and not checkall): return True
        elif (not sset in iset and checkall): return False
    return checkall

def makeSetFieldFilter(table, field, value, isnot=False):
    if (not isnot):
        likestr  = "%s.%s = s|%s| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%%,%s| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%s,%%| \n" %(table,field,value)
        likestr += "OR %s.%s LIKE s|%%,%s,%%| " %(table,field,value)
    else:
        likestr = " %s.%s != s|%s| \n" %(table,field,value)
        likestr += "AND %s.%s NOT LIKE s|%%,%s| \n" %(table,field,value)
        likestr += "AND %s.%s NOT LIKE s|%s,%%| \n" %(table,field,value)
        likestr += "AND %s.%s NOT LIKE s|%%,%s,%%| " %(table,field,value)
    return likestr

def utf8(value):
    if isinstance(value, unicode):
        return value.encode("utf8")
    elif isinstance(value, str):
        return unicode(value, 'utf8', errors='replace')
    elif isinstance(value, DBError):
        return utf8(value.__str__())
    else:
        try:
            return unicode(value, 'utf8', errors='replace')
        except:
            try:
                s = str(value)
            except:
                s = repr(value)
            return unicode(s, 'utf8', errors='replace')

def expireVersion(a,b=0,c=0):
    def wrap(fn):
        def decorated_funcion(*args, **kwargs):
            if getVersion()[1] >= (a,b,c):
                message("Method '%s' in %s expired since version %s.%s.%s. Please contact OpenOrange." % (fn.func_name,fn.__module__, a,b,c))
            return fn(*args, **kwargs)
        return decorated_funcion
    return wrap
    
def openOOCase():
    from OOCaseWindow import OOCaseWindow
    from OOCase import OOCase
    w = OOCaseWindow()
    c = OOCase()
    c.defaults()
    w.setRecord(c)
    w.open()
    
def openUTF8(fn, mode="r"):
    import codecs
    return codecs.open(fn, mode, "utf8")

def setCurrentCompany_fromC(company):
    #only called when company has ApplicationType = 1
    try:    
        srv = company.getServerConnection(False)
        if srv:
            return company.setCurrent()
        else:
            message(tr("Connection to server not established"))
            return False
    except AppException, e:
        #message(e)
        e.kwargs["ShouldBeProcessed"] = True
        processExpectedError(e)
    except DBError, e:
        processDBError(e, {}, utf8(e))
    except Exception, e:
        processUnexpectedError(e, {"method": "getServerConnection", "class": str(company.__class__)})
    return False

def checkEvents():
    from core.Event import Event
    evs = []
    while not Event.client_queue["ChatMessage"].empty():
        ev = Event.client_queue["ChatMessage"].get()
        evs.append(ev)
    if len(evs):
        w = None
        for ww in getOpenWindowsList():
            if ww.name() == "OOChatClientWindow" and ww.getRecord().ToUsers == ev.user:
                w = ww
                break
        if not w:
            from OOChatClientWindow import OOChatClientWindow
            from OOChatClient import OOChatClient
            w = OOChatClientWindow()
            r = OOChatClient()
            r.ToUsers = ev.user
            w.setRecord(r)  
            w.open()        
        for ev in evs:
            w.addMessage(ev)
        w.getRecord().setFocusOnField("Message")                    
        



        
