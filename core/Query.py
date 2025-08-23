import Embedded_OpenOrange
import re
from Log import log
from core.database.Database import Database, DBError

#class Query(Embedded_OpenOrange.Query):
from core.database.Query import Query as DBQuery

class ApplicationQuery(DBQuery):
    
    def open(self):
        return DBQuery.open(self)

    def execute(self):
        return DBQuery.execute(self)
        



#Database.createNew(Database.MYSQL)
#Database.getCurrentDB()

def Query():
    return Database.getCurrentDB().getQuery()

    query = Database.getCurrentDB().getQuery()
    return query

def Query_fromC():
    try:
        return Database.getCurrentDB().getQuery()
    except DBError, e:
        from functions import processDBError
        processDBError(e, {}, str(e))
    return None
