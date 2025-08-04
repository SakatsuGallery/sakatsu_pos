@echo off

cd /d %~dp0
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
    copy .env.example .env
)
echo Setup complete.
pause
