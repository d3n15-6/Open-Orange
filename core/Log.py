from Embedded_OpenOrange import logstring
from BasicFunctions import now, today
import encodings.utf_8
#import threading
#mutex = threading.Lock()
import encodings.utf_8

def log(s, param=None):
    #if not param:
    if not isinstance(s, basestring):
        s = str(s)
    elif isinstance(s, unicode):
        s = s.encode("utf8", "replace")
        
    logstring("%s: %s" % (now(), s))
    #    mutex.acquire()
    #    f = open("FFF.TXT","ab+")
    #    f.write("%s\n" % s)
    #    f.flush()
    #    f.close()
    #    mutex.release()
    
def logConnection(s):
   f = open("./tmp/connection.log", "a+")
   f.write("%s: %s\n" % (now(), s))
   f.close()
