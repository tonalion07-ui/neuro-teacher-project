#!/usr/bin/env python3
"""
vk_token.py
Project:   neuro-teacher-project
Purpose:   Управление access_token / refresh_token VK ID для автопостинга.

Содержит:
    get_access_token() -> str   — возвращает валидный access_token,
                                  автоматически обновляя через refresh_token
                                  если истёк (или близок к истечению).

Использование:
    from vk_token import get_access_token
    token = get_access_token()  # всегда валидный
    # дальше используем token в wall.post и других методах

Файлы .env:
    .env должен содержать VK_REFRESH_TOKEN (долгоживущий).
    VK_ACCESS_TOKEN и VK_TOKEN_EXPIRES_AT будут обновляться автоматически.

Безопасность:
    - refresh_token хранится в .env (как все секреты).
    - access_token обновляется за 5 минут до истечения — чтобы
      публикация не упала из-за «token expired» посреди запроса.
"""
import os
import sys
import time
from pathlib import Path

# Фикс эмодзи в print на Windows-консоли.
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import requests
from dotenv import load_dotenv, set_key

# Загружаем .env и .env.local (с override).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"
load_dotenv(ENV_PATH)
if ENV_LOCAL_PATH.exists():
    load_dotenv(ENV_LOCAL_PATH, override=True)

# Конфигурация.
VK_CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("VK_CLIENT_ID")
VK_APP_SERVICE_KEY = os.getenv("VK_APP_SERVICE_KEY")
TOKEN_URL = "https://id.vk.ru/oauth2/auth"

# За сколько секунд до истечения считать токен «просроченным» и обновлять.
# 5 минут — небольшой запас, чтобы публикация не упала посреди запроса.
REFRESH_MARGIN_SECONDS = 5 * 60


def _check_config():
    """Проверить, что есть всё для обновления токена."""
    missing = []
    if not VK_CLIENT_ID:
        missing.append("CLIENT_ID или VK_CLIENT_ID")
    if not VK_APP_SERVICE_KEY:
        missing.append("VK_APP_SERVICE_KEY")
    if not os.getenv("VK_REFRESH_TOKEN"):
        missing.append("VK_REFRESH_TOKEN")
    if missing:
        raise RuntimeError(
            f"Не хватает переменных в .env: {', '.join(missing)}. "
            "Сначала получи токены через oauth_get_tokens.py"
        )


def _save_tokens(access_token: str, refresh_token: str, expires_in: int):
    """Сохранить новые токены в .env."""
    expires_at = int(time.time()) + int(expires_in)
    set_key(ENV_PATH, "VK_ACCESS_TOKEN", access_token, quote_mode="never")
    set_key(ENV_PATH, "VK_REFRESH_TOKEN", refresh_token, quote_mode="never")
    set_key(ENV_PATH, "VK_TOKEN_EXPIRES_AT", str(expires_at), quote_mode="never")
    return expires_at


def _refresh_via_refresh_token(refresh_token: str) -> dict:
    """POST на id.vk.ru/oauth2/auth с grant_type=refresh_token."""
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": VK_CLIENT_ID,
        # device_id в refresh-grant не требуется по доке VK ID.
        # service_token тоже не нужен для refresh (только для authorization_code).
    }
    response = requests.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(
            f"VK ID вернул ошибку при refresh: {result.get('error')}: "
            f"{result.get('error_description', '(нет описания)')}"
        )
    return result


def _is_token_expired() -> bool:
    """Проверить, истёк ли access_token (или близок к истечению)."""
    expires_at_str = os.getenv("VK_TOKEN_EXPIRES_AT")
    if not expires_at_str:
        return True
    try:
        expires_at = int(expires_at_str)
    except (ValueError, TypeError):
        return True
    now = int(time.time())
    # Если до истечения меньше REFRESH_MARGIN_SECONDS — пора обновлять.
    return now >= (expires_at - REFRESH_MARGIN_SECONDS)


def get_access_token() -> str:
    """
    Вернуть валидный VK access_token. При необходимости обновить через refresh_token.

    Логика:
        1) Если access_token валиден (не истёк) — вернуть как есть.
        2) Если истёк или отсутствует — обменять refresh_token на новую пару.
        3) Сохранить новые токены в .env.
        4) Вернуть новый access_token.

    Raises:
        RuntimeError: если в .env нет VK_REFRESH_TOKEN или VK_ID вернул ошибку.
    """
    _check_config()

    # Случай 1: токен валиден, ничего не делаем.
    if not _is_token_expired():
        token = os.getenv("VK_ACCESS_TOKEN")
        if token:
            return token

    # Случай 2: обновляем через refresh_token.
    print("[vk_token] Access token истёк или отсутствует — обновляю через refresh_token...")
    refresh_token = os.getenv("VK_REFRESH_TOKEN")

    result = _refresh_via_refresh_token(refresh_token)
    access_token = result.get("access_token")
    new_refresh_token = result.get("refresh_token", refresh_token)  # если не вернули — оставляем старый
    expires_in = result.get("expires_in", 3600)

    if not access_token:
        raise RuntimeError(f"VK ID не вернул access_token: {result}")

    expires_at = _save_tokens(access_token, new_refresh_token, expires_in)
    print(f"[vk_token] OK: новый access_token до {time.ctime(expires_at)}")

    return access_token


if __name__ == "__main__":
    # Запуск как самостоятельный скрипт: проверить и обновить токен.
    try:
        token = get_access_token()
        print(f"\n[vk_token] access_token: {token[:25]}... (длина {len(token)})")
    except Exception as e:
        print(f"[vk_token] ОШИБКА: {e}", file=sys.stderr)
        sys.exit(1)
