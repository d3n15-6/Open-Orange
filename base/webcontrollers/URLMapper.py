#coding:utf-8
from OpenOrange import *
import re
import Web
import urllib
from BaseController import BaseController

class URLMapper(list):
    class URLMap(object):
        def __init__(self, url, controller, methodname, params):
            self.url = url
            self.controller = controller
            self.methodname = methodname
            self.params = params


    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self.addURLMap(URLMapper.URLMap("/(?P<path_to_resource>[^\?]+)", BaseController, "serveFromPublic", ("%(path_to_resource)s",)))

    def addURLMap(self, urlmap):
        self.insert(0, urlmap)
        
    def dispatch(self, request):
        for umap in self:
            for sd in getScriptDirs():
                matchobject = re.match(umap.url, urllib.unquote(request.path))
                if matchobject:
                    controller = umap.controller(request)
                    params = [urllib.unquote(p % matchobject.groupdict()) for p in umap.params]
                    controller._before_(*params)
                    getattr(controller, urllib.unquote(umap.methodname % matchobject.groupdict()))(*params)
                    controller._after_(*params)
                    return None
        request.send_error(404, "File not found")
        return None
                    
        
            