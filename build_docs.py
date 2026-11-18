#!/usr/bin/env python3
"""把《澜绣云裳agent-产品介绍.md》生成 docs.html。

文案只写在 md 里：飞书发这份 md，网页文档页由本脚本生成，两边说法不会不一致。
约定：## 是侧栏分组，### 是一页，#### 是页内小节。
"""
import html
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "澜绣云裳agent-产品介绍.md"
OUT = HERE / "docs.html"

# 页面标题 → 网址里的锚点；新加页面必须在这里登记
IDS = {
    "简介": "intro", "它解决什么问题": "problems", "谁在用": "roles", "和聊天机器人的区别": "diff",
    "对话助手": "chat", "研判队列": "queue", "方案配置": "scheme", "着装人管理": "wearers",
    "值班台": "duty", "面料学堂": "fabric", "经营报告": "report", "管理后台": "admin",
    "哪些事必须人签字": "sign", "明确不做的事": "not", "客户信息保护": "privacy",
    "怎么保证它是对的": "verify", "三种做法的对比": "compare", "数据与现状说明": "status",
    "常见问题": "faq",
}
# 有真实截图的页面
SHOTS = {"chat": "对话助手", "queue": "研判队列", "scheme": "方案配置", "wearers": "着装人管理"}


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" rel="noopener" style="color:var(--brand-deep)">\1</a>', s)


def body(lines):
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.startswith("#### "):
            out.append(f"<h2>{inline(ln[5:])}</h2>"); i += 1
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            head, rest = rows[0], rows[2:]
            t = "<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>"
            for r in rest:
                t += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            out.append(t + "</table>")
        elif re.match(r"^(- |\d+\. )", ln):
            tag = "ul" if ln.startswith("- ") else "ol"
            items = []
            while i < len(lines) and re.match(r"^(- |\d+\. )", lines[i]):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i])); i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
        elif ln.startswith("> "):
            cls = "note warn" if ln.startswith("> 限定") or ln.startswith("> 说明") else "note"
            out.append(f'<div class="{cls}">{inline(ln[2:])}</div>'); i += 1
        else:
            out.append(f"<p>{inline(ln)}</p>"); i += 1
    return "\n".join(out)


def main():
    lines = SRC.read_text(encoding="utf-8").splitlines()
    groups, group, page = [], None, None
    for ln in lines:
        if ln.startswith("## "):
            group = {"name": ln[3:].strip(), "pages": []}; groups.append(group); page = None
        elif ln.startswith("### "):
            title = ln[4:].strip()
            if title not in IDS:
                sys.exit(f"❌ 页面「{title}」没有在 IDS 里登记锚点")
            page = {"title": title, "id": IDS[title], "lines": []}; group["pages"].append(page)
        elif page is not None:
            page["lines"].append(ln)
    pages = [(g["name"], p) for g in groups for p in g["pages"]]
    if len(pages) != len(IDS):
        sys.exit(f"❌ md 里有 {len(pages)} 页，IDS 登记了 {len(IDS)} 页，对不上")

    side = ""
    for g in groups:
        side += f'<div class="grp">{html.escape(g["name"])}</div>\n'
        for p in g["pages"]:
            side += f'<a href="#{p["id"]}" data-id="{p["id"]}">{html.escape(p["title"])}</a>\n'

    main_html = ""
    for n, (gname, p) in enumerate(pages):
        content = body(p["lines"])
        # 第一段当导语
        content = re.sub(r"^<p>", '<p class="intro">', content, count=1) if content.startswith("<p>") else content
        shot = ""
        if p["id"] in SHOTS:
            shot = (f'<div class="shot" data-name="{SHOTS[p["id"]]}（{p["id"]}.png）">'
                    f'<img src="screenshots/{p["id"]}.png" alt="{SHOTS[p["id"]]}界面"><span class="tag">演示数据</span></div>')
        prev = pages[n - 1][1] if n else None
        nxt = pages[n + 1][1] if n + 1 < len(pages) else None
        pager = '<div class="pager">'
        pager += (f'<a href="#{prev["id"]}"><small>上一页</small>{html.escape(prev["title"])}</a>' if prev else '<a class="hide"></a>')
        pager += (f'<a class="next" href="#{nxt["id"]}"><small>下一页</small>{html.escape(nxt["title"])}</a>' if nxt else '<a class="hide"></a>')
        pager += "</div>"
        main_html += (f'<article class="doc" id="{p["id"]}">\n<div class="crumb">{html.escape(gname)}</div>\n'
                      f'<h1>{html.escape(p["title"])}</h1>\n{content}\n{shot}\n{pager}\n</article>\n')

    OUT.write_text(TEMPLATE.replace("{{SIDE}}", side).replace("{{MAIN}}", main_html), encoding="utf-8")
    print(f"✅ 生成 {OUT.name}：{len(groups)} 个分组，{len(pages)} 页")


TEMPLATE = """<!doctype html>
<html lang="zh-CN" class="nojs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>文档 · 澜绣云裳</title>
<meta name="description" content="澜绣云裳功能文档：每个功能的场景、使用岗位、痛点、解决方式、输入与输出。">
<link rel="stylesheet" href="style.css">
<script>document.documentElement.classList.remove('nojs')</script>
</head>
<body>
<!-- 本页由 build_docs.py 从《澜绣云裳agent-产品介绍.md》生成，改内容请改那份 md -->
<header class="head">
  <div class="wrap" style="max-width:1280px">
    <a class="logo" href="index.html"><span class="logo-mark">澜</span>澜绣云裳</a>
    <nav class="nav"><a href="index.html">首页</a><a class="on" href="docs.html">文档</a></nav>
    <button class="btn btn-line btn-sm menu-btn" id="menu">目录</button>
  </div>
</header>
<div class="docs">
<aside class="side" id="side">
{{SIDE}}</aside>
<main class="doc-main">
{{MAIN}}</main>
</div>
<script>
var docs = document.querySelectorAll('.doc'), links = document.querySelectorAll('.side a'), side = document.getElementById('side');
function show() {
  var id = location.hash.slice(1);
  if (!document.getElementById(id) || !document.getElementById(id).classList.contains('doc')) id = docs[0].id;
  docs.forEach(function (d) { d.classList.toggle('on', d.id === id); });
  links.forEach(function (a) { a.classList.toggle('on', a.dataset.id === id); });
  side.classList.remove('open');
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', show);
show();
document.getElementById('menu').addEventListener('click', function () { side.classList.toggle('open'); });
document.querySelectorAll('.shot img').forEach(function (img) {
  function empty() { img.parentNode.classList.add('empty'); }
  if (img.complete && !img.naturalWidth) empty();
  img.addEventListener('error', empty);
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
