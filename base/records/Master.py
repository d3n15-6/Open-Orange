#encoding: utf-8
from OpenOrange import *

ParentMaster = SuperClass("Master","Record",__file__)
class Master(ParentMaster):
    __codes__ = None

    def save_fromGUI(self):
        res = ParentMaster.save_fromGUI(self)
        if res and hasattr(self, "buffer"):
            if getApplicationType() == 1 or self.isLocal():
                postMessage(tr("Record was saved, please reload Modules!"))
        return res

    def store(self, **kwargs):
        res = ParentMaster.store(self, **kwargs)
        if not res: return res
        #if hasattr(self.__class__, "buffer") and len(self.__class__.buffer) < 1000: self.__class__.buffer[self.Code] = self #no debe entrar aca en buffer xq si mas adelante hay un rollback, queda en buffer y no en db
        self.removeFromBuffer()
        return res


    def defaults(self):
        ParentMaster.defaults(self)
        self.Closed = False
        
    def save(self, **kwargs):
        res = ParentMaster.save(self, **kwargs)
        if not res: return res
        #if hasattr(self.__class__, "buffer") and len(self.__class__.buffer) < 1000: self.__class__.buffer[self.Code] = self #no debe entrar aca en buffer xq si mas adelante hay un rollback, queda en buffer y no en db
        self.removeFromBuffer()
        return res

    def removeFromBuffer(self):
        if hasattr(self.__class__, "buffer"):
            try:
                del self.__class__.buffer[self.Code]
            except KeyError, e:
                pass

        
    def uniqueKey(self):
        return ['Code']

    def afterCopy(self):
        ParentMaster.afterCopy(self)
        self.Code = None
        self.Closed = False

    def check(self):
        res = ParentMaster.check(self)
        if not res: return res
        if (not self.Code):
            code = self.getCode()
            if (code):
              self.Code = code
            else:
              res = code
        elif (self.Code != self.oldFields("Code").getValue()):
           res = self.checkCode()
           if (res):
             if self.exists(self.Code): return self.FieldErrorResponse("EXISTSERR","Code")
        if hasattr(self,"Classification"):
           from LabelControl import LabelControl
           res = LabelControl.isValidMasterClassification(self)
           if (not res): return res
        return res

    @classmethod
    def exists(classobj, code):
        if not code: return False
        if hasattr(classobj, "buffer"):
            try:
                obj = classobj.buffer[code]
                return (obj is not None)
            except KeyError, e:
                obj = classobj.trybring(code)
                if obj: return True
            return False
        self = classobj()
        res = False
        if code:
            query = Query()
            query.sql = "SELECT {Code} FROM [%s] WHERE {Code}=s|%s|" % (self.tableName(), code)
            query.setLimit(1)
            if (query.open()):
                if (query.count() >= 1):
                    res = True
                query.close()
            else:
                res = False
        return res

    @classmethod
    def _bring_(classobj, code, **kwargs):
        #log("haciendo bring de %s, modulo %s, buffer: %s" % (classobj.__name__, classobj.__module__, hasattr(classobj, "buffer")))
        if not code: raise RecordNotFoundException(classobj, Key=code, ShouldBeProcessed=kwargs.get("ProcessErrorOnBlank",False))
        res = None
        if hasattr(classobj, "buffer"):
            try:
                res = classobj.buffer[code]
            except KeyError, e:
                res = classobj.freshbring(code)
                if res: classobj.buffer[code] = res
                #log("2 Trayendo de la base de datos %s, %s" % (classobj.__name__, code))
            #else: log("3 Trayendo del buffer de %s, %s" % (classobj.__name__, code))
        else:
            res = classobj.freshbring(code)
            #log("5 Trayendo de la base de datos %s, %s" % (classobj.__name__, code))
        if not res: raise RecordNotFoundException(classobj, Key=code)
        return res

    @classmethod
    def bring(classobj, code, **kwargs):
        #log("haciendo bring de %s, modulo %s, buffer: %s" % (classobj.__name__, classobj.__module__, hasattr(classobj, "buffer")))
        if not code: return ErrorResponse("%s %s not found" % (classobj.__name__, code))
        res = None
        if hasattr(classobj, "buffer"):
            try:
                res = classobj.buffer[code]
            except KeyError, e:
                res = classobj.freshbring(code)
                if (res or classobj.buffer.rememberNones) and len(classobj.buffer) < 1000: classobj.buffer[code] = res
                #log("2 Trayendo de la base de datos %s, %s" % (classobj.__name__, code))
            #else: log("3 Trayendo del buffer de %s, %s" % (classobj.__name__, code))
        else:
            res = classobj.freshbring(code)
            #log("5 Trayendo de la base de datos %s, %s" % (classobj.__name__, code))
        if not res: return ErrorResponse("%s %s not found" % (classobj.__name__, code))
        return res

    @classmethod
    def trybring(classobj, code, **kwargs):
        return classobj.bring(code, **kwargs) #temporal line
        try:
            return classobj.bring(code, **kwargs)
        except RecordNotFoundException:
            return None
        except:
            raise

    @classmethod
    def freshbring(classobj, code):
        if code:
            obj = NewRecord(classobj.__name__)
            obj.Code = code
            if obj.load():
                return obj
        return ErrorResponse("The object %s doesn't exist" % classobj.__name__)

    def getCode(self):
        """Si no se puede generar el codigo, no devuelve nada, y el registro se grabara con el codigo blanco"""
        table = self.tableName()
        query = Query()
        query.sql = "SELECT {Code} FROM [%s] ORDER BY {Code} DESC" % table
        query.setLimit(1)
        if query.open():
            if (not query.count()):
                return "0001"
            else:
                oldCode = query[0].Code
            #Quiero ver si el codigo termina con una serie de digitos, porque si no
            #no puedo autoincrementarlo. Para eso uso la siguiente regex
            import re
            pattern = re.compile('\d+$')
            s = pattern.search(oldCode)
            if (s):
                #Si el formato es valido, separo la parte numerica de la anterior,
                #la incremento, vuelvo a unir todo y lo devuelvo
                prefix = oldCode[0:s.start()]
                sufix = int(oldCode[s.start():s.end()]) + 1
                # rellena con 0's a la izquierda y concatena con el prefix
                result = "%s%s" % (prefix, str(sufix).rjust(len(oldCode) - len(prefix),"0"))
                return result
            else:
                return self.FieldErrorResponse("No automatic code could be generated, please enter one manually","Code")

    def checkCode(self):
        import re
        pattern = re.compile('[^\$0-9a-zA-Z_\.\-\/]')
        match = pattern.search(self.Code)
        if (match):
            return self.FieldErrorResponse("Invalid Format","Code")
        return True

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentMaster.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if not res: return res
        if (fieldname == "Code") and (not self.oldFields("Code").isNone()): res = False
        return res

    def getPortableId(self, useOldFields=False):
        kstring = ""
        kd = []
        for kn in self.uniqueKey():
            if (useOldFields):
                kd.append(utf8(self.oldFields(kn).getValue()))
            else:
                kd.append(utf8(self.fields(kn).getValue()))
        kstring = "|".join(kd)
        return kstring

    def setPortableId(self, id):
        kd = id.split("|")
        kl = self.uniqueKey()
        for ki in range(0,len(kd)):
            self.fields(kl[ki]).setValue(kd[ki])

    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, utf8(self.Code))

    @classmethod
    def getList(objclass, **kwargs):
        res = {}
        idsmap = {}
        codeslist = kwargs.get("CodesList", [])
        filloldfields = kwargs.get("SaveAllowed", False)
        if len(codeslist):
            codes = '\"'+'\",\"'.join(map(lambda x: str(x), codeslist)) + '\"'
            q = Query()
            fnames = kwargs.get("FieldNames", None)
            fnamesstr = "*"
            dnames = kwargs.get("DetailNames", None)
            if dnames is None:
                dnames = objclass().detailNames()
            if fnames is not None:
                if 'internalId' not in fnames: fnames = list(fnames) + ['internalId']
                if 'Code' not in fnames: fnames = list(fnames) + ['Code']
                fnamesstr = ','.join(map(lambda x: "{%s}" % x, fnames))
            q.sql = "SELECT %s FROM [%s] WHERE {Code} in (%s) ORDER BY {internalId}" % (fnamesstr, objclass.__name__, codes)
            if q.open():
                if fnames is None: fnames = q.fieldNames()
                for rec in q:
                    obj = objclass()
                    obj.setNew(False)
                    for fn in fnames:
                        if obj.hasField(fn):
                            if not rec.fields(fn).isNone():
                                obj.fields(fn).setValue(rec.fields(fn).getValue())
                                if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                    for dn in dnames:
                        obj.details(dn).setMasterId(obj.internalId)
                    res[obj.Code] = obj
                    idsmap[obj.internalId] = obj
            internalids = ','.join(map(lambda x: str(x), idsmap.keys()))
            for dn in dnames:
                detailrecordname = objclass().details(dn).name()
                q = Query()
                q.sql = "SELECT row.* FROM [%s] row " % detailrecordname
                q.sql += "INNER JOIN [%s] t ON t.{internalId} = row.{masterId} " % objclass.__name__
                q.sql += "WHERE row.{masterId} in (%s) ORDER BY {masterId}, {rowNr}" % internalids
                detailclass = NewRecord(detailrecordname).__class__
                q.setResultClass(detailclass)
                if q.open():
                    for rec in q:
                        obj = detailclass()
                        obj.setNew(False)
                        detail = idsmap[rec.masterId].details(dn)
                        detail.append(obj)
                        for fn in rec.fieldNames():
                            if obj.hasField(fn):
                                if not rec.fields(fn).isNone():
                                    obj.fields(fn).setValue(rec.fields(fn).getValue())
                                    if filloldfields: obj.oldFields(fn).setValue(rec.fields(fn).getValue())
                        obj.setModified(False)
            for sernr, obj in res.items(): obj.setModified(False)
        return res

    @classmethod
    def getNames(objclass,closedf=True):
        names = {}
        query = Query()
        query.sql =  "SELECT {Code}, {Name} "
        query.sql += "FROM [%s] " % objclass.__name__
        if closedf: query.sql += "WHERE?AND ({Closed} IS NULL OR {Closed} = 0)\n"
        if (query.open()):
           for rec in query:
              names[rec.Code] = rec.Name
        return names

    @classmethod
    def getCodes(objclass, closedf=True):
        if not objclass.__codes__:
            objclass.__codes__ = []
            query = Query()
            query.sql =  "SELECT {Code} "
            query.sql += "FROM [%s] " % objclass.__name__
            if closedf: query.sql += "WHERE?AND ({Closed} IS NULL OR {Closed} = 0)\n"
            if (query.open()):
                for rec in query:
                    objclass.__codes__.append(rec.Code)
        return objclass.__codes__

    @classmethod
    def increment(objclass,value,v=1):
        import re
        pattern = re.compile('\d+$')
        s = pattern.search(value)
        if (s):
            prefix = value[0:s.start()]
            sufix = int(value[s.start():s.end()]) + v
            # rellena con 0's a la izquierda y concatena con el prefix
            result = "%s%s" % (prefix, str(sufix).rjust(len(value) - len(prefix),"0"))
        return result

    @classmethod
    def expandRange(objclass,range):
        elements = [ x.strip() for x in range.split(",") ]
        res = []
        for element in elements:
            if (":" in element):
              first,last = element.split(":")
              ele,n = first,0
              while (ele <> last) and n < 200:
                  res.append(ele)
                  ele = objclass.increment(ele)
                  n += 1
            else:
                res.append(element)
        return res
        


