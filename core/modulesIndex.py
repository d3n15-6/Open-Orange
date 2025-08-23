import sys
import os
import os.path
import re
from Log import *

def getClassesIndex(scriptdirs):
    try:
        pidfile = open("openorange.pid","w")
        pidfile.write("%s" % os.getpid())
        pidfile.flush()
    except Exception, e:
        print e
        
    log("Cargando indice clases...")
    prefix = "" #"../"
    #log("Generando indices de clases")
    regexp = re.compile("class ([^\(:]*)[\(:]")
    res = {}
    for scriptdir in scriptdirs:
        px = os.path.split(scriptdir)[0]
        if (px != ""):
            px = os.path.normpath(px)
            px.replace("//","/")
            px.replace("\\\\","\\")
            px.replace("/",".")
            px.replace("\\",".")
            px += "."
        filesmap = {}
        for pydir in ['records','windows','reports','routines','documents', 'updates', 'webcontrollers']:
            for root,d,files in os.walk(prefix + scriptdir + "/" + pydir):
                for fn in files:
                    if fn[-3:] == ".py":
                        filesmap[os.path.join(pydir, fn)] = os.path.getmtime(os.path.join(scriptdir, pydir, fn))
                        mod_name = fn[:-3]
                        mod_path =  scriptdir + "." + pydir + "." +mod_name
                        f = file(prefix + scriptdir + "/" + pydir + "/" + fn,"r")
                        classlines = filter(lambda x: x[0:5] == "class",f.readlines())
                        for classline in classlines:
                            classname = regexp.search(classline).group(1);
                            if not res.has_key(classname): res[classname] = []
                            mod_path =  mod_path[mod_path.rfind('/')+1:]
                            res[classname].append(px + mod_path)
        #cPickle.dump(filesmap, open(os.path.join(scriptdir, "mod.idx"), "wb"))
    #cPickle.dump(res, open("./tmp/mod.obj","wb"))
    res["RoutineWindow"] = ["core.RoutineWindow"]
    res["ReportWindow"] = ["core.ReportWindow"]    
    import functions
    functions.modules_index = res
    log("Indexacion de clases terminada...")
    return res
