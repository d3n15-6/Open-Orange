#encoding: utf-8
# Marzo 2009 - Martin Salcedo
from OpenOrange import *

ParentDatabaseManagement = SuperClass("DatabaseManagement","Setting",__file__)
class DatabaseManagement(ParentDatabaseManagement):

    def checkDBPassword(self):
        if self.DBPasswordAdminEnabled:
            from Company import Company
            company = Company.bring(currentCompany())
            if company:
                if company.User != self.NewDBUser and company.Password != self.NewDBPassword:
                    company.User = self.NewDBUser
                    company.Password = self.NewDBPassword
                    res = company.store()
                    if not res:
                        message(res)
                    else:
                        self.PasswordChangesQty +=  1
                        res = self.store()
                        if not res:
                            message(res)
                        commit()
                        postMessage("Database password changed succesfully.")
            if not self.fields("OldDBPasswordExpirationDate").isNone() and today() > self.OldDBPasswordExpirationDate:
                q = Query()
                setQueryLogging(True) #False
                q.sql = "UPDATE mysql.user SET password = PASSWORD(s|%s|) where user=s|%s|" % (decode(self.NewDBPassword), self.NewDBUser)
                res = q.execute()
                if res:
                    commit()

    def exportDatabase(self):
        from Company import Company
        import os
        comp = Company.getCurrent()
        if (not self.BackupPath):
            targetdir = "."
        else:
            targetdir = self.BackupPath
        targetfile = "%s/%s%s.sql" %(targetdir,comp.DBName,now().strftime("%Y%m%d-%H%M"))
        systemstring = "mysqldump "
        if self.MySQLPath: systemstring = self.MySQLPath + " "
        bkpoptions  = "--host=%s " %(comp.Host)
        bkpoptions += "--port=%s " %(comp.Port)
        bkpoptions += "--user=%s " %(comp.User)
        bkpoptions += "--password=%s " %(decode(comp.Password))
        #bkpoptions += "--log-error='tmp/mysqldump_%s.log' " %(comp.DBName)
        if (self.HexBlob):
            bkpoptions += "--hex-blob "
        if (self.AddDropDatabase):
            bkpoptions += "--add-drop-database "
        if (self.AddDropTable):
            bkpoptions += "--add-drop-table "
        if (self.IgnoreTable):
            for tname in self.IgnoreTable.split(","):
                bkpoptions += "--ignore-table=%s.%s " %(comp.DBName,tname)
        bkpoptions += "%s " %(comp.DBName)
        systemstring += bkpoptions 
        systemstring += "> %s " %targetfile 
        log(systemstring)
        message("Inicio del backup de la base de datos. Esto puede tomar varios minutos...")
        os.system(systemstring)
        
        message(tr("Exportation done"))
        #outlog = open("tmp/mysqldump_%s.log" %(comp.DBName))
        #if (outlog):
        #    for oline in outlog.readlines():
        #        self.ExportOutput += oline

    def importDatabase(self):
        from Company import Company
        import os
        oopath = os.path.abspath(".")
        comp = Company.getCurrent()
        sourcefile = self.BackupFile
        if (self.FixMySQLBackup):
            
            fixedfile = "%s/tmp/%s" %(oopath,os.path.basename(self.BackupFile))
            from FixMySQLBackup import FixMySQLBackup
            fixmysql = FixMySQLBackup()
            fixmysql.getRecord().SourceFile = self.BackupFile
            fixmysql.getRecord().TargetFile = fixedfile
            fixmysql.open(False)
            sourcefile = fixedfile
        cmdstring = "mysql "
        if (self.ImportIntoThisDB):
            bkpoptions  = "--host=%s " %(comp.Host)
            bkpoptions += "--port=%s " %(comp.Port)
            bkpoptions += "--user=%s " %(comp.User)
            bkpoptions += "--password=%s " %(decode(comp.Password))
            dbname = comp.DBName
        else:
            bkpoptions  = "--host=%s " %(self.ImpHost)
            bkpoptions += "--port=%s " %(self.ImpPort)
            bkpoptions += "--user=%s " %(self.ImpUser)
            bkpoptions += "--password=%s " %(decode(self.ImpPassword))
            dbname = self.ImpDBName

        mysqlstring = cmdstring+bkpoptions+dbname
        mysqlstring += " < %s" %(sourcefile)
        log(mysqlstring)

        createstring = "mysql "
        createstring += bkpoptions
        createstring += "--execute='CREATE DATABASE IF NOT EXISTS `%s`' " %(dbname)

        message("Creating Database")
        os.system(createstring)

        message("Inicio de la importación. Esto puede tomar varios minutos...")
        sysprint(mysqlstring)
        log(mysqlstring)
        os.system(mysqlstring)
        message(tr("Importation done"))
        #outlog = open("tmp/mysql_%s.log" %(comp.DBName))
        #if (outlog):
        #    for oline in outlog.readlines():
        #        self.ExportOutput += oline
        #if (self.FixMySQLBackup):
        #    os.remove(fixedfile)

    def fieldIsEditable(self, fieldname, rowfieldname=None, rownr=None):
        res = ParentDatabaseManagement.fieldIsEditable(self, fieldname, rowfieldname, rownr)
        if (not res): return res
        if (self.ImportIntoThisDB == 1):
            if (fieldname in ("ImpDBName","ImpHost","ImpPort","ImpUser","ImpPassword")):
                res = False
        return res

#    def doBackup(self):
#        from Company import Company
#        company = Company()
#        company.Code = currentCompany()
#        if company.load():
#            dbname = company.Code
#            if company.DBName: dbname = company.DBName
#            host = currentCompanyHost()
#            self.writeBackupBatchFile(host,dbname,company.User,company.Password)
#            from os import popen
#            self.Output = "Making Backup ..."
#            if platform.startswith("linux"):
#              mm = popen("chmod 777 doBackup.sh").read()
#              feedback = popen("./doBackup.sh").read()
#              mm = popen("rm doBackup.sh").read()         # delete Backup File has passwords etc!
#            else:
#              feedback = popen("doBackup.bat").read()
#            self.Output = feedback
#
#
#    def writeBackupBatchFile(self,host,schema,username,password):
#        filename = "doBackup.bat"
#        if self.OS: filename = "doBackup.sh"
#        f = open(filename,"w")
#        s = []
#        s.append("MYSQLBIN_PATH='%s'" % self.DatabaseClientPath)
#        s.append("BACKUP_PATH='%s'" % self.BackupPath)
#        s.append("USER='%s'" % username)
#        s.append("PASSWD='%s'" % decode(password) )
#        s.append("HOST='%s'" % host)
#        s.append("DATABASE_NAME='%s'" % schema)
#        s.append('FILE_NAME=$DATABASE_NAME`date +%F%k-%M`\.sql')
#        s.append('ATTACH_NAME=$DATABASE_NAME-Attach`date +%F%k-%M`\.sql')
#        s.append('EVENTLOG_NAME=$DATABASE_NAME-EventLog`date +%F%k-%M`\.sql')
#        s.append('if ! test -d $BACKUP_PATH')
#        s.append('then')
#        s.append('    mkdir -p $BACKUP_PATH')
#        s.append('fi')
#        s.append('echo "Making Database Backup without Tables (EventLog,Attach)"')
#        s.append('$MYSQLBIN_PATH/mysqldump -u$USER -p$PASSWD -h$HOST --hex-blob --ignore-table="$DATABASE_NAME.Attach" --ignore-table="$DATABASE_NAME.EventLog" $DATABASE_NAME > $BACKUP_PATH/$FILE_NAME')
#        s.append('echo "Making Database Backup Table Attach"')
#        s.append('$MYSQLBIN_PATH/mysqldump -u$USER -p$PASSWD -h$HOST --hex-blob $DATABASE_NAME Attach > $BACKUP_PATH/$ATTACH_NAME ')
#        s.append('echo "Making Database Backup Table EventLog"')
#        s.append('$MYSQLBIN_PATH/mysqldump -u$USER -p$PASSWD -h$HOST --hex-blob $DATABASE_NAME EventLog > $BACKUP_PATH/$EVENTLOG_NAME ')
#        s.append('cd $BACKUP_PATH')
#        s.append('echo "Compressing Database Backup without Tables (EventLog,Attach)"')
#        s.append('tar cvfz "$FILE_NAME.tgz" "$FILE_NAME"')
#        s.append('rm "$FILE_NAME"')
#        s.append('echo "Compressing Database Backup Table Attach"')
#        s.append('tar cvfz "$ATTACH_NAME.tgz" "$ATTACH_NAME"')
#        s.append('rm "$ATTACH_NAME"')
#        s.append('echo "Compressing Database Backup Table EventLog"')
#        s.append('tar cvfz "$EVENTLOG_NAME.tgz" "$EVENTLOG_NAME"')
#        s.append('rm "$EVENTLOG_NAME"')
#        f.writelines("%s\n" % ("\n".join(s)))
#        f.flush()
#        f.close()