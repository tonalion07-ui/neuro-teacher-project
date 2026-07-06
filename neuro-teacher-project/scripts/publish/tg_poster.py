"""
Публикация постов в Telegram-канал @neuro_uchitel.

Использование:
    python tg_poster.py <text.md> [image.png]

Токен бота и chat_id берутся из .env:
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=@neuro_uchitel

Шаги:
1. Если передана картинка — отправляем фото с подписью через sendPhoto.
2. Если без картинки — отправляем текст через sendMessage.

Важно: после успешной отправки — вручную обновить
content/logs/published.md (статус, message_id, ссылка).
Без отметки публикация считается неподтверждённой.

Технические публикации (smoke-test, проверка токена) тоже
фиксируются в журнале — в отдельном блоке «технические тесты»
с префиксом T в номере. Скрытые/удалённые посты помечаются явно.
"""
import os
import sys

# Фикс эмодзи в print на Windows-консоли.
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Лимит Telegram на длину подписи к фото (sendPhoto).
MAX_CAPTION = 1024


def send_message(text: str) -> dict:
    """Отправка plain-текста в канал."""
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Нет TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID в .env")

    response = requests.post(
        f"{API_BASE}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": text,
            "disable_web_page_preview": True,
        },
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def send_photo(image_path: str, caption: str) -> dict:
    """Отправка фото с подписью."""
    if not BOT_TOKEN or not CHAT_ID:
        raise RuntimeError("Нет TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID в .env")
    if len(caption) > MAX_CAPTION:
        raise ValueError(
            f"Подпись слишком длинная: {len(caption)} символов "
            f"(лимит Telegram: {MAX_CAPTION})"
        )

    with open(image_path, "rb") as f:
        # Подпись отправляем plain text: наш канал @neuro_uchitel содержит
        # символ '_', который Telegram Markdown-парсер считает началом
        # курсива, что ломает всю подпись. Жирный/курсив в подписи не
        # используется, эмодзи рендерятся и без parse_mode.
        response = requests.post(
            f"{API_BASE}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "caption": caption,
            },
            files={"photo": f},
        )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data["result"]


def publish_post(text_path: str, image_path: str | None = None) -> dict:
    """Читает .md файл и публикует.

    Из содержимого .md вырезается служебная шапка: всё, что идёт ДО
    первого разделителя `---` (строка из трёх дефисов), и всё, что
    идёт ПОСЛЕ второго. В Telegram уходит только тело поста — между
    двумя `---`. Пустые строки вокруг `---` игнорируются. Это нужно,
    чтобы в лимит подписи к фото (1024) не упирались YAML-блоки и
    черновые заметки.
    """
    raw = Path(text_path).read_text(encoding="utf-8")

    # Ищем индексы строк, состоящих ровно из "---" (с поправкой на
    # висячие пробелы). Берём содержимое между первым и вторым.
    lines = raw.split("\n")
    separators = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if len(separators) >= 2:
        body = "\n".join(lines[separators[0] + 1: separators[1]])
    else:
        body = raw

    # Внутри тела поста черновика часто стоит служебный заголовок
    # `## Тело поста` — в Telegram-канал он не нужен. Вырезаем ровно
    # одну такую строку (если встречается в начале тела, после пустых
    # строк). Заголовок `## Статус` уже отрезан вторым `---`.
    body_lines = body.split("\n")
    cleaned: list[str] = []
    skipped_body_header = False
    for line in body_lines:
        if not skipped_body_header and line.strip() == "## Тело поста":
            skipped_body_header = True
            continue
        cleaned.append(line)
    text = "\n".join(cleaned).strip()

    if image_path:
        result = send_photo(image_path, text)
        msg_id = result["message_id"]
        print(f"[OK] Фото+текст отправлены в Telegram. message_id: {msg_id}")
    else:
        result = send_message(text)
        msg_id = result["message_id"]
        print(f"[OK] Текст отправлен в Telegram. message_id: {msg_id}")

    if isinstance(CHAT_ID, str) and CHAT_ID.startswith("@"):
        username = CHAT_ID.lstrip("@")
        url = f"https://t.me/{username}/{msg_id}"
        print(f"[OK] Ссылка: {url}")
        return {"message_id": msg_id, "url": url}

    return {"message_id": msg_id}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python tg_poster.py <text.md> [image.png]")
        sys.exit(1)

    text_path = sys.argv[1]
    image_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(text_path).exists():
        print(f"[ERR] Файл не найден: {text_path}")
        sys.exit(1)
    if image_path and not Path(image_path).exists():
        print(f"[ERR] Файл не найден: {image_path}")
        sys.exit(1)

    publish_post(text_path, image_path)