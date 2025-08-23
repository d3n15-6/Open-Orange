from Embedded_OpenOrange import *
from AppCommand import *
import socket
import struct
import cPickle
from functions import *
from datetime import datetime

class AppServerConnection:
    conn = None

    def __init__(self, company):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.settimeout(2)
        self.host = company.Host
        self.port = company.Port
        self.connected = False
        AppServerConnection.conn = self
    
    @classmethod
    def getConn(objclass, company = None):
        from core.AppServerConnection import AppServerConnection as ASC
        if not ASC.conn:
            if not company:
                from Company import Company
                company = Company.bring(currentCompany())
            ASC.conn = AppServerConnection(company)
            ASC.conn.connect()
        return ASC.conn
        
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
        except Exception, e:
            raise "No se puede establecer conexion con el servidor."
        self.__last = datetime.now()
        self.convertToClientApplication()
        self.login()
        
    def reconnect(self):
        #print "in reconnection"
        self.socket.close()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.settimeout(20)          
        return self.connect()
        
    def send(self, s, tries=2):
        try:
            #print "%s elapsed" % str(datetime.now() - self.__last)
            if datetime.now() - self.__last > timedelta(seconds=9):
                #probably the server has closed the connection so...
                #print "reconnecting..."
                self.reconnect()
            self.socket.sendall(struct.pack("!l", len(s)))
            self.socket.sendall(s)
        except:
            #print "checking tries"
            if tries > 0:
                #print "reconnecting"
                self.reconnect()
                self.send(s, tries-1)
            else:
                raise
    
    def sendObject(self, obj):
        self.send(cPickle.dumps(obj))
    
    def receive(self):
        lengthstr = ""
        while len(lengthstr) < 4:
            lengthstr += self.socket.recv(4 - len(lengthstr))
        length = struct.unpack("!l",lengthstr)[0]
        res = ""
        while (len(res) < length):
            res += self.socket.recv(length - len(res))
        self.__last = datetime.now()
        return res

    def receiveObject(self):
        recstr = self.receive()
        return cPickle.loads(recstr)
    
    def requestObject(self, command):
        self.sendObject(command)
        while True:    
            #this while exists only for receive messages from the server
            res = self.receiveObject()
            if res.__class__.__name__ == "AppCommand_ClientMessage":
                res.doit(None)
            else:
                break
        return res

    def call(self, functionname, *args, **kwargs):
        cmd = AppCommand_Call()
        cmd.functionname = functionname
        cmd.args = args
        cmd.kwargs = kwargs
        return self.requestObject(cmd)
        
    def saveRecord(self, record):
        cmd = AppCommand_SaveRecord()
        from PythonRecord import PythonRecord
        cmd.record = PythonRecord(record)
        result = self.requestObject(cmd)
        res = False
        if len(result) == 2:
            record = result[1].toRecord(record)
            result = result[0]
        return result
    
    def runRoutine(self, routine):
        from PythonRecord import PythonRecord
        cmd = AppCommand_RunRoutine()
        cmd.routinename = routine.__class__.__name__
        cmd.record = PythonRecord(routine.getRecord())
        return self.requestObject(cmd)
        
    def getDBConnInfo(self):    
        cmd = AppCommand_GetDBConnInfo()
        return self.requestObject(cmd)

    def login(self):
        cmd = AppCommand_Login()
        cmd.usercode = currentUser()
        return self.requestObject(cmd)

    def convertToClientApplication(self):
        import core.functions
        #print "getting server now"
        core.functions.server_time_difference = serverNow() - now()
        return
        """
        import Record as Record1, core.ClientRecord as ClientRecord, core.Record as Record2
        Record1.Record.__bases__ = (ClientRecord.ClientRecord,)
        Record2.Record.__bases__ = (ClientRecord.ClientRecord,)
        """
