@echo off
chcp 65001 > nul
title UIT Confession Crawler - High Speed Continuous Runner
cd /d "d:\uit-confession-sentiment\uit-confession-sentiment"
set PYTHONPATH=src
python run_continuous_crawler.py
pause
