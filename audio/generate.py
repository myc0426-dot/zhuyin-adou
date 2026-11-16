#!/usr/bin/env python3
"""Generate HsiaoChen MP3s for 阿豆的注音課.

Usage (from repo root or this folder):
    python3 audio/generate.py

Requires: edge-tts  (pip install edge-tts)

Voice is fixed to zh-TW-HsiaoChenNeural at rate -10% and pitch +5Hz,
matching the parent-approved sample. Isolated 注音符號 are the
symbols themselves (ㄅ, ㄆ, ㄇ) — never 玻 / 坡 / 摸 substitutes.
In sentences, write the symbol directly, e.g. 「這是ㄅ，爸爸的ㄅ」.

This file is the source of truth for spoken lines. It also writes
audio/manifest.json and audio/map.js so the lesson page can look up
each exact string. Add new tuples to LINES when making later lessons.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

try:
    import edge_tts
except ImportError:
    sys.stderr.write("Please install edge-tts:  pip install edge-tts\n")
    raise SystemExit(1)

VOICE = "zh-TW-HsiaoChenNeural"
RATE = "-10%"
PITCH = "+5Hz"

ROOT = Path(__file__).resolve().parent
OUT = ROOT  # mp3s live next to this script

# (id, text) — id becomes {id}.mp3 and must stay ASCII / URL-safe.
LINES: list[tuple[str, str]] = [
    # --- Lesson 1 pages ---
    ("welcome", "嗨，阿豆！準備好了嗎？今天是第一課，我們要認識ㄅ、ㄆ、ㄇ。先來玩暖身遊戲，讓耳朵打開。"),
    ("listen_intro", "暖身遊戲：聽了再動。阿豆要先把話聽完，聽到開始，再做動作。"),
    ("wood_intro", "接下來玩一二三木頭人。阿豆會走動，聽到木頭人就要站住。"),
    ("learn_b", "先來認識ㄅ。這是ㄅ，包子的ㄅ，爸爸的ㄅ。"),
    ("learn_p", "再來認識ㄆ。這是ㄆ，拍球的ㄆ，蘋果的ㄆ。"),
    ("learn_m", "最後是ㄇ。這是ㄇ，門的ㄇ，媽媽的ㄇ。"),
    ("learn_all", "阿豆，三個符號都在這裡。點一點，再聽一次。"),
    ("break_intro", "阿豆站起來動一動！跟著跳三下，轉一圈，然後坐好。"),
    ("quiz_intro", "現在來玩聽一聽、選一選。仔細聽，再點出正確的注音。"),
    ("stroke_intro", "來看筆順。先看怎麼寫，再用手指或滑鼠，沿著淡淡的字描一描。"),
    ("end", "阿豆好棒！今天我們認識了ㄅ、ㄆ、ㄇ。記得跟爸爸一起寫作業單喔。"),

    # Isolated 注音表 sounds — symbols only
    ("iso_b", "ㄅ"),
    ("iso_p", "ㄆ"),
    ("iso_m", "ㄇ"),

    # Symbol cards (click the big glyph / grid)
    ("say_b", "這是ㄅ，包子的ㄅ，爸爸的ㄅ。"),
    ("say_p", "這是ㄆ，拍球的ㄆ，蘋果的ㄆ。"),
    ("say_m", "這是ㄇ，門的ㄇ，媽媽的ㄇ。"),

    # Example words
    ("ex_baozi", "包子。包子的ㄅ。"),
    ("ex_baba", "爸爸。爸爸的ㄅ。"),
    ("ex_beizi", "杯子。杯子的ㄅ。"),
    ("ex_paiqiu", "拍球。拍球的ㄆ。"),
    ("ex_pingguo", "蘋果。蘋果的ㄆ。"),
    ("ex_paopao", "泡泡。泡泡的ㄆ。"),
    ("ex_men", "門。門的ㄇ。"),
    ("ex_mama", "媽媽。媽媽的ㄇ。"),
    ("ex_maozi", "帽子。帽子的ㄇ。"),

    # 聽了再動
    ("listen_clap", "阿豆，先聽完再動。請拍拍手。開始！"),
    ("listen_head", "阿豆，先聽完再動。請摸摸頭。開始！"),
    ("listen_hands", "阿豆，先聽完再動。請舉舉手。開始！"),
    ("listen_press_start", "先按開始這一題，聽完再做喔。"),
    ("listen_not_yet", "還沒說完喔，阿豆再聽一次。"),
    ("listen_great", "太專心了！阿豆的耳朵有在聽。"),
    ("listen_next", "很好，再來一題。"),

    # 木頭人
    ("wood_3", "3"),
    ("wood_2", "2"),
    ("wood_1", "1"),
    ("wood_freeze", "木頭人！"),
    ("wood_early", "還沒說木頭人喔，再等一等。"),
    ("wood_good", "阿豆站住了，真專心！"),
    ("wood_again", "很棒，再玩一次。"),

    # 動一動
    ("break_jump", "跳三下！"),
    ("break_spin", "轉一圈！"),
    ("break_sit", "很好，慢慢坐好。"),
    ("break_timeup", "時間到了，阿豆坐好，準備下一關！"),
    ("break_done", "坐好了，真乖。"),

    # 聽音辨識 prompts
    ("quiz_b", "ㄅ，爸爸的ㄅ。"),
    ("quiz_baozi", "包子。是哪一個音開頭呢？"),
    ("quiz_beizi", "杯子。是哪一個音開頭呢？"),
    ("quiz_p", "ㄆ，拍球的ㄆ。"),
    ("quiz_pingguo", "蘋果。是哪一個音開頭呢？"),
    ("quiz_paopao", "泡泡。是哪一個音開頭呢？"),
    ("quiz_m", "ㄇ，媽媽的ㄇ。"),
    ("quiz_maozi", "帽子。是哪一個音開頭呢？"),
    ("quiz_men", "門。是哪一個音開頭呢？"),
    ("quiz_correct", "答對了！阿豆真厲害！"),
    ("quiz_all_done", "都完成了，阿豆好棒！可以看筆順了。"),

    # Retry + replay of the same prompt (exact concatenation used by the page)
    ("quiz_retry_b", "再聽一次，沒關係。ㄅ，爸爸的ㄅ。"),
    ("quiz_retry_baozi", "再聽一次，沒關係。包子。是哪一個音開頭呢？"),
    ("quiz_retry_beizi", "再聽一次，沒關係。杯子。是哪一個音開頭呢？"),
    ("quiz_retry_p", "再聽一次，沒關係。ㄆ，拍球的ㄆ。"),
    ("quiz_retry_pingguo", "再聽一次，沒關係。蘋果。是哪一個音開頭呢？"),
    ("quiz_retry_paopao", "再聽一次，沒關係。泡泡。是哪一個音開頭呢？"),
    ("quiz_retry_m", "再聽一次，沒關係。ㄇ，媽媽的ㄇ。"),
    ("quiz_retry_maozi", "再聽一次，沒關係。帽子。是哪一個音開頭呢？"),
    ("quiz_retry_men", "再聽一次，沒關係。門。是哪一個音開頭呢？"),

    # 筆順
    ("stroke_b", "來看 ㄅ 的筆順。從左上的短斜線起筆，帶到轉角，向右寫橫，再轉折向下彎，最後向左鉤。一筆完成。"),
    ("stroke_p", "來看 ㄆ 的筆順。第 1 筆：從左上起筆，帶到轉角後向右寫橫，再向左下長長地撇下去。"),
    ("stroke_m", "來看 ㄇ 的筆順。第 1 筆：先寫左邊的一豎，由上往下。"),
    ("trace_b", "寫好了，阿豆真棒！ㄅ是 1 畫。"),
    ("trace_p", "寫好了，阿豆真棒！ㄆ是 2 畫。"),
    ("trace_m", "寫好了，阿豆真棒！ㄇ是 2 畫。"),

    # 瑪奇瑪 / 波奇塔
    ("welcome_friends", "嗨，阿豆！準備好了嗎？今天是第一課，我們要認識ㄅ、ㄆ、ㄇ。瑪奇瑪老師和波奇塔也來陪你。先來玩暖身遊戲，讓耳朵打開。"),
    ("listen_intro_makima", "暖身遊戲：聽了再動。瑪奇瑪老師會出示注音，阿豆要先把話聽完，聽到開始，再做動作。"),
    ("listen_b_clap", "阿豆，聽到ㄅ就拍手。開始！"),
    ("listen_p_head", "阿豆，聽到ㄆ就摸摸頭。開始！"),
    ("listen_m_hands", "阿豆，聽到ㄇ就舉舉手。開始！"),
    ("lulu", "嚕嚕嚕！"),
    ("break_intro_friends", "阿豆、波奇塔，站起來動一動！跟著跳三下，轉一圈，然後坐好。"),
    ("quiz_intro_makima", "現在瑪奇瑪老師要出題了。仔細聽，再點出正確的注音。"),
    ("end_friends", "阿豆好棒！波奇塔也很高興。今天我們認識了ㄅ、ㄆ、ㄇ。記得跟爸爸一起寫作業單喔。"),
]


def write_manifest() -> dict[str, str]:
    mapping = {text: f"audio/{lid}.mp3" for lid, text in LINES}
    by_id = {lid: {"file": f"audio/{lid}.mp3", "text": text} for lid, text in LINES}
    manifest = {
        "voice": VOICE,
        "rate": RATE,
        "pitch": PITCH,
        "byId": by_id,
        "byText": mapping,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # JS lookup used by the lesson page (inlined by pack.py)
    js_obj = json.dumps(mapping, ensure_ascii=False, indent=2)
    (OUT / "map.js").write_text(
        "/* generated by audio/generate.py — do not edit by hand */\n"
        "window.ZHUYIN_AUDIO_MAP = " + js_obj + ";\n",
        encoding="utf-8",
    )
    # sanity: unique ids and unique texts
    ids = [lid for lid, _ in LINES]
    texts = [t for _, t in LINES]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate line ids")
    if len(texts) != len(set(texts)):
        raise SystemExit("duplicate line texts")
    return mapping


async def synth(text: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(dest))
    if not dest.exists() or dest.stat().st_size < 100:
        size = dest.stat().st_size if dest.exists() else 0
        raise RuntimeError(f"empty or tiny output: {dest} ({size} bytes)")
    print(f"OK  {dest.name:24s}  {dest.stat().st_size:6d} B  {text!r}", flush=True)


async def main() -> int:
    write_manifest()
    errors: list[str] = []
    # modest concurrency so the service is not flooded
    sem = asyncio.Semaphore(4)

    async def one(lid: str, text: str) -> None:
        dest = OUT / f"{lid}.mp3"
        async with sem:
            try:
                await synth(text, dest)
            except Exception as e:
                errors.append(f"{lid}: {e!r}")
                print(f"FAIL {lid}: {e!r}", flush=True)

    await asyncio.gather(*(one(lid, text) for lid, text in LINES))
    if errors:
        print("\nSOME FAILURES:", file=sys.stderr)
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    print(f"\nAll {len(LINES)} segments generated into {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
