import tkinter as tk
from tkinter import Toplevel, StringVar

def select_payment(parent, methods=None):
    """
    支払い方法選択ダイアログを表示し、
    選択された方法（文字列）を返す。キャンセルは None。
    """
    if methods is None:
        methods = ["現金", "クレジットカード", "QRコード", "その他"]

    popup = Toplevel(parent)
    popup.title("支払い方法選択")
    popup.grab_set()
    popup.resizable(False, False)

    result_var = StringVar(value=None)

    tk.Label(popup, text="支払い方法を選択してください", font=("Arial", 14)).pack(pady=10)
    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=10, padx=10)

    def choose(method):
        result_var.set(method)
        popup.destroy()

    for m in methods:
        tk.Button(
            btn_frame,
            text=m,
            command=lambda m=m: choose(m),
            font=("Arial", 16),
            width=12,
            height=2
        ).pack(pady=5)

    popup.wait_window()
    return result_var.get()

# テストコード
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    method = select_payment(root)
    print("選択された支払い方法：", method)
    root.destroy()
