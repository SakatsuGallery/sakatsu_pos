# logic/sales_recorder.py
import os
from pathlib import Path
from datetime import datetime
from logger import get_logger
from nextengine.inventory_updater import InventoryUpdater
from utils.date_utils import get_current_timestamp
from utils.file_utils import ensure_dir, save_json
from utils.receipt_builder import ReceiptBuilder
from utils.printer import ReceiptPrinter

log = get_logger(__name__)

class SalesRecorder:
    def __init__(self, data_dir: str = "data", printer_ip: str = None):
        self.data_dir = Path(data_dir)
        self.receipt_builder = ReceiptBuilder(config_path="config/receipt_layout.yaml")
        host = printer_ip or os.getenv("PRINTER_IP", "127.0.0.1")
        self.printer = ReceiptPrinter(host=host)

    def record_sale(self, cart, total_due, payments, change,
                    transaction_id=None, timestamp=None):
        log.info(f">>> record_sale start")
        # Timestamp setup
        if timestamp:
            ts_obj = timestamp
        else:
            ts_obj = datetime.fromisoformat(get_current_timestamp(fmt="%Y-%m-%dT%H:%M:%S"))
        ts_str = ts_obj.isoformat()
        file_ts = ts_obj.strftime("%Y%m%d_%H%M%S")
        ym = ts_obj.strftime("%Y%m")
        # Save JSON record
        dir_path = self.data_dir / ym
        ensure_dir(str(dir_path))
        fname = f"sales_{file_ts}.json"
        file_path = dir_path / fname
        record = {
            "transaction_id": transaction_id or file_ts,
            "timestamp": ts_str,
            "cart": cart,
            "total_due": total_due,
            "payments": payments,
            "change": change,
        }
        save_json(str(file_path), record)
        log.info(f"Recorded sale: {file_path}")
        # Inventory sync
        try:
            sim = os.getenv("IS_SIMULATION", "true").lower() in ("1","true","yes")
            token_env = ".env.test" if sim else ".env"
            updater = InventoryUpdater(token_env=token_env, simulate=sim)
            res = updater.update_from_record(str(file_path))
            log.info(f"Inventory update successful (simulate={sim}): {res}")
        except Exception as e:
            log.error(f"Inventory update failed: {e}", exc_info=True)
        # Receipt print
        try:
            # Payment summary
            payments_list = record.get("payments", [])
            total_paid = sum(p.get("amount", 0) for p in payments_list)
            if payments_list:
                methods = {p.get("method", "") for p in payments_list}
                method = methods.pop() if len(methods) == 1 else "支払"
            else:
                method = "cash"
            label_map = {"cash": "現金", "クレカ": "クレジットカード", "QR": "QR", "支払": "支払"}
            pay_method_name = label_map.get(method, method)
            pay_amount = total_paid if payments_list else total_due
            # Build sale_data with integer values
            sale_data = {
                "items":           record["cart"],
                "total":           int(record["total_due"]),
                "change":          int(record["change"]),
                "timestamp":       datetime.fromisoformat(record["timestamp"]),
                "pay_method_name": pay_method_name,
                "pay_amount":      int(pay_amount),
            }
            log.info(f">>> preparing to build receipt job: {sale_data}")
            job = self.receipt_builder.build(sale_data)
            log.info(f">>> built receipt job: {job}")
            self.printer.execute(job)
            log.info(f">>> ReceiptPrinter.execute completed")
        except Exception as e:
            log.error(f"Receipt printing failed: {e}", exc_info=True)
        log.info(f">>> record_sale end")
        return str(file_path)

if __name__ == "__main__":
    # Test print
    recorder = SalesRecorder()
    recorder.record_sale(
        cart=[
            {"goods_id":"A1","name":"Test","price":100,"quantity":1}
        ],
        total_due=100,
        payments=[{"method":"cash","amount":150}],
        change=50
    )
