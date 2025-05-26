# --- ファイル: ui/tenkey_popup.py ---
import tkinter as tk
from tkinter import Toplevel, StringVar, simpledialog, messagebox


def ask_price(parent, title="金額入力", prompt="金額を入力してください：", default=None, tax_mode=False):
    """
    モーダルで数値入力テンキーを表示し、入力された金額(整数)を返す。
    キャンセル時は None を返す。

    Parameters:
    - parent: 親ウィンドウ
    - title: ダイアログのタイトル
    - prompt: プロンプト文言
    - default: 初期表示金額 (整数)
    - tax_mode: True の場合は税込/税別キーを表示し、税別入力時は税込に換算 (四捨五入)

    Returns:
    - 入力された整数金額 または None
    """
    popup = Toplevel(parent)
    popup.title(title)
    popup.grab_set()
    popup.resizable(False, False)

    # 結果格納
    popup.result = None

    # プロンプト表示
    tk.Label(popup, text=prompt, font=("Arial", 14)).pack(pady=(10, 0))

    # 入力欄
    entry_var = StringVar()
    entry = tk.Entry(popup, textvariable=entry_var, font=("Arial", 24), justify="right")
    entry.pack(pady=10, padx=10, fill="x")
    entry.focus_set()
    if default is not None:
        entry_var.set(str(default))
        entry.icursor(tk.END)

    # ボタンフレーム
    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=(0, 10))

    # ボタンコールバック
    def append_digit(d):
        entry_var.set(entry_var.get() + d)
    def clear_entry():
        entry_var.set("")

    def confirm_input(exclusive=False):
        val = entry_var.get().strip()
        # 正の整数チェック
        if not val.isdigit() or int(val) < 0:
            messagebox.showerror("入力エラー", "正の整数を入力してください。", parent=popup)
            return
        base = int(val)
        if tax_mode and exclusive:
            # 税別入力 → 税込価格に変換
            price = int(base * 1.1 + 0.5)
        else:
            price = base
        popup.result = price
        popup.destroy()

    # 数字ボタン配置
    buttons = [
        ("7", lambda: append_digit("7")), ("8", lambda: append_digit("8")), ("9", lambda: append_digit("9")),
        ("4", lambda: append_digit("4")), ("5", lambda: append_digit("5")), ("6", lambda: append_digit("6")),
        ("1", lambda: append_digit("1")), ("2", lambda: append_digit("2")), ("3", lambda: append_digit("3")),
        ("0", lambda: append_digit("0")), ("クリア", clear_entry)
    ]
    for idx, (txt, cmd) in enumerate(buttons):
        r, c = divmod(idx, 3)
        tk.Button(btn_frame, text=txt, command=cmd, font=("Arial", 18), width=4, height=2).grid(row=r, column=c, padx=5, pady=5)

    # 確定・税ボタン配置
    if tax_mode:
        tk.Button(btn_frame, text="税込", command=lambda: confirm_input(exclusive=False), font=("Arial", 18), width=4, height=2).grid(row=4, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="税別", command=lambda: confirm_input(exclusive=True), font=("Arial", 18), width=4, height=2).grid(row=4, column=2, padx=5, pady=5)
    else:
        tk.Button(btn_frame, text="入力", command=lambda: confirm_input(exclusive=False), font=("Arial", 18), width=4, height=2).grid(row=4, column=1, padx=5, pady=5)

    # キーイベント
    popup.bind('<Return>', lambda e: confirm_input(exclusive=False))
    popup.bind('<Escape>', lambda e: popup.destroy())

    # モーダル待機
    popup.wait_window()
    return popup.result

# テストコード
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    price1 = ask_price(root, prompt="通常入力テスト", default=1000)
    print("通常入力結果:", price1)
    price2 = ask_price(root, prompt="税モードテスト", tax_mode=True)
    print("税モード結果:", price2)
    root.destroy()
