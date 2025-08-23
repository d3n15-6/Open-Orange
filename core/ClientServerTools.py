import threading

class InteractionRequest(object):
    def __init__(self, cmd, *params):
        self.cmd = cmd
        self.params = params

def getClientConnection():
    t = threading.currentThread()
    try:
        return t.client_connection
    except AttributeError, e:
        return None