import SocketServer
import threading
import struct

class ApplicationServer(SocketServer.ThreadingTCPServer):
    allow_reuse_address = True    
        
    def server_activate(self):
        self.socket.settimeout(0.5)
        SocketServer.ThreadingTCPServer.server_activate(self)
        
class ClientHandler(SocketServer.StreamRequestHandler):
    cgi_directories = ['web/cgi-bin/client']

    def setup(self):
        self.connection = self.request
        self.connection.settimeout(0.5)
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)
    
    def __send__(self, datastr):
        sizestr = struct.pack("!i", len(datastr))
        self.wfile.write(sizestr + datastr)

    def handle(self):
        self.__send__("23123123123123123123123123123123")
        

class ServerStarter(threading.Thread):    
    def run(self):
        server = ApplicationServer(('',8081), ClientHandler)
        server.handle_request()



class ClientTester(threading.Thread):
    
    def __receive__(self):
        sizestr = ""
        data = ""
        while len(sizestr) < 4:
            sizestr = self.socket.recv(4 - len(sizestr))
        if len(sizestr) == 4:
            size = struct.unpack("!i", sizestr)[0]
            while len(data) < size:
                data += self.socket.recv(size - len(data))
        return data  
    
    def run(self):
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(2)
        self.socket.connect(('localhost', 8081))
        data = self.__receive__()
        print "|" + data + "|"


ServerStarter().start()
ClientTester().start()

