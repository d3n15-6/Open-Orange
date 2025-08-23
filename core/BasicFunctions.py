from datetime import datetime

def now():
    return datetime.now()

def today():
    return now().date()
    #if (True):
    #    query = Query()
    #    query.sql = "SELECT {CurDate()} " 
    #    if query.open():
    #        dp = query[0].split("-")
    #        tday   = int(dp[2])
    #        tyear  = int(dp[0])
    #        tmonth = int(dp[1])
    #    return date(tyear,tmonth,tday)
