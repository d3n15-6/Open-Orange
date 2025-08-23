#encoding: utf-8
from OpenOrange import *
import cPickle

class HistoryManager(object):
    __history__ = {(currentCompany(), currentUser()): []}
    __hist_dict__ = {(currentCompany(), currentUser()): {}}
    
    @classmethod    
    def addWindow(classobj, window):
        if not window.getRecord().isNew() or not window.getRecord().isPersistent():
            if not classobj.__history__.has_key((currentCompany(), currentUser())): classobj.__history__[(currentCompany(), currentUser())] = []        
            if not classobj.__hist_dict__.has_key((currentCompany(), currentUser())): classobj.__hist_dict__[(currentCompany(), currentUser())] = {}
            d = {}
            for k in window.getRecord().uniqueKey():
                d[k] = getattr(window.getRecord(), k)
            dhash = str(d)
            if HistoryManager.__hist_dict__[(currentCompany(), currentUser())].has_key((window.getRecord().name(), dhash)):
                k = 0
                for item in HistoryManager.__history__[(currentCompany(), currentUser())]:
                    if (item[4], str(item[5])) == (window.getRecord().name(), dhash):
                        del HistoryManager.__history__[(currentCompany(), currentUser())][k]
                        break
                    k += 1
            else:
                HistoryManager.__hist_dict__[(currentCompany(), currentUser())][(window.getRecord().name(), dhash)] = True
            HistoryManager.__history__[(currentCompany(), currentUser())].append((today(), now(), str(window.getRecord()), window.__class__.__name__, window.getRecord().name(), d))
            if len(HistoryManager.__history__[(currentCompany(), currentUser())]) > 20: 
                item = HistoryManager.__history__[(currentCompany(), currentUser())][0]
                dhash = str(item[5])
                try:
                    del HistoryManager.__hist_dict__[(currentCompany(), currentUser())][(item[4], dhash)]
                except:
                    pass
                HistoryManager.__history__[(currentCompany(), currentUser())] = HistoryManager.__history__[(currentCompany(), currentUser())][1:]
            from HistoryManagerReport import HistoryManagerReport
            for instance in HistoryManagerReport.instances:
                instance.refresh()

    def __getitem__(self, i):
        try:
            return HistoryManager.__history__[(currentCompany(), currentUser())][i]
        except KeyError, e:
            HistoryManager.__history__[(currentCompany(), currentUser())] = []
            return len(HistoryManager.__history__[(currentCompany(), currentUser())])

    def __len__(self):
        try:
            return len(HistoryManager.__history__[(currentCompany(), currentUser())])
        except KeyError, e:
            HistoryManager.__history__[(currentCompany(), currentUser())] = []
            return len(HistoryManager.__history__[(currentCompany(), currentUser())])
        
    @classmethod
    def openItem(classobj, idx):
        item = classobj.__history__[(currentCompany(), currentUser())][idx]
        w = NewWindow(item[3])
        r = NewRecord(item[4])
        d = item[5]
        if r.isPersistent():
            if hasattr(r, "bring") and len(d.keys()) == 1:
                r = r.bring(d[d.keys()[0]])
            else:
                for k in d:
                    setattr(r, k, d[k])
                r.load()
        else:
            r.defaults()
        if r:
            w.setRecord(r)
            w.open()
    
    @classmethod
    def saveHistory(objclass):
        try:
            cPickle.dump(objclass.__history__, open("./tmp/history.log", "w"))
        except:
            pass

    @classmethod
    
    def loadHistory(objclass):
        try:
            objclass.__history__ = cPickle.load(open("./tmp/history.log", "r"))
        except:
            objclass.__history__ = {(currentCompany(), currentUser()): []}
        if not objclass.__history__.has_key((currentCompany(), currentUser())): objclass.__history__[(currentCompany(), currentUser())] = []
        for k1 in objclass.__history__:
            objclass.__hist_dict__[k1] = {}
            objclass.__history__[k1] = objclass.__history__[k1][-20:]
            for k2 in objclass.__history__[k1]:
                objclass.__hist_dict__[k1][(k2[4], str(k2[5]))] = True

HistoryManager.loadHistory()
