@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo Dang khoi chay crawler cao 1500 bai viet va comments...
python crawl_full_dataset.py --target 1500
pause

