@echo off
chcp 65001 > nul
title Facebook Login Helper - Save Profile
cd /d "d:\uit-confession-sentiment\uit-confession-sentiment"
set PYTHONPATH=src
python scripts/login_facebook.py
pause
