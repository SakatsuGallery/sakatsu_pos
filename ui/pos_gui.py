# ui/pos_gui.py

import os
import subprocess
import threading
import tkinter as tk
import winsound
from tkinter import messagebox

from ui.daily_tasks import run_daily_tasks
from logic.cash_flow_recorder import CashFlowRecorder
from logic.discount_manager import DiscountManager
from logic.goods_manager import GoodsManager

# 新しい支払いロジック関数
from logic.payment_manager import reset_payments  # 事前に payment_manager.py に実装してある想定です
from logic.payment_manager import get_initial_amount, get_payments_summary, process_payment
from logic.sales_recorder import SalesRecorder
from ui.tenkey_popup import ask_price

# ビープ音再生用ファイルパス
WAVE_PATH = os.path.join(os.path.dirname(__file__), "..", "wave", "key.wav")


def play_beep():
    try:
        winsound.PlaySound(WAVE_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


class POSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sakatsu POS")

        # 各マネージャ初期化
        self.gm = GoodsManager()
        self.gm.load_index()
        self.cf_recorder = CashFlowRecorder(data_dir="data")
        self.sales_recorder = SalesRecorder(data_dir="data")
        self.discount_manager = DiscountManager()

        # カート・未決済額
        self.cart = []
        self.remaining_due = 0.0

        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        # 入力欄
        tk.Label(frame, text="バーコードまたは商品コード").grid(row=0, column=0, sticky="w")
        self.code_entry = tk.Entry(frame, width=30)
        self.code_entry.grid(row=0, column=1)
        self.code_entry.bind(
            "<Return>", lambda e: (play_beep(), self.search_product(auto_register=True))
        )
        self.code_entry.bind("<Escape>", lambda e: (play_beep(), self.reset_code_entry()))
        self.code_entry.bind("<KeyRelease>", lambda e: (play_beep(), self.update_suggestion()))

        self.suggestion_var = tk.StringVar()
        tk.Label(frame, textvariable=self.suggestion_var, fg="gray").grid(
            row=0, column=2, sticky="w"
        )

        # 商品名・価格表示
        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        tk.Label(frame, text="商品名").grid(row=1, column=0, sticky="w")
        tk.Label(frame, textvariable=self.name_var).grid(row=1, column=1, sticky="w")
        tk.Label(frame, text="価格").grid(row=2, column=0, sticky="w")
        tk.Label(frame, textvariable=self.price_var).grid(row=2, column=1, sticky="w")

        # 操作ボタン
        buttons = [
            ("登録", self.register_product),
            ("クリア", self.clear_last),
            ("全クリア", self.clear_all),
            ("確定", self.finalize_sale),
            ("入金", self.handle_deposit),
            ("出金", self.handle_withdraw),
            ("個別¥値引き", self.handle_item_fixed_discount),
            ("個別％値引き", self.handle_item_percent_discount),
            ("全体¥値引き", self.handle_order_fixed_discount),
            ("全体％値引き", self.handle_order_percent_discount),
            ("機能", self.show_features),
            ("日次", self.run_daily),
            ("月次", self.run_monthly),
        ]
        for i, (text, cmd) in enumerate(buttons):
            tk.Button(frame, text=text, command=lambda c=cmd: (play_beep(), c())).grid(
                row=3, column=i, padx=5, pady=5
            )

        # カートリスト
        tk.Label(frame, text="登録リスト").grid(row=4, column=0, sticky="nw")
        self.listbox = tk.Listbox(frame, width=50, height=12)
        self.listbox.grid(row=4, column=1, columnspan=len(buttons) - 1, sticky="w")

        # 合計表示
        self.total_var = tk.StringVar(value="合計: ¥0 円")
        tk.Label(frame, textvariable=self.total_var, font=("Arial", 12, "bold")).grid(
            row=5, column=len(buttons) - 2, columnspan=2, sticky="e"
        )

        # 日次処理実行ボタン
        self.daily_btn = tk.Button(frame, text="日次処理実行", command=self.run_daily_tasks)
        self.daily_btn.grid(row=6, column=0, columnspan=len(buttons), pady=10)

    # ――――― 商品検索まわり ―――――
    def reset_code_entry(self):
        self.code_entry.delete(0, tk.END)
        self.name_var.set("")
        self.price_var.set("")
        self.suggestion_var.set("")

    def update_suggestion(self):
        code = self.code_entry.get().strip().lower()
        product = self.gm.lookup(code)
        self.suggestion_var.set(f"候補: {product.get('goods_name', '')}" if product else "")

    def search_product(self, auto_register=False):
        code = self.code_entry.get().strip().lower()
        product = self.gm.lookup(code)
        if product:
            self.name_var.set(product.get("goods_name", ""))
            self.price_var.set(str(product.get("goods_selling_price", "")))
        else:
            self.name_var.set(code[:20])
            self.price_var.set("")
        if auto_register:
            self.register_product()

    # ――――― カート登録まわり ―――――
    def register_product(self):
        code = self.code_entry.get().strip().lower()
        product = self.gm.lookup(code)
        if product:
            item_name = product.get("goods_name", "")
            # Next Engine からの価格を整数化
            price_value = int(float(product.get("goods_selling_price", 0)))
        else:
            raw = self.code_entry.get().strip()
            amt = ask_price(
                self.root, title="未登録商品の価格入力", prompt="価格を入力してください："
            )
            if amt is None:
                return
            item_name = raw[:20]
            # ユーザー入力分も整数化
            price_value = int(amt)

        item = {
            "goods_id": code if product else "",
            "name": item_name,
            "price": price_value,
            "quantity": 1,
        }
        self.cart.append(item)

        # 表示用に20文字超えを省略
        display_name = item_name if len(item_name) <= 20 else item_name[:20] + "…"
        self.listbox.insert(tk.END, f"{display_name}  ¥{int(price_value)}円")
        self.update_total()
        self.reset_code_entry()

    def update_total(self):
        total = self.discount_manager.calculate_total(self.cart)
        self.total_var.set(f"合計: ¥{int(total)} 円")

    # ――――― 割引まわり ―――――
    def handle_item_fixed_discount(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("選択エラー", "割引対象を選択してください")
            return
        idx = sel[0]
        if self.listbox.get(idx).startswith("  "):
            messagebox.showwarning("選択エラー", "商品行を選択してください")
            return

        amt = ask_price(self.root, title="個別金額割引", prompt="割引額を入力してください：")
        if amt is None:
            return
        # カートインデックス算出
        item_index = sum(1 for j in range(idx + 1) if not self.listbox.get(j).startswith("  ")) - 1

        self.discount_manager.apply_item_discount(item_index, amt)
        self.listbox.insert(idx + 1, f"  個別値引き –¥{int(amt)}円")
        self.update_total()

    def handle_item_percent_discount(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("選択エラー", "割引対象を選択してください")
            return
        idx = sel[0]
        if self.listbox.get(idx).startswith("  "):
            messagebox.showwarning("選択エラー", "商品行を選択してください")
            return

        pct = ask_price(self.root, title="個別％割引", prompt="割引率(％)を入力してください：")
        if pct is None:
            return

        item_index = sum(1 for j in range(idx + 1) if not self.listbox.get(j).startswith("  ")) - 1

        self.discount_manager.apply_item_percent(item_index, pct)
        original = self.cart[item_index]["price"]
        disc = int(original * pct / 100 + 0.5)
        self.listbox.insert(idx + 1, f"  個別％値引き –¥{disc}円")
        self.update_total()

    def handle_order_fixed_discount(self):
        amt = ask_price(self.root, title="全体金額割引", prompt="割引額を入力してください：")
        if amt is None:
            return
        self.discount_manager.apply_order_discount(amt)
        self.listbox.insert(tk.END, f"全体値引き –¥{int(amt)}円")
        self.update_total()

    def handle_order_percent_discount(self):
        pct = ask_price(self.root, title="全体％割引", prompt="割引率(％)を入力してください：")
        if pct is None:
            return
        old_total = self.discount_manager.calculate_total(self.cart)
        self.discount_manager.apply_order_percent(pct)
        new_total = self.discount_manager.calculate_total(self.cart)
        disc = old_total - new_total
        self.listbox.insert(tk.END, f"全体％値引き –¥{int(disc)}円")
        self.update_total()

    # ――――― クリアまわり ―――――
    def clear_last(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])
            self.update_total()
            return

        last = self.listbox.size() - 1
        if last < 0:
            return
        text = self.listbox.get(last)
        if text.startswith("全体"):
            self.discount_manager.order_discounts.pop()
        elif text.startswith("  "):
            self.discount_manager.item_discounts.pop()
        else:
            self.cart.pop()
            if last > 0 and self.listbox.get(last - 1).startswith("  "):
                self.discount_manager.item_discounts.pop()
        self.listbox.delete(last)
        self.update_total()

    def clear_all(self):
        self.cart.clear()
        self.listbox.delete(0, tk.END)
        self.discount_manager.item_discounts.clear()
        self.discount_manager.order_discounts.clear()
        self.update_total()

    # ――――― 会計／決済まわり ―――――
    def finalize_sale(self):
        if not self.cart:
            messagebox.showinfo("確認", "登録されている商品がありません")
            return

        # 売上合計を計算し、支払いバッファをリセット
        total_due = self.discount_manager.calculate_total(self.cart)
        reset_payments()
        self.remaining_due = total_due
        # 支払いポップアップに合計額を渡す
        self.open_payment_popup(total_due)

    def open_payment_popup(self, total_due):
        popup = tk.Toplevel(self.root)
        popup.grab_set()
        popup.title("支払い")
        popup.attributes("-topmost", True)
        popup.lift()

        label = tk.Label(popup, text=f"未決済額：¥{int(self.remaining_due)}")
        label.pack(padx=10, pady=5)

        def _process(method: str):
            init_amt = get_initial_amount(method, self.remaining_due)
            kw = {"default": init_amt} if init_amt is not None else {}
            amt = ask_price(
                popup,
                title=f"{method}支払額入力",
                prompt=f"支払額を入力してください（残¥{int(self.remaining_due)}）：",
                **kw,
            )
            if amt is None:
                return

            result = process_payment(method, self.remaining_due, amt)
            status = result["status"]

            if status == "pending":
                # 部分支払い: 残額を更新して、再度支払いポップアップを表示
                self.remaining_due = result["remaining_due"]
                messagebox.showinfo("支払い継続", result["message"])
                popup.destroy()
                # total_due は元の合計金額を渡しつつ再表示
                self.open_payment_popup(total_due)
                return

            if status == "complete":
                change = result.get("change", 0.0)
                if change > 0:
                    messagebox.showinfo("おつり", f"おつり¥{int(change)}")
                popup.destroy()
                # total_due は外部から渡された値を使う
                self.complete_payment(total_due)
                return

            if status == "warning":
                messagebox.showwarning("支払いエラー", result["message"])
                return

        for m in ["現金", "クレカ", "QR"]:
            tk.Button(popup, text=m, command=lambda m=m: _process(m)).pack(side="left", padx=5)
        tk.Button(popup, text="キャンセル", command=popup.destroy).pack(side="left", padx=5)

    def complete_payment(self, total_due):
        summary = get_payments_summary()
        payments = [{"method": m, "amount": a} for m, a in summary.items() if a > 0]
        total_paid = sum(summary.values())
        change = max(0, int(total_paid - total_due))

        path = self.sales_recorder.record_sale(
            self.cart, total_due=total_due, payments=payments, change=change
        )
        info = "売上を記録しました。\n"
        if change > 0:
            info += f"おつり：¥{change}\n"
        info += path
        messagebox.showinfo("会計完了", info)

        # 会計完了後のUIクリア
        self.cart.clear()
        self.listbox.delete(0, tk.END)
        self.update_total()
        # ここで割引設定をリセットし、次回会計に引き継がれないようにする
        self.discount_manager.item_discounts.clear()
        self.discount_manager.order_discounts.clear()
        # 支払い累計もリセット
        reset_payments()

    # ――――― 入出金 ―――――
    def handle_deposit(self):
        amt = ask_price(self.root, title="入金額入力", prompt="現金入金額を入力してください：")
        if amt is None:
            return
        path = self.cf_recorder.record_deposit(amount=amt)
        messagebox.showinfo(
            "入金完了", f"{int(amt):,} 円を入金として記録しました。\n{path} へ保存されました。"
        )

    def handle_withdraw(self):
        amt = ask_price(self.root, title="出金額入力", prompt="現金出金額を入力してください：")
        if amt is None:
            return
        path = self.cf_recorder.record_withdraw(amount=amt)
        messagebox.showinfo(
            "出金完了", f"{int(amt):,} 円を出金として記録しました。\n{path} へ保存されました。"
        )

    # ――――― 日次／月次 ―――――
    def run_daily_tasks(self):
        try:
            subprocess.Popen(["python", "ui/daily_tasks.py"], cwd=os.getcwd())
            messagebox.showinfo(
                "日次処理実行", "日次処理を開始しました。\n終了後にログをご確認ください。"
            )
        except Exception as e:
            messagebox.showerror("日次処理エラー", str(e))

    def show_features(self):
        features = ["日次処理実行"]
        messagebox.showinfo("機能一覧", "\n".join(features))

    def show_toast(self, message: str, duration: int = 3000):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        tk.Label(toast, text=message, bg="#333", fg="white", padx=10, pady=5).pack()
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - (toast.winfo_reqwidth() // 2)
        y = self.root.winfo_rooty() + self.root.winfo_height() - toast.winfo_reqheight() - 50
        toast.geometry(f"+{x}+{y}")
        toast.after(duration, toast.destroy)

    def run_daily(self):
        def task():
            try:
                run_daily_tasks(mode="daily")
                self.show_toast("日次処理完了")
            except Exception as e:
                messagebox.showerror("日次処理エラー", str(e))

        threading.Thread(target=task, daemon=True).start()

    def run_monthly(self):
        def task():
            try:
                run_daily_tasks(mode="monthly")
                self.show_toast("月次処理完了")
            except Exception as e:
                messagebox.showerror("月次処理エラー", str(e))

        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = POSApp(root)
    root.mainloop()
