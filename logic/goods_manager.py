# logic/goods_manager.py

from utils.file_utils import load_json, save_json
import os

class GoodsManager:
    def __init__(self, data_dir=None):
        # data_dir がなければ、同階層の data フォルダを想定
        base = os.path.dirname(os.path.dirname(__file__))
        self.data_dir = data_dir or os.path.join(base, "data")
        self.goods_file = os.path.join(self.data_dir, "goods_data.json")
        self.index = {}
        self.fallback = {}

    def load_index(self):
        """JSONファイルから商品マスタを読み込み、コード→商品辞書を構築"""
        with open(self.goods_file, "r", encoding="utf-8") as f:
            goods_list = load_json(f)
        self.index.clear()
        self.fallback.clear()
        for item in goods_list:
            code6 = item.get("goods_6_item")
            gid = item.get("goods_id")
            if code6:
                self.index[code6.lower()] = item
            if gid:
                self.fallback[gid.lower()] = item

    def lookup(self, code):
        """コード（goods_6_item or goods_id）で検索、なければ None を返す"""
        key = code.strip().lower()
        return self.index.get(key) or self.fallback.get(key)

    def all_goods(self):
        """全件マスターをリストで返す"""
        with open(self.goods_file, "r", encoding="utf-8") as f:
            return load_json(f)
