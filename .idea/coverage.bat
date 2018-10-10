@echo off
set python=%1\python.exe
set arguments=%2
set PYTHONPATH=%3

%python% -m coverage run %arguments%
if %errorlevel% EQU 0 ( 
	%python% -m coverage html
	cd htmlcov
	index.html
)