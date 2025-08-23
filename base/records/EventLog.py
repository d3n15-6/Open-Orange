#encoding: utf-8
from OpenOrange import *

ParentEventLog = SuperClass("EventLog", "Record", __file__)
class EventLog(ParentEventLog):
    INSERT = 0
    UPDATE = 1
    DELETE = 2
    
    @classmethod
    def getEventsOnDate(classobj, eventsdate, recordname = None, uniqueids = False):
        return getEventsOnPeriod(eventsdate, eventsdate, uniqueids)

    @classmethod
    def getEventsOnPeriod(classobj, fromdate, todate, recordname = None, uniqueids = False):
        query = Query()
        query.sql = "SELECT {recInternalId} as recInternalId "
        query.sql += "FROM [EventLog] "
        if recordname: query.sql += "WHERE?AND {RecordName} = s|%s| " % recordname
        query.sql += "WHERE?AND {TransDate} BETWEEN d|%s| AND d|%s| " % (fromdate, todate)
        if uniqueids: "GROUP BY {recInternalId}"
        query.sql += "ORDER BY {TransTime} "
        if query.open():
            return query
        return None            