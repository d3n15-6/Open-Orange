from BasicFunctions import *
import Queue

class Event(object):
    user_connections = {} #used in server  {conn->user}
    connection_queues = {} #used in server {connection->events_queue}
    client_queue = {} #used in client
    client_queue["ChatMessage"] = Queue.Queue()
    
    type = "Event"
    
    def __init__(self):
        from functions import currentUser
        self.creation_date = today()
        self.creation_time = now()
        self.user = currentUser()

    @classmethod
    def getQueue(clsobj,  conn):
        try:
            return clsobj.connection_queues[conn]
        except KeyError, e:
            clsobj.connection_queues[conn] = Queue.Queue()
            return clsobj.connection_queues[conn]
        
    def dispatch(self):
        return 0
    
    
    @classmethod
    def pop(clsobj, conn, timeout=10):
        return clsobj.getQueue(conn).get(bool(timeout), timeout)
        
    def __str__(self):
        return "%s <%s> posted by %s" % (self.creation_time, self.__class__.__name__, self.user)

class IdleEvent(object):
    
    type = "Idle"
    
        
class ChatMessageEvent(Event):
    type = "ChatMessage"
    
    def __init__(self, to_users, msg):
        Event.__init__(self)
        self.to_users = to_users
        self.msg = msg
        self.linkwindowname = None
        self.linkrecord = None
        
        
    def dispatch(self):
        k = 0
        for conn, user in Event.user_connections.items():
            if user in self.to_users:
                ChatMessageEvent.getQueue(conn).put(self)
            k += 1
        return k

    def __str__(self):
        return "%s says: %s" % (self.user, self.msg)

    def post(self):
        from Company import Company
        cc = Company.getCurrent()
        if not cc.isApplicationServerCompany(): return -1
        return cc.getServerConnection().postEvent(self)

                