@echo off
REM Move to project root
cd /d C:\sakatsu_pos

REM Activate Python virtual environment
call .\.venv\Scripts\activate

REM Set development environment variables
set APP_ENV=development
set LOG_LEVEL=DEBUG

REM Launch POS GUI in module mode
python -m ui.pos_gui

pause
