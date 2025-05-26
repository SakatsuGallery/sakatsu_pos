# logic/payment_manager.py

from typing import Optional, Dict

class PaymentManager:
    """
    複数支払い対応の管理クラス。
    支払い方法と金額を追加し、合計支払額とお釣りを計算する。
    """
    def __init__(self):
        self.payments = []

    def add_payment(self, method: str, amount: float):
        if amount <= 0:
            raise ValueError("支払額は正の数で指定してください。")
        self.payments.append((method, amount))

    def total_paid(self) -> float:
        return sum(amount for _, amount in self.payments)

    def calculate_change(self, total_due: float) -> float:
        return self.total_paid() - total_due

    def is_fully_paid(self, total_due: float) -> bool:
        return self.total_paid() >= total_due

    def reset(self):
        self.payments.clear()

    def summary(self) -> Dict[str, float]:
        summary = {}
        for method, amount in self.payments:
            summary.setdefault(method, 0.0)
            summary[method] += amount
        return summary

# ── ここからモジュールレベルの関数群 ──

# 支払い累計を管理する内部辞書
_payments: Dict[str, float] = {"現金": 0.0, "クレカ": 0.0, "QR": 0.0}

def get_initial_amount(method: str, remaining_due: float) -> Optional[float]:
    """
    決済方法ごとの金額入力の初期値を返す。
     - 現金: None（空欄）
     - それ以外: 残額
    """
    if method == "現金":
        return None
    return remaining_due

def process_payment(method: str, remaining_due: float, amt: float) -> Dict:
    """
    支払いを処理し、次のステータスとメッセージを返す。
    戻り値の Dict フォーマット:
      {
        "status": "pending"|"complete"|"warning",
        "remaining_due": float,
        "change": float,
        "message": str
      }
    """
    # 累計に加算
    _payments[method] += amt
    new_remain = remaining_due - amt

    # 部分支払い
    if new_remain > 0:
        return {
            "status": "pending",
            "remaining_due": new_remain,
            "change": 0.0,
            "message": f"残り¥{int(new_remain)}の支払いをお待ちしております"
        }

    # 完全支払い or おつりあり（現金のみ）
    if new_remain == 0 or method == "現金":
        change = max(0.0, -new_remain)
        return {
            "status": "complete",
            "remaining_due": 0.0,
            "change": change,
            "message": ""
        }

    # カード／QR の超過入力
    over = -new_remain
    return {
        "status": "warning",
        "remaining_due": remaining_due,
        "change": 0.0,
        "message": f"注意！未決済額を¥{int(over)}上回っています"
    }

def get_payments_summary() -> Dict[str, float]:
    """
    現在の支払い累計を取得する。
    日次／月次レポートで利用してください。
    """
    return dict(_payments)

def reset_payments():
    """
    支払い累計をリセットする。
    GUI で別会計を開始する前に呼び出してください。
    """
    for key in _payments:
        _payments[key] = 0.0
