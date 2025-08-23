#encoding: utf-8
from OpenOrange import *
import time
from core.Event import *



class ServerEventListener(CThread):

    def beforePleaseFinish(self):
        self.conn.close()
    
    def run(self):
        self.setName(self.__class__.__name__)
        from server.ProtocolInterface import ConnectionClosed
        from Company import Company
        cc = Company.getCurrent()
        if not cc.isApplicationServerCompany():
            message("Invalid Company type")
            return
                    
        self.conn = cc.createServerConnection()
        while not self.shouldFinish():
            try:
                event = self.conn.popEvent()                    
                if Event.client_queue.has_key(event.type):
                    Event.client_queue[event.type].put(event)
                #postMessage(str(event))
            except ConnectionClosed, e:
                if not self.shouldFinish():
                    sysprint("Connection Closed, waiting...")
                    for i in range(10):
                        if self.shouldFinish(): return
                        time.sleep(1)
                    if not self.shouldFinish():
                        sysprint("reconnecting...")
                        self.conn = cc.createServerConnection() #falta capturar las exceptions que lance este metodo
                        sysprint("reconnected")                
            except AppException, e:
                if not self.shouldFinish():
                    sysprint("Connection Closed, waiting...")
                    for i in range(10):
                        if self.shouldFinish(): return
                        time.sleep(1)
                    if not self.shouldFinish():
                        sysprint("reconnecting...")
                        self.conn = cc.createServerConnection() #falta capturar las exceptions que lance este metodo
                        sysprint("reconnected")
        #if self.conn and not self.conn.closed:
        #    self.conn.close()

                
        