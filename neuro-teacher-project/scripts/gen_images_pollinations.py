"""
gen_images_pollinations.py
Генерация изображений для постов «Нейроучитель: AI в школе» через Pollinations.ai.
Без API-ключа, без доп. зависимостей (только stdlib).

Запуск:
    python scripts/gen_images_pollinations.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = PROJECT_ROOT / "posts"
META_FILE = POSTS_DIR / "2026-06-23-image-gen.json"

# Модель flux — топовая у Pollinations, без ключа.
MODEL = "flux"
NOLOGO = "true"  # убирает водяной знак Pollinations
SEED_VK = 42
SEED_TG = 73
TIMEOUT_S = 90
MAX_RETRIES = 2

JOBS = [
    {
        "name": "2026-06-23_vk-image.png",
        "width": 1080,
        "height": 1080,
        "seed": SEED_VK,
        "prompt": (
            "Minimalist flat vector illustration, happy teacher sitting at a "
            "desk with a laptop, relaxed expression, wall clock showing 5 PM, "
            "organized papers, warm orange and blue color palette, modern "
            "educational style, no text, no watermark, no letters, no words"
        ),
    },
    {
        "name": "2026-06-23_tg-image.png",
        "width": 1280,
        "height": 720,
        "seed": SEED_TG,
        "prompt": (
            "Flat vector illustration, teacher working with a friendly AI "
            "assistant on a laptop screen, classroom background, blue and "
            "orange color scheme, clean modern style, no text, no watermark, "
            "no letters, no words"
        ),
    },
]


def build_url(prompt: str, width: int, height: int, seed: int) -> str:
    base = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    params = urllib.parse.urlencode(
        {
            "width": width,
            "height": height,
            "model": MODEL,
            "nologo": NOLOGO,
            "seed": seed,
            "enhance": "false",
        }
    )
    return f"{base}?{params}"


def fetch(url: str, dest: Path) -> tuple[bool, str]:
    last_err = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "neuro-teacher-bot/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                if resp.status != 200:
                    last_err = f"HTTP {resp.status}"
                    time.sleep(2 * attempt)
                    continue
                data = resp.read()
                # Pollinations отдаёт JPEG/PNG — определяем по сигнатуре
                if data[:8] == b"\x89PNG\r\n\x1a\n":
                    ext = ".png"
                elif data[:2] == b"\xff\xd8":
                    ext = ".jpg"
                else:
                    ext = ".img"
                if dest.suffix.lower() != ext:
                    dest = dest.with_suffix(ext)
                dest.write_bytes(data)
                return True, f"OK {len(data)} bytes -> {dest.name}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
    return False, last_err


def main() -> int:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for job in JOBS:
        dest = POSTS_DIR / job["name"]
        url = build_url(job["prompt"], job["width"], job["height"], job["seed"])
        print(f"[gen] {job['name']} ({job['width']}x{job['height']})")
        print(f"      url: {url[:120]}...")
        ok, info = fetch(url, dest)
        results.append(
            {
                "name": job["name"],
                "width": job["width"],
                "height": job["height"],
                "seed": job["seed"],
                "ok": ok,
                "info": info,
            }
        )
        print(f"      -> {info}\n")

    META_FILE.write_text(
        json.dumps(
            {
                "model": MODEL,
                "nologo": NOLOGO,
                "jobs": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    failed = [r for r in results if not r["ok"]]
    if failed:
        print(f"[fail] {len(failed)}/{len(results)} картинок не сгенерированы")
        return 1
    print(f"[done] {len(results)}/{len(results)} картинок готово")
    return 0


if __name__ == "__main__":
    sys.exit(main())
