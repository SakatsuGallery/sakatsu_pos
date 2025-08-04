# utils/printer.py
from escpos.printer import Network

class ReceiptPrinter:
    """
    ESC/POS サーマルプリンタへの印刷をラップするクラスです。
    """

    def __init__(self, host: str, port: int = 9100, timeout: int = 10):
        """
        host: プリンターの IP アドレス
        port: ESC/POS 通常ポート (デフォルト 9100)
        timeout: タイムアウト秒数
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        try:
            # ネットワーク接続を確立
            self.printer = Network(self.host, port=self.port, timeout=self.timeout)
            # 日本語コードページ CP932 (0x11) に設定
            self.printer._raw(b"\x1B\x74\x11")
        except Exception as e:
            raise RuntimeError(f"Printer connection failed: {e}")

    def execute(self, jobs):
        """
        jobs: List[Tuple[str, Optional[str], Dict[str, Any]]]
          - cmd: 'text' or 'cut'
          - text: 印字する文字列 (None 可能)
          - opts: set() に渡すパラメータ辞書
        """
        for cmd, text, opts in jobs:
            if cmd == 'text':
                # 文字スタイル設定
                self.printer.set(**opts)
                if text:
                    # 日本語をCP932でエンコード
                    raw = text.encode('cp932', errors='replace')
                    self.printer._raw(raw + b"\n")
            elif cmd == 'cut':
                # レシートカット
                self.printer.cut()
            elif cmd == 'image':
                # 画像印字：Python-escpos の image() を呼ぶ
                # text は画像パス
                self.printer.image(text)
            else:
                # 追加コマンドがあればここで分岐
                pass
        # キャッシュドロワーキック（ドロワー1）
        try:
            self.printer.cashdraw(0)
        except Exception:
            # ESC p m t1 t2: m=0, t1=50ms, t2=250ms
            self.printer._raw(b"\x1B\x70\x00\x32\xFA")
