import sys
stderr = sys.stderr
class VoidStdErr:
    def write(self, d):
        pass
sys.stderr = VoidStdErr()
try:
    try:
        import MySQLdb
        from MySQLdb.connections import Connection
        from MySQLdb.constants import *
        from MySQLdb.times import *
        import MySQLdb.converters
    except Exception, e:
        stderr.write(str(s))
finally:
    sys.stderr = stderr
