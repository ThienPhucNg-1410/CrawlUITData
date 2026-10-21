@echo off
chcp 65001 > nul
title UIT Confession Web App Server
cd /d "%~dp0"
if exist "serve_dashboard.py" (
    set SCRIPT=serve_dashboard.py
) else (
    cd /d "%~dp0\uit-confession-sentiment"
    set SCRIPT=serve_dashboard.py
)
python %SCRIPT%
pause

