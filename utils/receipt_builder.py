import yaml
from typing import List, Tuple, Dict, Any

class ReceiptBuilder:
    """
    レイアウト設定（YAML）をもとに、ReceiptPrinter に渡す印刷ジョブを生成します。
    """

    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config: Dict[str, Any] = yaml.safe_load(f)

    def _fit_text(self, text: str, width: int) -> str:
        """
        全角を2文字、半角を1文字として幅を計算し、指定幅に収まるよう切り詰め、足りない分はスペースで埋める
        """
        w = 0
        out = ''
        for ch in text:
            char_width = 2 if ord(ch) > 127 else 1
            if w + char_width > width:
                break
            out += ch
            w += char_width
        out += ' ' * (width - w)
        return out

    def build(self, sale: Dict[str, Any]) -> List[Tuple[str, Any, Dict[str, Any]]]:
        job: List[Tuple[str, Any, Dict[str, Any]]] = []

        # ヘッダー部（画像対応含む）
        for entry in self.config.get('header', []):
            if 'image' in entry:
                opts = {'align': entry.get('align', 'center')}
                job.append(('image', entry['image'], opts))
            else:
                opts: Dict[str, Any] = {}
                if 'align' in entry:
                    opts['align'] = entry['align']
                if entry.get('weight') == 'bold':
                    opts['bold'] = True
                if entry.get('size') == 'large':
                    opts['width'] = 2
                    opts['height'] = 2
                job.append(('text', entry['text'], opts))
        job.append(('text', '', {}))

        # 日時表示
        body_cfg = self.config.get('body', {})
        dt_cfg = body_cfg.get('datetime', {})
        dt_label = dt_cfg.get('label', '')
        dt_fmt = dt_cfg.get('format', '%Y/%m/%d %H:%M:%S')
        dt_str = sale['timestamp'].strftime(dt_fmt)
        job.append(('text', f"{dt_label} {dt_str}", {}))

        # 区切り線
        sep = body_cfg.get('separator', '-' * 48)
        job.append(('text', sep, {}))

        # 明細ヘッダー
        cols = body_cfg.get('columns', [])
        header_line = ''
        # 全角2、半角1の幅を数える
        def disp_width(text: str) -> int:
            return sum(2 if ord(ch) > 127 else 1 for ch in text)
        for col in cols:
            name = col['name']
            width = col['width']
            align = col.get('align', 'left')
            display = '数' if name in ('数量', '数') else name
            if align == 'right':
                pad = width - disp_width(display)
                header_line += ' ' * pad + display
            else:
                header_line += self._fit_text(display, width)
        job.append(('text', header_line, {'bold': True}))
        job.append(('text', sep, {}))

        # 商品明細
        for item in sale['items']:
            line = ''
            for col in cols:
                name = col['name']
                width = col['width']
                if name == '商品名':
                    text = self._fit_text(item.get('name', ''), width)
                elif name in ('数量', '数'):
                    text = str(item.get('quantity', 0)).rjust(width)
                elif name == '単価':
                    text = f"{item.get('price', 0):,}".rjust(width)
                elif name == '金額':
                    amt = item.get('price', 0) * item.get('quantity', 0)
                    text = f"{amt:,}".rjust(width)
                else:
                    text = ' ' * width
                line += text
            job.append(('text', line, {}))
        job.append(('text', sep, {}))

        # 税サマリー
        total = sale.get('total', 0)
        tax_base = total * 10 // 11
        tax_value = total - tax_base
        line1 = self._fit_text('10%対象', 48 - disp_width(f"{total:,}")) + f"{total:,}"
        job.append(('text', line1, {}))
        prefix = '(内消費税等 10%'
        suffix = f"{tax_value:,})"
        spaces = 48 - disp_width(prefix) - disp_width(suffix)
        line2 = prefix + (' ' * max(spaces, 0)) + suffix
        job.append(('text', line2, {}))
        job.append(('text', sep, {}))

        # フッター部（YAML制御）
        for entry in self.config.get('footer', []):
            opts: Dict[str, Any] = {}
            if 'align' in entry:
                opts['align'] = entry['align']
            text = entry['text'].format(
                total=sale.get('total', 0),
                pay_amount=sale.get('pay_amount', 0),
                change=sale.get('change', 0),
                pay_method_name=sale.get('pay_method_name', '')
            )
            job.append(('text', text, opts))
        job.append(('cut', None, {}))
        return job
