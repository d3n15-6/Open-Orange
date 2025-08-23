from datetime import timedelta
from functions import now

class RecordBuffer:
    __instances__ = []
    defaulttimeout = timedelta(hours=2)
    
    def __init__(self, classname=None, timeout=defaulttimeout, rememberNones=False):
        from BufferSettings import BufferSettings
        RecordBuffer.__instances__.append(self)
        self.rememberNones = rememberNones
        self.classname = classname
        self.objects = {}        
        self.hits = 0
        self.requests = 0        
        self.timeout_enabled = False
        self.timeout = timeout
        self.loaded = False
        if classname:
            self.timeout = BufferSettings.getExpiration(classname, timeout)
        if self.timeout == timedelta():
            self.timeout_enabled = False
        else:
            self.timeout_enabled = True
       
    @classmethod
    def getStatistics(classobj, detailed = True):
        res = []
        requests = 0
        hits = 0
        buffers = 0
        for inst in RecordBuffer.__instances__:
            if detailed: res.append(str(inst))
            requests += inst.requests
            hits += inst.hits
            buffers += 1
        res.append("Total Buffers: %i" % buffers)
        res.append("Total Requests: %i" % requests)
        res.append("Total Hits: %i" % hits)
        res.append("Total Fails: %i" % (requests - hits))
        if requests: res.append("Total %%Hits: %%%.2f\n" % (float(hits) / requests * 100))
        return '\n'.join(res)

    def __len__(self):
        return len(self.objects)
        
    def clear(self):
        self.objects.clear()
        self.requests = 0
        self.hits = 0
        self.loaded = False
        
    @classmethod
    def reset(objclass):
        for inst in RecordBuffer.__instances__:
            #print "reseting buffer %i" % id(inst)
            inst.clear()

    def get(self, key, default):
        try:
            return self.__getitem__(key)
        except:
            return default
        
    def __getitem__(self, key):
        #returns KeyError if the object has never been in the buffer or if the object has expired; otherwise returns the object.    
        self.requests += 1
        try:
            if self.timeout_enabled:
                expires, obj = self.objects[key]                
                if expires > now():
                    #print "%s found in buffer... vigencia: %s" % (key, expires - now())
                    self.hits += 1
                    return obj
            else:
                obj = self.objects[key]
                self.hits += 1
                return obj                
            raise KeyError
        except:
            #print "%s NOT found in buffer" % key
            raise

    def __delitem__(self, key):
        del self.objects[key]

    def __setitem__(self, key, value):
        if self.timeout_enabled:
            self.objects[key] = (now() + self.timeout, value)
        else:
            self.objects[key] = value
        #print "adding %s to buffer %i, objects: %i" % (key, id(self), len(self.objects))
     
    def __str__(self):
        s = "Buffer of %s, %i objects stored, Timeout Enabled: %s, Timeout: %s\n" % (self.classname, len(self.objects), self.timeout_enabled, self.timeout)
        n = now()
        for k, v in self.objects.items():   
            if self.timeout_enabled:
                if v[0] > now():
                    t = (v[0]-now())
                    tt = "%s:%s:%s.%i" % (t.seconds / 3600, (t.seconds % 3600) / 60, t.seconds % 60, t.microseconds/100)
                    s += "%s: (%s) %s\n" % (k,tt, str(v[1]))
                else:
                    tt = "expired"
                    s += "%s (%s) %s\n" % (k,tt, str(v[1]))
            else:
                s += "%s: %s\n" % (k,str(v))
        if self.requests: s += "Resquests: %i, Hits: %i, Fails: %i  -> (%%%.2f)\n" % (self.requests, self.hits, self.requests - self.hits, float(self.hits) / self.requests * 100)
        return s
        
class TemporalRecordBuffer(RecordBuffer):
    pass
    
class SettingBuffer(RecordBuffer):
    pass

        