#encoding: utf-8
from OpenOrange import *
from Routine import Routine
import SocketServer
import sys
import cPickle
import struct
import socket
import threading

class CAppClientThread(CThread):

    def run(self):
        disableMessages()
        self.target(*self.args)
        

class ApplicationServerRequestHandler(SocketServer.StreamRequestHandler):

    def __init__(self, thread, request, client_address, server):
        self.thread = thread #must be before the parent __init__
        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)
        
    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        self.connection.settimeout(2)
        
    def send(self, s):
        sysprint("6_1_1_1")
        self.wfile.write(struct.pack("!l", len(s)))
        sysprint("6_1_1_2")
        self.wfile.write(s)
        sysprint("6_1_1_3")
    
    def sendObject(self, obj):
        sysprint("6_1_1")
        self.send(cPickle.dumps(obj))
        sysprint("6_1_2")
    
    def receive(self):
        sysprint("4_1_1")
        lengthstr = ""
        tm = now()
        while True:
            sysprint("4_1_2 %s" % len(lengthstr))
            lengthstr += self.connection.recv(4 - len(lengthstr))
            sysprint("4_1_3 %s"  % len(lengthstr))
            if len(lengthstr) == 4: break
            sysprint("4_1_4 %s"  % len(lengthstr))
            if len(lengthstr) == 0 and now() - tm > timedelta(seconds=10):
                sysprint("4_1_5 %s"  % len(lengthstr))
                raise socket.timeout
            sysprint("4_1_6 %s"  % len(lengthstr))
        sysprint("4_1_7")
        length = struct.unpack("!l",lengthstr)[0]
        sysprint("4_1_8")
        res = ""
        while True:
            sysprint("4_1_9 %s" % len(res))
            res += self.connection.recv(length - len(res))
            sysprint("4_1_10 %s" % len(res))
            if len(res) == length: break
            sysprint("4_1_11 %s" % len(res))
            if len(res) == 0 and now() - tm > timedelta(seconds=15):
                sysprint("4_1_12 %s" % len(res))
                raise socket.timeout
                sysprint("4_1_13 %s" % len(res))
            sysprint("4_1_14 %s" % len(res))
        sysprint("4_1_15")
        return res

    def receiveObject(self):
        sysprint("4_1")
        recstr = self.receive()
        sysprint("4_2")
        res = cPickle.loads(recstr)
        sysprint("4_3")
        return res
        
    def handle(self):
        sysprint("1")
        threading.currentThread().clientHandler = self
        self.lastrequesttime = now()
        sysprint("2")
        while not self.server.routine.shouldFinish():   
            sysprint("3")
            try:
                sysprint("4")
                command = self.receiveObject()
                sysprint("5")
                self.thread.setName("%s %s " % (currentUser(),self.thread.client_address) + str(command))
                sysprint("6")
                command.doit(self)
                sysprint("7")
                self.lastrequesttime = now()
            except socket.timeout, e:
                sysprint("8")
                if now() - self.lastrequesttime > timedelta(seconds=10):
                    sysprint("9")
                    break
                sysprint("10")
                self.thread.setName("%s %s " % (currentUser(),self.thread.client_address) + " waiting command")
                sysprint("11")
            except Exception, e:
                sysprint("12") 
                sysprint(str(e))
                self.sendObject(str(e))
                sysprint("13")
        sysprint("14")
        
class CThreadingMixIn:
    #Mix-in class to handle each request in a new thread using CThread instead of threading.

    def process_request_thread(self, thread, request, client_address):
        #Same as in BaseServer but as a thread.
        #In addition, exception handling is done here.

        try:
            self.finish_request(thread, request, client_address)
            self.close_request(request)
        except:
            self.handle_error(request, client_address)
            self.close_request(request)

    def process_request(self, request, client_address):
        #Start a new thread to process the request.
        t = CAppClientThread()
        t.setName("conexion entrando")
        t.client_address = str(client_address)
        t.target = self.process_request_thread
        t.args = (t, request, client_address)
        t.start()

    def finish_request(self, thread, request, client_address):
        #Finish one request by instantiating RequestHandlerClass.
        self.RequestHandlerClass(thread, request, client_address, self)
        
class ApplicationServer(CThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True
    
class ApplicationServerRoutine(Routine):

    def run(self):
        ss = bringSetting("ServerSettings")
        port = ss.AppServerPort
        disableMessages()
        server_class=ApplicationServer
        handler_class=ApplicationServerRequestHandler
        server_address = ('', port)

        appd = server_class(server_address, handler_class)
        appd.routine = self
        sys.stderr = sys.stdout
        for i in range(100):
            sysprint("")
        appd.socket.settimeout(2)
        while not self.shouldFinish():
            sysprint("A")
            appd.handle_request()
            sysprint("B")
        sysprint("C")
