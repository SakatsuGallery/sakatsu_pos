import pytest
from logic.payment_manager import get_initial_amount, process_payment, reset_payments

@pytest.fixture(autouse=True)
def clear_payments():
    # グローバル支払い累計を毎回リセット
    reset_payments()
    yield
    reset_payments()

def test_get_initial_amount_cash():
    assert get_initial_amount("現金", 150.0) is None

def test_get_initial_amount_other():
    assert get_initial_amount("クレカ", 200.0) == 200.0
    assert get_initial_amount("QR", 300.0) == 300.0

@pytest.mark.parametrize("amt,remaining,status,message", [
    (50, 50.0, "pending", "残り¥50の支払いをお待ちしております"),
    (100, 0.0, "complete", ""),
])
def test_process_payment_partial_and_complete(amt, remaining, status, message):
    total_due = 100.0
    result = process_payment("現金", total_due, amt)
    assert result["status"] == status
    assert result["remaining_due"] == remaining
    assert result["message"] == message

def test_process_payment_overpayment_cash():
    total_due = 80.0
    result = process_payment("現金", total_due, 100.0)
    assert result["status"] == "complete"
    assert result["change"] == 20.0

def test_process_payment_overpayment_card_warning():
    total_due = 80.0
    result = process_payment("クレカ", total_due, 100.0)
    assert result["status"] == "warning"
    # メッセージには「¥」付きで表示されるのでこちらをチェック
    assert "未決済額を¥20" in result["message"]