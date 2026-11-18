"""文档页里的流程图：手写坐标的内联 SVG。

为什么不用 mermaid：网页要能离线打开，而且自动布局排出来的图要逐张看才知道对不对。
图不多，坐标手写更稳。排版约定：主链一条竖线自上而下，分支一律甩到右边；
只在有语义的地方上色（拒绝=红、通过=绿、需要人判断=黄、关键一层=品牌绿）。

md 里对应位置仍是文字版代码块（飞书不渲染图，留文字版给它）。
build_docs.py 按代码块的第一行认出是哪张图，见 KEY。
"""
import html

FONT = "'PingFang SC',-apple-system,'Microsoft YaHei',sans-serif"
KINDS = {
    "plain": ("#ffffff", "#d5d9de", "#1a1a1a"),
    "soft":  ("#f7f8f9", "#e0e3e7", "#1a1a1a"),
    "key":   ("#f2fcfa", "#00c29a", "#00614d"),
    "ok":    ("#eaf7ef", "#2f9e5b", "#1d6b3c"),
    "stop":  ("#fff1f0", "#e5484d", "#b3261e"),
    "ask":   ("#fff8e1", "#d9a400", "#7a5200"),
}
LINE = "#8a9099"


def _text(cx, cy, lines, color, size=14, weight=400):
    lines = lines.split("\n")
    lh = size * 1.5
    y0 = cy - lh * (len(lines) - 1) / 2
    out = ""
    for i, ln in enumerate(lines):
        w = 500 if (i == 0 and len(lines) > 1) else weight
        s = size if i == 0 else size - 1.5
        out += (f'<text x="{cx}" y="{y0 + i * lh:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-size="{s}" font-weight="{w}" fill="{color}">{html.escape(ln)}</text>')
    return out


def box(x, y, w, h, text, kind="plain", pill=False):
    fill, stroke, color = KINDS[kind]
    r = h / 2 if pill else 10
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            + _text(x + w / 2, y + h / 2, text, color))


def diamond(cx, cy, w, h, text, kind="ask"):
    fill, stroke, color = KINDS[kind]
    pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>' + _text(cx, cy, text, color, size=13.5)


def arrow(pts, color=LINE, dash=False, head="a"):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    extra = ' stroke-dasharray="6 5"' if dash else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5"{extra} marker-end="url(#{head})"/>'


def label(x, y, text, color="#646464", anchor="start", size=13):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="central" font-size="{size}" '
            f'fill="{color}">{html.escape(text)}</text>')


def svg(w, h, body, title, minw, show=None):
    """w、h 是画布坐标；show 是电脑上显示的宽度（缺省等于 w）；minw 是手机上不再缩小的下限，0 表示一直缩到框宽。"""
    defs = ('<defs>'
            f'<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker>'
            '<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#e5484d"/></marker>'
            '</defs>')
    style = f' style="min-width:{minw}px"' if minw else ""
    return (f'<figure class="diagram"><svg viewBox="0 0 {w} {h}" width="{show or w}"{style} role="img" '
            f'aria-label="{html.escape(title)}" font-family="{FONT}">{defs}{body}</svg></figure>')


def loop():
    # 画布只有 330 宽：手机上框里能用的宽度约 322，这样几乎 1:1 显示，字不会缩到看不清，
    # 「不够就回到 ①」那条回头的线不用横滑也看得到。电脑上放大到 440 显示。
    cx = 130
    b = ""
    b += '<rect x="6" y="88" width="318" height="372" rx="14" fill="#fbfcfc" stroke="#00c29a" stroke-width="1.5" stroke-dasharray="6 5"/>'
    b += label(312, 106, "承载框架（Harness）管这一圈", "#009273", anchor="end", size=12.5)
    b += box(cx - 70, 16, 140, 44, "用户提问", "soft", pill=True)
    b += box(cx - 112, 126, 224, 50, "① 模型想：还要查什么？")
    b += box(cx - 112, 212, 224, 50, "② 调用一个工具")
    b += box(cx - 112, 298, 224, 50, "③ 拿到结果")
    b += diamond(cx, 404, 204, 76, "够回答了吗？")
    b += box(cx - 70, 488, 140, 44, "给出答复", "ok", pill=True)
    for y1, y2 in ((60, 126), (176, 212), (262, 298), (348, 366), (442, 488)):
        b += arrow([(cx, y1), (cx, y2)])
    b += label(cx + 10, 470, "够了")
    # 回路：从判定框右尖出，绕回 ①
    b += arrow([(cx + 102, 404), (274, 404), (274, 151), (cx + 112, 151)])
    b += label(281, 268, "不够")
    b += label(281, 286, "再查")
    b += label(8, 566, "这一圈里我们加了：", "#1a1a1a", size=13)
    for i, t in enumerate(["按岗位发放的工具名单", "13 个技能（固定动作）", "6 个守卫（关不掉）", "预算上限", "每一轮的记录"]):
        b += f'<circle cx="12" cy="{594 + i * 25}" r="2.5" fill="#00c29a"/>' + label(24, 594 + i * 25, t, size=13)
    return svg(330, 710, b, "智能体的工作循环：提问、想、调用工具、拿结果、判断够不够，不够就再查", 0, show=440)


def write_gate():
    cx = 220
    b = box(cx - 90, 16, 180, 44, "模型想写入", "soft", pill=True)
    b += diamond(cx, 126, 270, 84, "是 33 个可写\n工具之一？")
    b += diamond(cx, 256, 270, 84, "预演：这个岗位\n业务允许吗？")
    b += diamond(cx, 386, 270, 84, "踩中四道\n行为闸了吗？")
    b += box(cx - 130, 478, 260, 56, "写入，并记操作日志\n谁、什么时候、改了什么、为什么允许", "ok")
    b += arrow([(cx, 60), (cx, 84)])
    for y1, y2, t in ((168, 214, "是"), (298, 344, "允许"), (428, 478, "没踩中")):
        b += arrow([(cx, y1), (cx, y2)]) + label(cx + 12, (y1 + y2) / 2, t)
    for cy, t, lab in ((126, "拒绝", "不是"), (256, "拒绝，并说清缺什么", "不允许"), (386, "拦下", "踩中任何一道")):
        b += arrow([(cx + 135, cy), (470, cy)], "#e5484d", head="r")
        b += label((cx + 135 + 470) / 2, cy - 12, lab, "#b3261e", "middle", 12.5)
        b += box(470, cy - 22, 220, 44, t, "stop")
    x = 470
    b += label(x, 432, "四道行为闸：", "#1a1a1a")
    for i, t in enumerate(["连着写好几条 *", "一模一样的参数再试一次", "已经成功过一次还要写 *", "试了三次都没成"]):
        b += f'<circle cx="{x + 4}" cy="{458 + i * 24}" r="2.5" fill="#e5484d"/>' + label(x + 16, 458 + i * 24, t, size=12.5)
    b += label(x, 458 + 4 * 24 + 4, "* 只管派任务、排班这类动作", "#a3a3a3", size=12)
    return svg(720, 580, b, "写入的四步闸：是否可写工具、预演是否允许、是否踩中行为闸，都通过才写入并记日志", 640)


def arch():
    cx = 360
    b = box(cx - 100, 16, 200, 48, "模型（会说话）", "soft", pill=True)
    xs = (40, 260, 480)
    texts = ("规矩 127 条\n按岗位配置", "工具 110 个\n分属 8 个业务服务", "闸\n读、写、答三层")
    for x, t in zip(xs, texts):
        b += box(x, 124, 200, 60, t)
        b += arrow([(cx, 64), (cx, 94), (x + 100, 94), (x + 100, 124)])
    b += box(cx - 180, 244, 360, 64, "口径模块 59 个\n业务规矩写在这里，不写在工具里", "key")
    b += box(cx - 180, 368, 360, 52, "数据库 136 张表", "soft")
    b += arrow([(cx, 184), (cx, 244)]) + label(cx + 12, 214, "工具只负责取数")
    b += arrow([(cx, 308), (cx, 368)])
    return svg(720, 436, b, "总体结构：模型通过工具、规矩和闸工作，工具下面是口径模块，再下面是数据库", 600)


def chain():
    ts = ("人手写规则", "程序推导\n出结论", "存进数据库", "包成\n只读工具", "智能体查询")
    b = ""
    for i, t in enumerate(ts):
        x = 2 + i * 158
        b += box(x, 16, 128, 60, t, "key" if i == 0 else "plain")
        if i:
            b += arrow([(x - 30, 46), (x, 46)])
    b += arrow([(2 + 4 * 158 + 64, 76), (2 + 4 * 158 + 64, 118), (66, 118), (66, 80)], "#e5484d", dash=True, head="r")
    b += label(382, 136, "✕ 反方向一步都不许走：数据库里的数不回写进规则", "#b3261e", "middle", 12.5)
    return svg(764, 154, b, "知识单向链：人写规则，程序推导，存库，包成只读工具，智能体查询；不许反向回写", 680)


def v2():
    b = ""
    items = (("规则查数据", "plain", "不调用模型"), ("规则判断原因", "plain", "不调用模型"), ("模型写成一段话", "key", "只在这一步调用模型，1 次"))
    for i, (t, k, cap) in enumerate(items):
        x = 2 + i * 250
        b += box(x, 12, 196, 56, t, k)
        b += label(x + 98, 88, cap, "#009273" if k == "key" else "#a3a3a3", "middle", 12.5)
        if i:
            b += arrow([(x - 54, 40), (x, 40)])
    return svg(700, 104, b, "第二代的流程：规则查数据，规则判断原因，模型只负责写成一段话", 600)


def queue():
    b = ""
    items = (("扫出事项", "soft", "系统每天扫"), ("AI 研判\n根因、建议、证据", "key", "AI 出草稿"),
             ("人复核\n采纳、改判、升级", "ask", "人签字"), ("办结\n凭系统单号回执", "ok", "系统核对回执"))
    for i, (t, k, cap) in enumerate(items):
        x = 2 + i * 190
        b += box(x, 12, 150, 64, t, k)
        b += label(x + 75, 96, cap, "#646464", "middle", 12.5)
        if i:
            b += arrow([(x - 40, 44), (x, 44)])
    return svg(724, 112, b, "研判队列一件事怎么走完：扫出事项，AI 研判，人复核，凭回执办结", 660)


# 文字版代码块的第一行 → 对应的图
KEY = {
    "用户提问": loop,
    "模型想写": write_gate,
    "模型（会说话）": arch,
    "人手写规则  →  程序推导出结论  →  存进数据库  →  包成只读工具  →  智能体查询": chain,
    "规则查数据  →  规则判断原因  →  模型只负责写这段话": v2,
    "扫出事项  →  AI 研判  →  人复核  →  办结": queue,
}
