@echo off
chcp 65001 > nul
title UIT Confession Crawler - Live Auto Runner
cd /d "d:\uit-confession-sentiment\uit-confession-sentiment"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "d:\uit-confession-sentiment\uit-confession-sentiment\run_auto_3sessions.ps1"
pause
