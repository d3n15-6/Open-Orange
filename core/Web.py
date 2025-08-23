# encoding: utf-8

from OpenOrange import *
from Embedded_Web import *
import os,re, threading, sys
import cPickle
from HTMLParser import HTMLParser
import sys
import Cookie

sys.path.append("web/cgi-bin/client")

def startHTMLPage():
    WebServerStreamer.addHeader ("Content-type","text/html; charset=UTF-8")
    
def endHTMLPage():
    pass
    
def startXMLPage():
    WebServerStreamer.addHeader ("Content-type","text/xml")

def startFilePage(filename):
    ct = "application/octet-stream"
    if filename.lower().endswith("pdf"):
        ct = "application/pdf"
    elif filename.lower().endswith("doc"):
        ct = "application/msword"
    elif filename.lower().endswith("rtf"):
        ct = "application/rtf"
    elif filename.lower().endswith("zip"):
        ct = "application/zip"
    elif filename.lower().endswith("rar"):
        ct = "application/rar"
    elif filename.lower().endswith("odt"):
        ct = "application/vnd.oasis.opendocument.text"
    WebServerStreamer.addHeader ("Content-type",ct)
    WebServerStreamer.addHeader ("Content-disposition",'attachment; filename="%s"' % filename)


def endXMLPage():
    pass
    
def startTEXTPage():
    WebServerStreamer.addHeader ("Content-type","text/plain; charset=UTF-8")

def endTEXTPage():
    pass

def startJSONPage():
    WebServerStreamer.addHeader ("Content-type","application/json")

try:
    import json
except:
    pass
    

def dispatchView(locals):
    import Web
    callback = WebServerStreamer.getCallback()
    if callback:
        matchobject = WebServerStreamer.getMatchObject()
        if matchobject:
            fname = callback[0] % matchobject.groupdict()
            params = [x % matchobject.groupdict() for x in callback[1:]]
        else:
            fname = callback[0]
            params = []
        session = Session.find(getWebParams()) #para que se setee el cookie para sessiones
        locals[fname](*params)
        
class WebServerStreamer(object):
    originalstdout = None
    originalstdin = None
    wfiles = {}
    rfiles = {}
    environments = {}
    cookie = {}
    headersList = {}
    originalStdoutList = {}
    originalStdinList = {}
    callback = {}
    matchobject = {}
    
    @classmethod
    def start(objclass):
        WebServerStreamer.originalstdout = sys.stdout
        WebServerStreamer.originalstdin = sys.stdin    
        streamer = WebServerStreamer()
        sys.stdout = streamer
        sys.stdin = streamer

        
    @classmethod
    def end(objclass):
        sys.stdout = WebServerStreamer.originalstdout 
        sys.stdin = WebServerStreamer.originalstdin

    @classmethod
    def registerConnection(objclass, rfile, wfile, environment, callback, matchobject):
        #sysprint("registering connection %s" % threading.currentThread().getName())
        threadname = threading.currentThread().getName()
        WebServerStreamer.rfiles[threadname] = rfile
        WebServerStreamer.wfiles[threadname] = wfile
        WebServerStreamer.environments[threadname] = environment
        WebServerStreamer.headersList[threadname] = {}
        WebServerStreamer.cookie[threadname] = None
        WebServerStreamer.callback[threadname] = callback
        WebServerStreamer.matchobject[threadname] = matchobject

    @classmethod
    def disposeConnection(objclass):
        #sysprint("registering connection %s" % threading.currentThread().getName())
        threadname = threading.currentThread().getName()
        del WebServerStreamer.rfiles[threadname]
        del WebServerStreamer.wfiles[threadname]
        del WebServerStreamer.environments[threadname]
        del WebServerStreamer.headersList[threadname]
        del WebServerStreamer.callback[threadname]
        del WebServerStreamer.matchobject[threadname]
        
    def write(self, data):
        #sysprint("write to connection %s" % (threading.currentThread().getName()) )
        wfile = WebServerStreamer.wfiles.get(threading.currentThread().getName(), WebServerStreamer.originalstdout)
        if isinstance(data, unicode):
            wfile.write(data.encode("utf8"))
        else:
            wfile.write(data)
        
    def read(self, cnt):
        #sysprint("write from connection %s" % (threading.currentThread().getName()) )
        rfile = WebServerStreamer.rfiles.get(threading.currentThread().getName(), WebServerStreamer.originalstdin)
        return rfile.read(cnt)

    @classmethod
    def addHeader (objclass, name, value):
        #sysprint("write to connection %s" % (threading.currentThread().getName()) )
        headers = WebServerStreamer.headersList[threading.currentThread().getName()]
        headers[name]=value

    @classmethod
    def setCookie(objclass, cookie):
        WebServerStreamer.cookie[threading.currentThread().getName()] = cookie

    @classmethod
    def getCookie(objclass):
        return WebServerStreamer.cookie.get(threading.currentThread().getName(), None)

    @classmethod
    def getClientCookie(objclass):
        import Cookie
        http_cookie = objclass.getEnvironment().get("HTTP_COOKIE", "")
        return Cookie.SimpleCookie(http_cookie)

    @classmethod
    def getCallback(objclass):
        return WebServerStreamer.callback.get(threading.currentThread().getName(), None)

    @classmethod
    def getMatchObject(objclass):
        return WebServerStreamer.matchobject.get(threading.currentThread().getName(), None)

    @classmethod
    def getHeaders(objclass):
        return WebServerStreamer.headersList.get(threading.currentThread().getName(), None)

    @classmethod
    def getEnvironment(objclass):
        return WebServerStreamer.environments[threading.currentThread().getName()]

class WebServerNewStreamer(WebServerStreamer):
    @classmethod
    def start(objclass):
        WebServerStreamer.originalstdin = sys.stdin    
        
    @classmethod
    def end(objclass):
        pass
        
def webprint(data):
    try:
        wfile = WebServerStreamer.wfiles[threading.currentThread().getName()]
        if isinstance(data, unicode):
            wfile.write(data.encode("utf8"))
        else:
            wfile.write(data)   
    except AttributeError,e:
        print "Error finding output file to web"
        raise

    
def output_json(func):
    def decorated_function(*args, **kwargs):
        startJSONPage()
        webprint(json.dumps(func(*args, **kwargs)))
        return
    return decorated_function

def output_html(func):
    def decorated_function(*args, **kwargs):
        startHTMLPage()
        webprint(func(*args, **kwargs))
        return
    return decorated_function
    
    
validCharsURL = {}
"""
"\xc3\xa1":chr(225), #á
"\xc3\xa9":chr(233), #é
"\xc3\xad":chr(237), #í
"\xc3\xb3":chr(243), #ó
"\xc3\xba":chr(250), #ú
"\xc3\x81":chr(193), #Á
"\xc3\x89":chr(201), #É
"\xc3\x8d":chr(205), #Í
"\xc3\x93":chr(211), #Ó
"\xc3\x9a":chr(218), #Ú
"\xc3\xb1":chr(241), #ñ
"\xc3\x91":chr(209), #Ñ
"\xc3\xa0":chr(224), #à
"\xc3\xa8":chr(232), #è
"\xc3\xac":chr(236), #ì
"\xc3\xb2":chr(242), #ò
"\xc3\xb9":chr(249), #ù
"\xc3\x80":chr(192), #À
"\xc3\x88":chr(200), #È
"\xc3\x8c":chr(204), #Ì
"\xc3\x92":chr(210), #Ò
"\xc3\x99":chr(217), #Ù
"\xb0": chr(176), #°
}
"""

def getWebParams():
    env = WebServerStreamer.getEnvironment()
    ct = env.get("CONTENT_TYPE", None)
    params = env['PARAMS']    
    if not ct or ct.lower().find("utf-8") < 0:
        for k in params.keys():
            for urlChar in validCharsURL.keys():
                if isinstance(params[k], str):
                    params[k] = params[k].replace(urlChar,validCharsURL[urlChar]) #No sacar por favor!!! (SP)
    return params
    
def getRemoteAddress():
    add = WebServerStreamer.getEnvironment().get("REMOTE_ADDR", "unknown")
    return add
    
def getRemoteHost(): 
    host = WebServerStreamer.getEnvironment().get("REMOTE_HOST", "unknown")
    return host
    
def login(user, password, registerId = True,language = "",timedelta=None):
    params = getWebParams()
    res = False
    currentuser = curUser()
    from Person import Person
    person = Person()
    person.WebUser = user
    if person.load() and person.WebUserFlag:
        if person.WebPassword == genPassword(password):
            if not Session.sessionsId.has_key(person.Code):
                res = Session.getNewId()
                from User import User
                user = User()
                user.Person = person.Code
                if user.load():
                    setCurrentUser(user.Code)
                    log("LOGIN 1 user: %s threadid: %s" % (user.Code, id(threading.currentThread())))
                    currentuser = user.Code                
                if registerId: Session.sessionsId[person.Code] = res
                t = CleanSessionsThread()
                t.start()
                lastaccess = str(now())
                c = Cookie.SimpleCookie()
                c["__openorange_sessionid__"] = res
                c["__openorange_sessionid__"]["expires"] = "never"
                c["__openorange_last_access__"] = lastaccess
                c["__openorange_last_access__"]["expires"] = "never"        
                c["__openorange_last_access__"]["path"] = "/"
                WebServerStreamer.setCookie(c)
            else: res = Session.sessionsId[person.Code]
    if not Session.sessions.has_key(res):
        Session.sessions[res] = Session(sessionid=res, person = person, currentuser = currentuser, language = language, register=True, timedelta=timedelta)
        #sysprint(str(Session.sessions[res]))
    return res

def loginPerson(person,registerId = True,language = "",timedelta=None):
    res = False
    #loguea a una persona sin pedir password
    if person and person.WebUserFlag:
        if not Session.sessionsId.has_key(person.Code):
            res = Session.getNewId()
            from User import User
            currentuser = curUser()
            user = User()
            user.Person = person.Code
            if user.load():
                setCurrentUser(user.Code)
                log("LOGIN 1 user: %s threadid: %s" % (user.Code, id(threading.currentThread())))
                currentuser = user.Code
            Session.sessions[res] = Session(sessionid=res, person = person, currentuser = currentuser, language = language, register=True, timedelta=timedelta)
            session = Session.sessions[res]
            if registerId: Session.sessionsId[person.Code] = res
            t = CleanSessionsThread()
            t.start()
            session.lastaccess = str(now())
            c = Cookie.SimpleCookie()
            c["__openorange_sessionid__"] = session.id
            c["__openorange_sessionid__"]["expires"] = "never"
            c["__openorange_last_access__"] = session.lastaccess
            c["__openorange_last_access__"]["expires"] = "never"        
            c["__openorange_last_access__"]["path"] = "/"
            WebServerStreamer.setCookie(c)
        else: res = Session.sessionsId[person.Code]
    return res

def transformXML_fromString(xml, xmlpath):
    from Ft.Xml.Xslt.Processor import Processor
    from Ft.Xml.InputSource import DefaultFactory
    from Ft.Lib import Uri
    xsltproc = Processor()
    res = xsltproc.run(DefaultFactory.fromString(xml,Uri.OsPathToUri(xmlpath)))
    return res

def transformXML_fromFile(filename):
    from Ft.Xml.Xslt.Processor import    Processor
    from Ft.Xml.InputSource import DefaultFactory
    from Ft.Lib import Uri
    xsltproc = Processor()
    res = xsltproc.run(DefaultFactory.fromUri(Uri.OsPathToUri(filename)))
    return res

reservedXMLChars = {'&':'&amp;' , '<':'&lt;' , '>':'&gt;' , '"':'&#034;' , "'":'&#039;'}
reserved2anciiChars = {'&#38;':'&' , '&#60;':'<' , '&#62;':'>' , '&#034;':'"' , '&#039;':"'"}

def convert2XMLChar(char):
    if ord(char) >= 127: return ('&#'+str(ord(char))+';')
    return reservedXMLChars.get(char,char)

def escapeXMLValue(value):
    strOut = ""
    for char in utf8(value):
        strOut+=convert2XMLChar(char)
    return strOut

def convert2anciiChar(htmlChar):
    num=int(htmlChar[2:-1])
    if num >= 127: return chr(num)
    return reserved2anciiChars.get(htmlChar,htmlChar)

def decriptXMLValue(value):
    strOut = ""
    htmlChar = ""
    for char in str(value):
        if (htmlChar or char == "&"):
            htmlChar = char
        if (char == ";"):
            #htmlChar : &#iii;
            sysprint("htmlChar: %s"%htmlChar)
            strOut += convert2anciiChar(htmlChar)
            htmlChar = ""
        strOut += char
    return strOut

def XMLAttr(value):
    return '"' + escapeXMLValue(value) + '"'
 
def parseRichText(string):
    string = re.sub("<html[^>]*>.*<body[^>]*>",'<div>',string,1) 
    string = re.sub("</body>.*</html>",'</div>',string,1) 
    return string

evaltag = re.compile("<\?eval([^:]*?): (.*?)\?/?>((.*?)</\?eval\\1>)?", re.S)
iteratetag = re.compile("<\?iterate([^:]*?): (.*?)\?/?>((.*?)</\?iterate\\1>)?", re.S)
def parsePythonTags(html, globals, locals):    
    #parse iterate tag
    res = []
    pos = 0
    end = 0
    for mo in iteratetag.finditer(html):
        i=0
        codestr = mo.group(2)
        content = mo.group(4)
        globals["__content__"] = content
        res.append(html[pos:mo.start(0)])
        iterator = eval(codestr, globals, locals)
        try:
            v = iterator.next()
            while True:
                if isinstance(v, str):
                    v = unicode(v, "utf8", errors="replace")
                elif not isinstance(v, unicode):
                    v = str(v)
                res.append(v)
                v = iterator.next()
        except StopIteration:
            pass
        i += 1
        pos = mo.end(0)
    res.append(html[pos:])
    #end of parse iterate tag
    html = ''.join(res)
    #parse eval tag
    res = []
    pos = 0
    end = 0
    for mo in evaltag.finditer(html):
        i=0
        codestr = mo.group(2)
        content = mo.group(4)
        globals["__content__"] = content
        res.append(html[pos:mo.start(0)])
        repl = eval(codestr, globals, locals)
        if isinstance(repl, str):
            repl = unicode(repl, "utf8", errors="replace")
        elif not isinstance(repl, unicode):
            repl = str(repl)
        res.append(repl)
        i += 1
        pos = mo.end(0)
    res.append(html[pos:])
    #end of parse eval tag
    return ''.join(res)


global websettings
websettings = None
def getWebSettings():
    global websettings
    if not websettings:
        from WebSettings import WebSettings 
        websettings = WebSettings.bring()
    return websettings

global alt_baseurl
alt_baseurl = None
def getAlt_BaseURL():
    global alt_baseurl
    if not alt_baseurl:
        alt_baseurl = 'http://%s:%i/' % (getWebSettings().AlternativeWebServerPrefix, getWebSettings().AlternativeWebServerPort)
        if getWebSettings().AlternativeWebServerLabel:
            alt_baseurl += websettings.AlternativeWebServerLabel + "/"
    return alt_baseurl

global altwspattern_src
altwspattern_src= None
def getAltWSPattern():
    global altwspattern_src
    if not altwspattern_src:
        altwspattern_src = re.compile(' *= *[",\']../([^",^\']*[^.py][^.html][^.htm])[",\']', re.S) #Alternative Web Server Match Pattern
    return altwspattern_src
    
def parseAltWSURL(html):
     #parse Alternative Server URLs
     res = []
     pos = 0
     end = 0
     for mo in getAltWSPattern().finditer(html):
         url = getAlt_BaseURL() + mo.group(1)
         res.append(html[pos:mo.start(0)])
         res.append('="%s"' % url)
         pos = mo.end(0)
     res.append(html[pos:])
     return ''.join(res)

class Basket:

    def reloadCustomerData(self,person):
        self.pricedeal = ""
        self.currency = ""
        self.custcode = ""
        cs = bringSetting("OurSettings")
        if cs: self.currency = cs.BaseCur1
        if person:
            from Customer import Customer
            cust = Customer.bring(person.CustCode)
            if cust:
                self.custcode = cust.Code
                if cust.PriceDeal: self.pricedeal = cust.PriceDeal
                if cust.Currency: self.currency = cust.Currency   
            from WebSettings import WebSettings
            ws = WebSettings.bring()
            if ws.AnonymousPerson == person.Code:
                if ws.PriceDealAnonymousPerson: self.pricedeal = ws.PriceDealAnonymousPerson
                if ws.CurrencyAnonymousPerson: self.currency = ws.CurrencyAnonymousPerson      

    def __init__(self, person):
        self.items = {}
        self.decimals = 2
        self.itemsQty = 0;     
        self.soNr = None #para los casos en los que ya existe la orden y se va a modificar
        self.reloadCustomerData(person)
    
    def getSoNr(self):
        return self.soNr
    
    def setSoNr(self,sonr):
        self.soNr = sonr
        
    def setItem(self, artcode, qty):
        if qty != 0:
            from Item import Item
            item = Item.bring(artcode)
            if item:
                itd = {}
                itd["code"] = artcode
                itd["qty"] = qty
                from Customer import Customer
                cust = Customer.bring(self.custcode)
                price = 0
                try:
                    price = float(item.getPrice(today(),self.pricedeal, self.currency, qty))
                except:
                    price = 0

                from PriceDeal import PriceDeal
                priceDealRecord = PriceDeal.bring(self.pricedeal)
                #Como los precios de la pag son sin iva, en el caso de los clientes IVA incluido les saco el iva al precio que se muestra
                if cust and priceDealRecord and priceDealRecord.InclVAT == 1: #Incluided
                    from VATCode import VATCode
                    vatCode = VATCode.getSLCode(item,cust.Code)
                    if (item.VATCode):
                        vatCode = item.VATCode
                    vatRecord = VATCode.bring(vatCode) 
                    if vatRecord and vatRecord.Percent:
                        price = 100 * price / (vatRecord.Percent + 100)

                itd["price"] = price
                ddeal = None
                if cust:
                    from DiscountDeal import DiscountDeal
                    ddeal = DiscountDeal.bring(cust.DiscountDeal)
                disc = 0
                if (ddeal):
                    disc = ddeal.getDiscount(today(),artcode,qty,itd["price"])
                    if (ddeal.Type==1):
                        MarkupDiscount = disc
                        disc = pasteMarkupDiscount(artcode,itd["price"],MarkupDiscount)
                itd["name"] = item.Name
                itd["total"] = (itd["qty"] * itd["price"]) * (100.0-disc)/100
                itd["price"] = itd["price"] * (100.0-disc)/100
                from VATCode import VATCode
                vatcode = VATCode.getSLCode(item,self.custcode)
                vatCodeRec = VATCode.bring(vatcode)
                if vatCodeRec:
                    itd["iva"] = itd["total"] * (1+vatCodeRec.Percent/100)
                else:
                    itd["iva"] = itd["total"]
                self.items[artcode] = itd
        else:
            if self.items.has_key(artcode):
                self.items.pop(artcode)
    
    def clear(self):
        self.items.clear()
        
    def copy(self,basket):
        for item in basket.items.values():
            self.setItem(item["code"], item["qty"])
    
        
    def getXML(self):
        xml = []
        total = 0
        itemsQty = 0
        iva = 0
        for artcode in self.items:
            total += self.items[artcode]["total"]
            iva += self.items[artcode]["iva"]
            itemsQty += 1

        xml.append("<basket sonr=\"%s\" total=\"%s\" iva=\"%s\" itemsQty=\"%i\">" % ( str(self.getSoNr()), round(total,self.decimals) ,round(iva,self.decimals), itemsQty )   )
        for artcode in self.items:
            item = self.items[artcode]
            code = item["code"]
            qty = item["qty"]
            price = item["price"]
            total = round(item["total"],self.decimals)
            itemname = item["name"]
            xml.append('<item code="%s" qty="%s" price="%s" total="%s"><![CDATA[%s]]></item>' % (code,qty,price,total,itemname))
        xml.append("</basket>")
        return xml
    
    def getHeaderXML(self):
        xml = []
        total = 0
        itemsQty = 0
        iva = 0
        for artcode in self.items:
            total += self.items[artcode]["total"]
            iva += self.items[artcode]["iva"]
            itemsQty += 1

        xml.append("<basket sonr=\"%s\" total=\"%s\"  iva=\"%s\"  itemsQty=\"%i\">" % ( str(self.getSoNr()), round(total,self.decimals),round(iva,self.decimals), itemsQty )   )
        xml.append("</basket>")
        return xml
        
    def getItemQty(self, artcode):
        item = self.items.get(artcode, None)
        if item: return item["qty"]
        return 0
    
    def __str__(self):
        res = "Currency: %s\n" % self.currency
        res += "PriceDeal: %s\n" % self.pricedeal
        res += "SoNr: %s\n" % str(self.getSoNr())
        res += "Items: %s\n" % str(self.items)
        return res

def pasteMarkupDiscount(itemcode,price,MarkupDiscount):
    from ItemCost import ItemCost
    icost = ItemCost()
    icost.Code = itemcode
    if (icost.load()):
        cost = icost.SalesCost
    if (cost):
        Markup = 100 * (price - cost) / cost
    else:
        Markup = 0
    #recalcula Marcup
    Markup = ((100.0 - MarkupDiscount)/100.0) * Markup
    disc = pasteMarkup(price,cost,Markup)
    return disc

def pasteMarkup(price,cost,Markup):
    nPrice = cost * ((Markup/100.00) + 1.00)
    disc = 100.00 * ((price - nPrice) / price)
    return disc

class Session:
    sessions = {}
    sessionsId = {} #personCode:sessionid
    xml_rootCat = {} #E-Commerce: estructura de categorías (se limpia con borrar buffers)

    @classmethod
    def find(classobj, params={}):        
        Session.cleanSessions()
        cc = WebServerStreamer.getClientCookie()
        if cc.has_key("__openorange_sessionid__"):
            sid = cc["__openorange_sessionid__"].value
        else:
            sid = params.get("__sessionid__","")
        try:
            session = Session.sessions[sid]
        except KeyError, e:
            session = Session("",None,curUser(),params.get("language","en"), register=True)
        import threading
        threading.currentThread().currentUser = session.getCurrentUser()
        session.lastaccess = str(now())
        c = Cookie.SimpleCookie()
        c["__openorange_sessionid__"] = session.id
        c["__openorange_sessionid__"]["expires"] = "never"
        c["__openorange_last_access__"] = session.lastaccess
        c["__openorange_last_access__"]["expires"] = "never"        
        c["__openorange_last_access__"]["path"] = "/"
        WebServerStreamer.setCookie(c)
        return session

    @classmethod
    def getSession (classobj, sessionId):
        #acá no hay que modificar el lastaccess!! sino nunca se podría consultar (SP). Solo se modifica en el login y en el find
        return Session.sessions.get (sessionId, None)

    @classmethod
    def getPersonSession (classobj, p):
        #acá no hay que modificar el lastaccess!! Solo se modifica en el login y en el find
        if p:
            return Session.sessions.get (Session.sessionsId.get(p.Code,None), None)
        return None

    @classmethod
    def registerSession (classobj, session):
        sdict = Session.sessions
        if sdict.has_key (session.getId()):
            return False
        sdict[session.getId()]=session
        return True
        
    #pbd, y sp: lo moví acá, pero fijensé que cuando termina esta clase declaro
    # una referencia a este método a nivel de clase para no romper con la 
    # interfaz actual.
    @classmethod
    def getNewId (cObj):
        import md5
        n = now()
        res = md5.new(n.isoformat()).hexdigest()
        return res

    @classmethod
    def cleanSessions(classobj):
        iterateAndCleanSessions()
        #no lo hago como Thread porque ahora lo checkeo desde el Session.find
        #t = SerializeThread()
        #t.start()

    def __init__(self, sessionid="", person = None, currentuser = None, language = "", register=False,timedelta=None):
        if not sessionid:
            self.id = Session.getNewId ()
        else:
            self.id = sessionid
        self.person = person
        self.currentuser = currentuser
        self.basket = Basket(person)
        self.lastaccess = str(now())
        self.records = {}
        self.windows = {}
        self.reports = {}
        self.lang = ""
        self.timedelta = timedelta
        if self.timedelta == None:
            self.loadWebSettingsTimeDelta()# Carga el tiempo de caducidad de la session según seteos Web
        if language:
            #self.lang = language[0:2]
            self.lang = 'en' #cambiar
        self.__sessionData ={}
        if register:
            Session.registerSession (self)

    def __del__ (self):
        self.close ()

    # le da la capacidad de acceder a las variables de session por medio de los
    # indices como si fuera un diccionario. s["varname"]
    def __getitem__ (self, key):
        return self.getSessionVar(key)

    # para setear variables de sesion por medio de indices como si fuera un 
    # diccionario. s["varname"]=1000
    def __setitem__ (self, key, value):
        self.setSessionVars (**{key:value})

    def __str__(self):
        res = "--------------\n"
        res += "Session <%s>\n" % self.id
        res += "Last Access: %s\n" % self.lastaccess
        res += "Time Delta: %s\n" % self.timedelta
        res += "Person: %s\n" % self.person
        res += "Customer: %s\n" % self.getCustomer()
        res += "User: %s\n" % self.currentuser
        res += "Basket: %s\n" % self.basket
        res += "--------------\n"
        return res

    def isExpired(self):
        if str(self.lastaccess) < str(now() - self.timedelta):
            return True
        return False
    
    def loadWebSettingsTimeDelta(self):
        from datetime import timedelta
        ws = bringSetting("WebSettings")
        ws_days,ws_hours,ws_minutes,ws_seconds = 0,0,0,0
        if ws.SessionTimeOutDays != None: ws_days = ws.SessionTimeOutDays
        if ws.SessionTimeOutTime != None:
            timelist = str(ws.SessionTimeOutTime).split(":")
            ws_hours,ws_minutes,ws_seconds = int(timelist[0]),int(timelist[1]),int(timelist[2])
        if (ws_days,ws_hours,ws_minutes,ws_seconds) == (0,0,0,0):
            #si está todo en cero, por defecto pongo 2 dias
            ws_days = 2
        self.timedelta = timedelta(days=ws_days,hours=ws_hours,minutes=ws_minutes,seconds=ws_seconds)

    def logued(self):
        return (self.person != None)

    def login(self, webuser, webpassword):
        self.person = None
        self.currentuser = curUser()
        from Person import Person
        person = Person()
        person.WebUser = webuser
        res = False
        if person.load():
            if person.WebPassword == genPassword(webpassword):
                self.person = person            
                res = True
                from User import User
                user = User()
                user.Person = person.Code
                if user.load():
                    self.currentuser = user.Code                
                    setCurrentUser(user.Code)
        return res
        
    def close(self):
        if self.sessions.has_key(self.id): del self.sessions[self.id]
        if self.person and self.sessionsId.has_key(self.person.Code): del self.sessionsId[self.person.Code]

    def getId(self):
        return self.id
        
    def getWebUser(self):
        if self.person:
            return self.person.WebUser
        else:
            return ""
    
    def getName(self):
        if self.person:
            return self.person.Name + " " + self.person.LastName
        else:
            return ""
    def getPerson (self):
        #hay que traerlo de la base para que no quede desactualizado
        from Person import Person
        self.person =  Person.bring(self.person.Code)
        return self.person

    def getCustomer (self):
        if self.person and self.person.ContactType == 0:
            from Customer import Customer
            return Customer.bring(self.person.CustCode)
        return None
    
    def getCurrentUser(self):
        return self.currentuser
        
    def currentUserCanDo(self,actionname,default=True):
        from User import User
        user = User.bring(self.getCurrentUser())
        if user: return user.canDo(actionname,default)
        return default
        
    def getXML(self):
        return "<session user=\"%s\" name=\"%s\" id=\"%s\"/>" % (self.getWebUser(), self.getName(), self.getId())

    def addRecord(self, record, id = None):
        if not id: id = Session.getNewId()
        self.records[id] = record
        record.recordid = id
        record.session = self
        return id

    def getRecord(self, recordid, default=None):
        return self.records.get(recordid,default)

    def addWindow(self, window, id = None):
        if not id: id = Session.getNewId()
        self.windows[id] = window
        window.windowid = id
        window.session = self
        window.getRecord = window.webGetRecord
        window.setRecord = window.webSetRecord
        window.name = window.webName
        window.getOriginalTitle = window.webGetOriginalTitle
        window.setFieldDecimals = window.webSetFieldDecimals
        window.setRowFieldDecimals = window.webSetRowFieldDecimals
        window.getReportView = window.webGetReportView
        return id
        
    def getWindow(self, windowid, default=None):
        return self.windows.get(windowid,default)

    def addReport(self, report, id = None):
        # GS: Comento estas lineas porque estan tirando el OpenOrange que
        # funciona como servidor web al usar este metodo.
        #if not id: id = Session.getNewId()
        #self.reports[id] = report
        #report.reportid = id
        return id
        
    def getReport(self, reportid, default=None):
        return self.reports.get(reportid,default)
        
    def getLabelRoot(self):
        #E-Commerce
        labelRoot = ""
        from Label import Label
        if self.person and self.person.LabelType:
            l = Label()
            l.Level = 0
            l.Type = self.person.LabelType
            if l.load():
                labelRoot = l.Code
        if not labelRoot:
            ws = bringSetting("WebSettings")
            if ws and ws.LabelType:
                l = Label()
                l.Level = 0
                l.Type = ws.LabelType
                if l.load():
                    labelRoot = l.Code
        return labelRoot

    def addSessionVars (self, **data):
        for k in data.keys():
            if not k in self.__sessionData.keys():
                self.__sessionData[k] = data[k]
    #agrega datos pisando valores
    def setSessionVars (self, **data):
       dict.update(self.__sessionData, data) 
       
    def getSessionVar(self, name):
        try:
            return self.__sessionData[name]
        except:
            return None
            
    def getSessionVarNames (self):
        return self.__sessionData.keys ()
        
    def removeSessionVars (self, *varNames):
        for vname in varNames:
            try:
                self.__sessionData.pop (vname)
            except:
                pass
                
    def clearSessionVars (self):
        self.__sessionData ={}
        
    @classmethod
    def currentUser(classobj):
        import threading
        currentthread = threading.currentThread()
        if hasattr(currentthread, "currentUser") and currentthread.currentUser:
            log("CU user: %s threadid: %s" % (threading.currentThread().currentUser, id(threading.currentThread())))
            return currentthread.currentUser
        else:
            return curUser()
    
    @classmethod
    def serializeFile(classobj):
        t = SerializeThread()
        t.start()

try:
    fh = open("session", "r")
    dic = cPickle.load(fh)
    Session.sessions = dic.get("sessions",{})
    for s in Session.sessions:
        s.reloadCustomerData(s.getPerson())
    Session.sessionsId = dic.get("sessionsId",{})
    fh.close()
except:
    pass
    #import traceback,sys
    #import StringIO
    #stringio = StringIO.StringIO()
    #traceback.print_exc(file=stringio)      
    #log(str(stringio.getvalue()))
    #log("Error al cargar session del archivo")

try:
    fh = open("xml_rootCat", "r")
    Session.xml_rootCat = cPickle.load(fh) #el archivo se renueva desde limpiarBuffer
    fh.close()
except:
    pass
    #import traceback,sys
    #import StringIO
    #stringio = StringIO.StringIO()
    #traceback.print_exc(file=stringio)      
    #log(str(stringio.getvalue()))
    #log("Error al cargar xml_rootCat del archivo")

class SerializeThread(CThread):
    def run(self):
        try:
            fh = open("session", "w")
            dic = {"sessions":Session.sessions, "sessionsId":Session.sessionsId}
            cPickle.dump(dic,fh)
            fh.close()
        except:
            import traceback,sys                
            import StringIO
            stringio = StringIO.StringIO()
            traceback.print_exc(file=stringio)      
            log(str(stringio.getvalue()))
            log("Error al serializar session")

def iterateAndCleanSessions():
    for s in Session.sessions.values():
        if s.isExpired():
            sysprint("id caducado: %s"%s.id)
            s.close()

class  CleanSessionsThread(CThread):
    def run(self):
        try:
            iterateAndCleanSessions()
        except:
            import traceback,sys                
            import StringIO
            stringio = StringIO.StringIO()
            traceback.print_exc(file=stringio)      
            log(str(stringio.getvalue()))
            log("Error al borrar sesiones")
            
#parche para no romper las llamadas externas, comentar con sp y pdb luego
getNewId = Session.getNewId()

def currentUserCanDo(classobj,actionname, default=True):
    from User import User
    if default is False: default = ErrorResponse("No esta autorizado para realizar esta operacion")
    res = User.currentCanDo(actionname,default)
    return res


def render(template_path, glb, loc, content_type="html"):
    try:
        import codecs
        fn = getWebDir() + template_path
        f = codecs.open(fn, "rb", "utf8")
        content = f.read()
        exec("start"+content_type.upper()+"Page()")
        print parsePythonTags(content, glb, loc)
    except IOError, e:
        Web.startTEXTPage()
        print "template %s no found" % template_path

class HTMLTextParser(HTMLParser):
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.message = ""

    def handle_data(self,data):
        self.message += data

class TracebackManager(object):
    tracebacks = {}