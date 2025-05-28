# remove_bom.py
import io

path = "setup.cfg"
with io.open(path, "r", encoding="utf-8-sig") as f:
    text = f.read()
with io.open(path, "w", encoding="utf-8") as f:
    f.write(text)
print("BOM removed from setup.cfg")
