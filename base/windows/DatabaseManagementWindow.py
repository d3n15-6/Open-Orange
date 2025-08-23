#encoding: utf-8
# Marzo 2009 - Martin Salcedo
from OpenOrange import *
from Routine import Routine

ParentDatabaseManagementWindow = SuperClass("DatabaseManagementWindow","SettingWindow",__file__)
class DatabaseManagementWindow(ParentDatabaseManagementWindow):

    def afterShowRecord(self):
        ParentDatabaseManagementWindow.afterShowRecord(self)
        self.loadParameters()
        find = FindMySQLPath()
        find.ParentWindow = self
        find.setBackground(True)
        find.open(False)
        
        
    def buttonClicked(self, buttonname):
        dm = self.getRecord()
        if (buttonname == "Backup"):
            dm.doBackup()
        record = self.getRecord()
        if (buttonname == "exportDatabase"):
            record.exportDatabase()
        elif (buttonname == "getExportFolder"):
            backupdir = getDirectoryName()
            if (backupdir):
                record.BackupPath = backupdir
        elif (buttonname == "getBackupFile"):
            fname = getOpenFileName(tr("Select File"))
            if (fname):
                record.BackupFile = fname
        elif (buttonname == "importDatabase"):
            record.importDatabase()
        elif (buttonname == "getMySQLPath"):
            find = FindMySQLPath()
            find.ParentWindow = self
            find.setBackground(True)
            find.open(False)
            

    def pastDir(self):           # no fieldname parameter is passed !
        rg = self.getRecord()
        dirname = getDirectoryName(tr("Directory"))
        rg.fields("BackupPath").setValue(dirname)
        return

    def loadParameters(self):
        q = Query()
        q.sql = "SHOW global variables like 'max_allowed_packet'"
        q.open()
        self.getRecord().MySQLMaxAllowedPacket = q[0].Value
        
    def afterEdit(self, fieldname):
        ParentDatabaseManagementWindow.afterEdit(self, fieldname)
        if fieldname == "MySQLMaxAllowedPacket":
            if askYesNo("Update parameter value in database?"):
                q = Query()
                q.sql = "SET GLOBAL max_allowed_packet = %i " % self.getRecord().MySQLMaxAllowedPacket
                q.execute()
                self.loadParameters()

class FindMySQLPath(Routine):

    def run(self):

        import os
        record = self.ParentWindow.getRecord()
        record.MySQLPath = "Searching..."
        postMessage("Looking for MySQL Path")

        lastroot = None
        for root, folder, files in os.walk("/"):
            if (lastroot != root):
                lastroot = root
            if (getPlatform() in ("linux","mac")):
                if ("mysqldump" in files):
                    record.MySQLPath = "%s/mysqldump" %(root)
                    break
            elif (getPlatform() == "win"):
                if ("mysqldump.exe" in files):
                    record.MySQLPath = "%s\mysqldump.exe" %(root)