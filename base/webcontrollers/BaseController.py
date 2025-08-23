#coding:utf-8
from OpenOrange import *
import Web
import os
import urllib
import mako.template
from mako.lookup import TemplateLookup



class BaseController(object):
    class Context(object):
        pass
        
    #template_lookup = TemplateLookup(directories=['/docs'], module_directory='/tmp/mako_modules')
    template_lookup = TemplateLookup(directories=[os.path.join(sd, "templates") for sd in getScriptDirs()], input_encoding="utf-8")
    
    def __init__(self, request):
        self.request = request
        self.c = BaseController.Context()
        
    def serveFromPublic(self, path_to_resource):
        for sd in getScriptDirs():
            p = os.path.join(sd, "public", path_to_resource)
            if os.path.exists(p):
                return self.serveStaticFile(p)

    def _before_(self, *args, **kwargs):
        pass

    def _after_(self, *args, **kwargs):
        pass

    def send_error(self, errnum, desc):
        self.request.send_error(errnum, desc)

    def findTemplate(self, templatename):
        template = self.__class__.template_lookup.get_template(templatename)
        template.lookup = self.__class__.template_lookup
        return template
    
    def serveStaticFile(self, path):                
        ctype = self.request.guess_type(path)
        Web.WebServerStreamer.addHeader("Content-type", ctype)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
            print f.read()
        except IOError:
            self.send_error(404, "File not found")

    def render(self, templatename, **kwargs):
        template = self.findTemplate(templatename)
        return template.render(c = self.c, **kwargs)
