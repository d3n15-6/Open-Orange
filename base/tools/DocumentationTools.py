#encoding: utf-8
from OpenOrange import *
from DocumentationService_client import DocumentationServiceSoapSOAP
from DocumentationService_client import GetDocumentationSoapIn
from DocumentationService_client import GetIndexSoapIn

def getFieldDocumentation(tablename, fieldname=None,url="http://www.openorange.com.ar:11001/WSActions/DocumentationServices.py"):
    #url  = "http://127.0.0.1:11001/WSActions/DocumentationServices.py"
    srv = DocumentationServiceSoapSOAP(url)
    req = GetDocumentationSoapIn()
    req.Data = req.new_Data()
    req.Data.TableName = tablename
    req.Data.FieldName = fieldname
    try:
        respobj = srv.GetDocumentation(req)
    except Exception, err:
        message("Error al obtener documentación de ayuda. Contacte con OpenOrange.")
        return
    doc = None
    if respobj.Result.Status != 0:
        res = respobj.Result
        raise Exception("Error(%s): %s - %s " %(res.Status, res.ErrorCode, res.Description))
    else:
        doc = respobj
        #print len(doc.Data.FieldsArray)
    return doc

def getIndexDocumentation(tablename, url="http://www.openorange.com.ar:11001/WSActions/DocumentationServices.py"):
    #url  = "http://127.0.0.1:11001/WSActions/DocumentationServices.py"
    srv = DocumentationServiceSoapSOAP(url)
    req = GetIndexSoapIn()
    req.Data = req.new_Data()
    req.Data.TableName = tablename
    req.Data.FieldName = ""
    try:
        respobj = srv.GetIndex(req)
    except Exception, err:
        message("Error al obtener indice de la ayuda. Contacte con OpenOrange.")
        return
    doc = None
    if respobj.Result.Status != 0:
        res = respobj.Result
        raise Exception("Error(%s): %s - %s " %(res.Status, res.ErrorCode, res.Description))
    else:
        doc = respobj
        #print len(doc.Data.FieldsArray)
    return doc
