@echo off
SET MYSQL_PATH="C:\Archivos de programa\MySQL\MySQL Server 5.0"
SET TARGETDIR="backups"
SET USER=root
SET PASSWORD=123456
SET HOST=127.0.0.1
SET PORT=3306
SET DBNAME=open
SET WINRAR_EXE="C:\Archivos de programa\WinRAR\rar.exe"

:: ------------
:: Get current date/time
:: ------------
FOR /F "TOKENS=2-4 DELIMS=/ " %%F IN ('DATE /T') DO (
 SET YYYY=%%H
 SET MM=%%F
 SET DD=%%G
)
FOR /F "TOKENS=5-6 DELIMS=: " %%F IN ('ECHO.^|TIME') DO (
 SET HR=%%F
 SET MN=%%G
)


:: ------------------------------------------------------------------
:: Batchfile : NewDate.bat
:: Purpose   : A routine to parse the current date. Supports formats:
::             MM-DD-YYYY  DD-MM-YYYY  DD.MM.YYYY  DD/MM/YYYY
:: OS        : Windows 95+, Windows NT4+
:: Created   : Tom Lavedas <lavedas@pressroom.com>, 20000717
:: Adopted   : Frank-Peter Schultze <fpschultze@bigfoot.de>, 20000719
:: Revised   : Frank-Peter Schultze <fpschultze@bigfoot.de>, 20050918
:: ------------------------------------------------------------------
  @echo off
   if %1/==:/ goto %2
   if NOT %1/==/?/ goto Begin
   echo Parses the current date.
   echo.
   echo [CALL] NewDate
   echo.
   echo NewDate sets the following variables:
   echo.
   echo   Day of Week : DOW
   echo   Day         : DD
   echo   Month       : MM
   echo   Year        : YYYY
   echo.
   echo NewDate supports the following date formats:
   echo.
   echo   MM-DD-YYYY  DD-MM-YYYY  DD.MM.YYYY  DD/MM/YYYY
   for %%C in (echo. goto:End) do %%C
  :Begin --------------------------------------------------------------
   echo. | date | FIND "(mm" > NUL
   if NOT errorlevel 1 %0 : %OS%Parse MM DD
                       %0 : %OS%Parse DD MM
  :Windows_NTParse ----------------------------------------------------
   for /F "tokens=1-4 delims=/.- " %%A in ('date /T') do if %%D!==! (
     set %3=%%A&set %4=%%B&set YYYY=%%C
   ) else (
     set DOW=%%A&set %3=%%B&set %4=%%C&set YYYY=%%D)
   goto End
  :Parse --------------------------------------------------------------
   for %%C in (md cd) do %%C @tmp@
   echo @prompt set _D=$D$_> ~tmp1.bat
   %COMSPEC% /e:2048 /c ~tmp1.bat > ~tmp2.bat
   call ~tmp2
   echo %_D% | FIND "/" > NUL
   if NOT errorlevel 1 goto Slash
   lfnfor on > "%_D%.-"
   ren "%_D%.-" "??? ?? ?? ????"
   for %%F in ("??? ?? ?? ????") do set _D=%%F
   lfnfor off
  :Slash
   echo set DOW=%%%3%%>~tmp1.bat
   for %%S in ("%3=%%%4%%" "%4=%%YYYY%%" "YYYY=%%1") do echo set %%S>>~tmp1.bat
   for %%S in (%_D%) do call ~tmp1 %%S
   echo %_D% | FIND "/" > NUL
   if errorlevel 1 goto Cleanup
   echo @prompt set %4=$%%%4%%$_set YYYY=$%YYYY%$_ > ~tmp1.bat
   %COMSPEC% /e:2048 /c ~tmp1.bat > ~tmp2.bat
   call ~tmp2
  :Cleanup
   for %%C in ("set _D=" cd.. "deltree /y @tmp@ > NUL") do %%C
   echo Demo: YYYY=%YYYY% MM=%MM% DD=%DD% DOW=%DOW%
  :End ----------------------------------------------------------------
   

SET TARGET_FILE=%DBNAME%-%YYYY%-%MM%-%DD%_%HR%-%MN%.sql
SET ATTACH_FILE=%DBNAME%-%YYYY%-%MM%-%DD%_%HR%-%MN%-Attach.sql
SET EVENTLOG_FILE=%DBNAME%-%YYYY%-%MM%-%DD%_%HR%-%MN%-EventLog.sql

%MYSQL_PATH%\bin\mysqldump.exe -u%USER% -p%password% -h%HOST% --port %PORT% -Q --hex-blob --ignore-table="%DBNAME%.Attach" --ignore-table="%DBNAME%.EventLog" --verbose --complete-insert --allow-keywords --create-options -r"%TARGETDIR%\%TARGET_FILE%" %DBNAME%
%MYSQL_PATH%\bin\mysqldump.exe -u%USER% -p%password% -h%HOST% --port %PORT% -Q --hex-blob --verbose --complete-insert --allow-keywords --create-options -r"%TARGETDIR%\%ATTACH_FILE%" %DBNAME% Attach
%MYSQL_PATH%\bin\mysqldump.exe -u%USER% -p%password% -h%HOST% --port %PORT% -Q --hex-blob --verbose --complete-insert --allow-keywords --create-options -r"%TARGETDIR%\%EVENTLOG_FILE%" %DBNAME% EventLog

 :: echo Comprimiendo...
 :: cd %TARGETDIR%
 :: %WINRAR_EXE% a "%TARGET_FILE%.rar" %TARGET_FILE%
 :: del %TARGET_FILE%

echo Backup terminado.
echo.
