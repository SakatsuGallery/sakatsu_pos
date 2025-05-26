# test_tenkey.py
import tkinter as tk
from ui.tenkey_popup import ask_price

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを非表示
    price = ask_price(
        root,
        title="未登録商品の価格入力",
        prompt="価格を入力してください："
    )
    print("入力された価格：", price)
    root.destroy()
