#!/usr/bin/env python3
"""把飞书文档里的文字版流程图换成图片。用法：python3 feishu_diagrams.py <飞书文档链接或编号>

为什么要有：飞书导入 Markdown 不会画图，流程在飞书里只是文字代码块。
这里把网页用的同一批图（diagrams.py）导成图片插进去，两边看到的是同一张图。
每次重发飞书文档后都要重跑一次（重发会生成新文档，图不会带过去）。
凭证沿用发布脚本的缓存，不在本仓库里。
"""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "澜绣云裳agent" / "tools"))
import feishu_publish as fp
import diagrams
from PIL import Image, ImageChops

API = "https://open.feishu.cn/open-apis"


def call(method, url, token, body=None, form=None):
    cmd = ["curl", "-s", "-X", method, url]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json; charset=utf-8", "-d", json.dumps(body, ensure_ascii=False)]
    for f in form or []:
        cmd += ["-F", f]
    r = fp._跑curl(cmd, token, 120)
    if not isinstance(r, dict):
        r = json.loads(r if isinstance(r, str) else getattr(r, "stdout", r))
    if r.get("code") != 0:
        sys.exit(f"❌ {method} {url.split('/open-apis')[1][:60]} 失败：{r.get('code')} {r.get('msg')}")
    return r.get("data", {})


def png_of(fn, out):
    svg = re.search(r"<svg.*</svg>", fn(), re.S).group(0).replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    svg = re.sub(r' width="\d+"', "", svg, count=1)
    src = out.with_suffix(".svg"); src.write_text(svg, encoding="utf-8")
    subprocess.run(["qlmanage", "-t", "-s", "1800", "-o", str(out.parent), str(src)], capture_output=True)
    im = Image.open(str(src) + ".png").convert("RGBA")
    bg = Image.new("RGBA", im.size, "white"); bg.alpha_composite(im); im = bg.convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if not box:
        sys.exit(f"❌ {fn.__name__} 导出来是空白图")
    pad = 24
    im = im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height)))
    im.save(out); return im.size


def blocks(doc, token):
    out, page = [], ""
    while True:
        d = call("GET", f"{API}/docx/v1/documents/{doc}/blocks?page_size=500" + (f"&page_token={page}" if page else ""), token)
        out += d.get("items", [])
        if not d.get("has_more"):
            return out
        page = d["page_token"]


def first_line(b):
    els = (b.get("code") or {}).get("elements", [])
    return "".join(e.get("text_run", {}).get("content", "") for e in els).split("\n")[0].strip()


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    doc = sys.argv[1].rstrip("/").split("/")[-1].split("?")[0]
    token = fp.acquire_token()
    tmp = Path(tempfile.mkdtemp())
    done = 0
    todo = [b for b in blocks(doc, token) if b.get("block_type") == 14 and first_line(b) in diagrams.KEY]
    print(f"找到 {len(todo)} 个要换的文字流程图（应为 {len(diagrams.KEY)} 个）")
    for b in reversed(todo):   # 从后往前，前面的位置不受影响
        fn = diagrams.KEY[first_line(b)]
        png = tmp / f"{fn.__name__}.png"; w, h = png_of(fn, png)
        parent = b["parent_id"]
        kids = next(x for x in blocks(doc, token) if x["block_id"] == parent)["children"]
        i = kids.index(b["block_id"])
        new = call("POST", f"{API}/docx/v1/documents/{doc}/blocks/{parent}/children", token,
                   {"index": i, "children": [{"block_type": 27, "image": {}}]})["children"][0]["block_id"]
        ft = call("POST", f"{API}/drive/v1/medias/upload_all", token, form=[
            f"file_name={png.name}", "parent_type=docx_image", f"parent_node={new}",
            f"size={png.stat().st_size}", f"file=@{png}"])["file_token"]
        call("PATCH", f"{API}/docx/v1/documents/{doc}/blocks/{new}", token, {"replace_image": {"token": ft}})
        call("DELETE", f"{API}/docx/v1/documents/{doc}/blocks/{parent}/children/batch_delete", token,
             {"start_index": i + 1, "end_index": i + 2})
        done += 1; print(f"  ✓ {fn.__name__}（{w}×{h}）")
    left = [b for b in blocks(doc, token) if b.get("block_type") == 14 and first_line(b) in diagrams.KEY]
    imgs = sum(1 for b in blocks(doc, token) if b.get("block_type") == 27)
    print(f"换了 {done} 张；文档里现在有 {imgs} 个图片块，剩 {len(left)} 个没换的文字流程图")
    print(f"图片留在 {tmp}，可以打开看")
    if done != len(diagrams.KEY) or left:
        sys.exit("❌ 没换全")


if __name__ == "__main__":
    main()
