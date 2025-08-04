# draw_test.py
from utils.printer import ReceiptPrinter

p = ReceiptPrinter(host="192.168.1.24")
# 試しにドロワー１を5回叩く
for _ in range(5):
    p.printer._raw(b"\x1B\x70\x00\x32\xFA")
print("Drawer test pulses sent")
