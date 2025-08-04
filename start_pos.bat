@echo off
chcp 65001 >nul
cd /d %~dp0

call venv\Scripts\activate

python -c "from dotenv import load_dotenv; load_dotenv('.env'); from nextengine.inventory_updater import InventoryUpdater; InventoryUpdater(simulate=False)"

python -m ui.pos_gui

pause
