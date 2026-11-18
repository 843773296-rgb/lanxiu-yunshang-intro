#!/usr/bin/env python3
"""给 assets/ 里的服装图写回「AI 生成」的隐式标识（XMP 的 DigitalSourceType）。

为什么要有：原图带 C2PA 内容凭证（写明由 AI 生成），缩小成 jpg 时丢了。
《人工智能生成合成内容标识办法》要求不得隐匿生成合成内容标识，所以补回来。
做法是往文件头插一段 XMP，不重新压缩画面；重复运行不会重复插入。
新增或替换服装图后要再跑一次。
"""
import struct
import sys
from pathlib import Path

NS = b"http://ns.adobe.com/xap/1.0/\x00"
XMP = ('<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
       '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
       '<rdf:Description rdf:about="" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
       'xmlns:dc="http://purl.org/dc/elements/1.1/" '
       'Iptc4xmpExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia">'
       '<dc:description><rdf:Alt><rdf:li xml:lang="x-default">AI 生成的效果图，不是实物照片 / AI-generated image</rdf:li></rdf:Alt></dc:description>'
       '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>').encode("utf-8")


def tag(p):
    d = p.read_bytes()
    if d[:2] != b"\xff\xd8":
        sys.exit(f"❌ {p.name} 不是 jpg")
    if b"trainedAlgorithmicMedia" in d:
        return "已有"
    i = 2
    # 插在开头的 APP0（JFIF）之后，别的段之前
    while d[i:i + 2] == b"\xff\xe0":
        i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    payload = NS + XMP
    seg = b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload
    p.write_bytes(d[:i] + seg + d[i:])
    return "已写入"


files = sorted(Path(__file__).parent.glob("assets/*.jpg"))
if not files:
    sys.exit("❌ assets/ 里没找到 jpg")
for f in files:
    print(f.name, tag(f))
print(f"共 {len(files)} 张")
