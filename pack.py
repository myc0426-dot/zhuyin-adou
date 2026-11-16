#!/usr/bin/env python3
"""Pack style.css, body.html, paths.js, audio/map.js and app.js into index.html.

Keeps the inlined LessonTC @font-face (stored in font-face.css, or extracted
from the existing index.html if that file is missing).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

HEAD = """<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#1F5A64">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='36' r='22' fill='%237BC96A' stroke='%233E7A32' stroke-width='3'/%3E%3Ccircle cx='26' cy='32' r='3' fill='%2324343C'/%3E%3Ccircle cx='38' cy='32' r='3' fill='%2324343C'/%3E%3Cpath d='M26 42 Q32 48 38 42' fill='none' stroke='%2324343C' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E">
  <title>阿豆的注音課・第 1 課 ㄅㄆㄇ</title>
  <style>
"""


def font_face() -> str:
    ff = ROOT / "font-face.css"
    if ff.exists():
        return ff.read_text(encoding="utf-8")
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    start = idx.index("<style>\n") + len("<style>\n")
    end = idx.index("/* 阿豆的注音課 第 1 課 */")
    text = idx[start:end]
    ff.write_text(text, encoding="utf-8")
    return text


def main() -> None:
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    body = (ROOT / "body.html").read_text(encoding="utf-8")
    paths = (ROOT / "paths.js").read_text(encoding="utf-8")
    audio_map = (ROOT / "audio" / "map.js").read_text(encoding="utf-8")
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    html = (
        HEAD
        + font_face()
        + css
        + "\n  </style>\n</head>\n<body>\n"
        + body
        + "\n<script>\n"
        + paths
        + ("\n" if not paths.endswith("\n") else "")
        + audio_map
        + ("\n" if not audio_map.endswith("\n") else "")
        + app
        + ("\n" if not app.endswith("\n") else "")
        + "</script>\n</body>\n</html>\n"
    )
    dest = ROOT / "index.html"
    dest.write_text(html, encoding="utf-8")
    print(f"wrote {dest} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
