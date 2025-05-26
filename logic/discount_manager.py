# --- ファイル: logic/discount_manager.py ---
"""
割引ロジックを管理するモジュール
・固定金額割引は合計額を単純加算で差し引く
・％割引は逐次乗算方式で適用
"""

class DiscountManager:
    def __init__(self):
        # 個別商品への割引: list of dict {type:'fixed'|'percent', index:int, value:float}
        self.item_discounts = []
        # 注文全体への割引: list of dict {type:'fixed'|'percent', value:float}
        self.order_discounts = []

    def apply_item_discount(self, index, amount):
        """
        カート内 index のアイテム価格から固定金額 amount を差し引く
        """
        self.item_discounts.append({'type': 'fixed', 'index': index, 'value': amount})

    def apply_item_percent(self, index, percent):
        """
        カート内 index のアイテム価格に percent(%) の割引を逐次乗算方式で適用
        """
        self.item_discounts.append({'type': 'percent', 'index': index, 'value': percent / 100.0})

    def apply_order_discount(self, amount):
        """
        注文全体から固定金額 amount を差し引く
        """
        self.order_discounts.append({'type': 'fixed', 'value': amount})

    def apply_order_percent(self, percent):
        """
        注文全体に percent(%) の割引を逐次乗算方式で適用
        """
        self.order_discounts.append({'type': 'percent', 'value': percent / 100.0})

    def calculate_total(self, cart):
        """
        アイテム単位の割引 + 全体割引を適用した最終合計を返す
        """
        # Deep copy prices to avoid mutating cart
        prices = [item['price'] for item in cart]

        # アイテム割引適用
        for d in self.item_discounts:
            idx = d['index']
            if idx < 0 or idx >= len(prices):
                continue
            if d['type'] == 'fixed':
                prices[idx] = max(0, prices[idx] - d['value'])
            else:
                prices[idx] = int(prices[idx] * (1 - d['value']) + 0.5)

        # 小計
        subtotal = sum(prices[i] * cart[i].get('quantity', 1) for i in range(len(cart)))

        # 全体割引適用
        total = subtotal
        for d in self.order_discounts:
            if d['type'] == 'fixed':
                total = max(0, total - d['value'])
            else:
                total = int(total * (1 - d['value']) + 0.5)

        return total
