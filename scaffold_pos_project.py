import os

# Base project directory
base = r"C:\sakatsu_pos"

# Subdirectories to create
dirs = [
    "ui",
    "logic",
    "nextengine",
    "data"
]

# Create directories
for d in dirs:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)

# Files to create
files = [
    "main.py",
    os.path.join("ui", "pos_gui.py"),
    os.path.join("ui", "tenkey_popup.py"),
    os.path.join("ui", "payment_selector.py"),
    os.path.join("ui", "customer_display.py"),
    os.path.join("ui", "printer_controller.py"),
    os.path.join("logic", "goods_manager.py"),
    os.path.join("logic", "payment_manager.py"),
    os.path.join("logic", "discount_manager.py"),
    os.path.join("logic", "sales_recorder.py"),
    os.path.join("logic", "report_generator.py"),
    os.path.join("logic", "drawer_control.py"),
    os.path.join("logic", "cash_flow_manager.py"),
    os.path.join("nextengine", "api_client.py"),
    os.path.join("nextengine", "inventory_sync.py"),
    os.path.join("nextengine", "sales_uploader.py"),
    os.path.join("data", "goods_data.json"),
    os.path.join("data", "settings.json"),
    os.path.join("data", "sales_log.csv"),
    os.path.join("data", "cash_log.csv")
]

# Create files
for f in files:
    full_path = os.path.join(base, f)
    dirpath = os.path.dirname(full_path)
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as file:
        file.write("# " + os.path.basename(f) + " – scaffold file\n")

print(f"Project scaffold created under {base}")
