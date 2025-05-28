# flake8: noqa
# ui/printer_controller.py
from logger import get_logger
log = get_logger(__name__)

import os
from utils.date_utils import get_current_timestamp

# Try to import real printer driver
try:
    from escpos.printer import Usb
except ImportError:
    Usb = None

# Configuration: Vendor and Product ID for TM-m30III
VENDOR_ID = 0x04B8  # Epson
PRODUCT_ID = 0x0E15  # TM-T30III USB


class MockPrinter:
    """
    Development stub that prints receipts to console instead of hardware.
    """

    def set(self, **kwargs):
        pass

    def text(self, txt):
        print(txt, end="")

    def image(self, path):
        print(f"[Simulated Image: {path}]")

    def qr(self, data, **kwargs):
        print(f"[Simulated QR: {data}]")

    def cut(self):
        print("\n--- [Simulated Cut] ---\n")

    def cashdraw(self, pin):
        print(f"--- [Simulated Drawer Open: pin {pin}] ---")


class PrinterController:
    def __init__(self, simulate=None):
        """
        simulate=True で MockPrinterを、Falseで実機ドライバを使用。
        """
        use_mock = simulate if simulate is not None else (Usb is None)
        if use_mock:
            self.printer = MockPrinter()
            log.info("[PrinterController] Simulation mode enabled.")
        else:
            try:
                self.printer = Usb(VENDOR_ID, PRODUCT_ID)
                log.info("Initialized USB printer: %04x:%04x", VENDOR_ID, PRODUCT_ID)
            except Exception as e:
                log.error("Printer connection failed: %s", e)
                raise RuntimeError(f"Printer connection failed: {e}")

    def print_receipt(
        self,
        cart,
        total_due,
        payments,
        change,
        store_info=None,
        logo_path=None,
        homepage_url=None,
        transaction_id=None,
    ):
        """
        Print a receipt with cart items, header, footer, totals, payments, and change.
        cart: list of tuples (name, price)
        payments: list of tuples (method, amount)
        change: numeric
        store_info: dict with keys 'name','address','tel','company_name','business_license'
        logo_path: logo image path
        homepage_url: URL for QR code
        transaction_id: unique identifier
        """
        p = self.printer
        # Header: logo and QR
        if logo_path and hasattr(p, "image"):
            p.image(logo_path)
        if homepage_url and hasattr(p, "qr"):
            p.qr(homepage_url, size=4)
            p.text("\n")
        # Store details
        if store_info:
            p.set(align="center", bold=True)
            p.text(f"{store_info.get('name','')}\n")
            p.set(align="center")
            p.text(f"{store_info.get('address','')}\n")
            p.text(f"TEL: {store_info.get('tel','')}\n")
            p.text(f"{store_info.get('company_name','')}\n")
            p.text(f"{store_info.get('business_license','')}\n")
        # Date/time and transaction ID
        now = get_current_timestamp(fmt="%Y/%m/%d %H:%M")
        p.text(f"{now}\n")
        if transaction_id:
            p.text(f"取引ID: {transaction_id}\n")
        p.text("--------------------------------\n")
        # Items
        for name, price in cart:
            p.set(align="left")
            p.text(f"{name}\n")
            p.text(f"  {int(price):>8,} 円\n")
        p.text("--------------------------------\n")
        # Totals
        p.set(bold=True)
        p.text(f"合計: {int(total_due):,} 円\n")
        p.set(bold=False)
        # Payments
        for method, amount in payments:
            p.text(f"{method}: {int(amount):,} 円\n")
        p.text(f"お釣り: {int(change):,} 円\n")
        # Footer
        p.text("\nご利用ありがとうございました。\n")
        p.text("またのご来店お待ちしております。\n")
        p.cut()

    def open_drawer(self):
        """Open the attached cash drawer."""
        self.printer.cashdraw(2)


# テストコード
if __name__ == "__main__":
    cart = [("商品A", 1000), ("商品B", 500)]
    payments = [("現金", 1500)]
    total_due = 1500
    change = 0
    store_info = {
        "name": "さかつうギャラリー",
        "address": "東京都豊島区巣鴨3-25-13",
        "tel": "03-3949-2892",
        "company_name": "有限会社さかつう",
        "business_license": "T2013302004491",
    }
    logo_path = os.path.join(os.path.dirname(__file__), "..", "data", "logo.png")
    homepage_url = "https://shop-sakatsu.com"
    transaction_id = "00012345"
    pc = PrinterController(simulate=True)
    pc.print_receipt(
        cart, total_due, payments, change, store_info, logo_path, homepage_url, transaction_id
    )
    pc.open_drawer()
