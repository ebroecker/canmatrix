@echo off
rem -------------------------------------------------------------
rem In PyCharm create "external tool" pointing to this file, with
rem Arguments: $PyInterpreterDirectory$ $FilePath$
rem WorkingDirectory $ProjectFileDir$
rem -------------------------------------------------------------
set python=%1\python.exe
set arguments=%2


%python% -m coverage run -m pytest %arguments%
if %errorlevel% EQU 0 ( 
	%python% -m coverage html
	cd htmlcov
	index.html
)
