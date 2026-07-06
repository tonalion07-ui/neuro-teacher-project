#!/usr/bin/env python3
"""
oauth_get_tokens.py
Project:   neuro-teacher-project
Purpose:   Одноразовое получение VK USER access_token + refresh_token
           через OAuth 2.1 Authorization Code + PKCE flow.

Поток:
    1. Сгенерировать code_verifier, code_challenge, state, device_id
    2. Вывести URL для браузера
    3. Пользователь открывает URL, разрешает доступ
    4. VK ID редиректит на redirect_uri?code=...&state=...&device_id=...
    5. Пользователь копирует code из URL и вставляет в stdin
    6. Скрипт обменивает code на токены через id.vk.ru/oauth2/auth
    7. Сохраняет токены в .env (VK_ACCESS_TOKEN, VK_REFRESH_TOKEN, expires_at)

Использование:
    python scripts/publish/oauth_get_tokens.py

После успешного выполнения можно удалить или оставить как утилиту для
повторного получения токенов.
"""
import base64
import hashlib
import os
import secrets
import sys
import time
import uuid
from pathlib import Path

# Фикс эмодзи в print на Windows-консоли (cp1251 по умолчанию).
os.environ["PYTHONIOENCODING"] = "utf-8"
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import requests
from dotenv import load_dotenv, set_key, dotenv_values

# Загружаем оба env-файла: .env (основной) и .env.local (локальный, поверх).
# python-dotenv по умолчанию читает только .env, поэтому грузим .env.local явно.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
ENV_LOCAL_PATH = PROJECT_ROOT / ".env.local"
load_dotenv(ENV_PATH)
if ENV_LOCAL_PATH.exists():
    load_dotenv(ENV_LOCAL_PATH, override=True)

# --- Конфигурация из .env ---
VK_CLIENT_ID = os.getenv("CLIENT_ID") or os.getenv("VK_CLIENT_ID")
VK_APP_SERVICE_KEY = os.getenv("VK_APP_SERVICE_KEY")
VK_REDIRECT_URI = os.getenv("VK_REDIRECT_URI")

# IP пользователя, с которого будет сделан /authorize.
# Нужен для token-exchange (ВК привязывает token к IP авторизации).
# Если token-exchange идёт с того же IP — можно не указывать.
# Если с другого (например, с нашего backend) — укажи явно.
VK_AUTHORIZE_IP = os.getenv("VK_AUTHORIZE_IP")

# Scope: все нужные права. Зависит от того, какие галочки включены
# в кабинете VK ID для приложения 54646486.
SCOPE = "vkid.personal_info wall photos groups"

# Endpoints
AUTH_URL = "https://id.vk.ru/authorize"
TOKEN_URL = "https://id.vk.ru/oauth2/auth"


def _check_config():
    """Проверить, что все нужные переменные окружения заданы."""
    missing = []
    if not VK_CLIENT_ID:
        missing.append("CLIENT_ID или VK_CLIENT_ID")
    if not VK_APP_SERVICE_KEY:
        missing.append("VK_APP_SERVICE_KEY")
    if not VK_REDIRECT_URI:
        missing.append("VK_REDIRECT_URI")
    if missing:
        print("[ERR] В .env не хватает переменных:")
        for m in missing:
            print(f"       - {m}")
        sys.exit(1)


def _b64url(data: bytes) -> str:
    """Base64 URL-safe без padding (требование PKCE RFC 7636)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _generate_pkce() -> tuple[str, str]:
    """Сгенерировать code_verifier и code_challenge (S256).

    Используем 64 байта (86 chars base64url) — как в vk-init.js
    нашего backend. ВК, по наблюдениям, принимает оба размера (43 и 86),
    но чтобы исключить любые сюрпризы, держимся формата, который
    уже работает в проекте.
    """
    # 64 байта -> 86 символов base64url. Попадает в диапазон 43-128.
    verifier_bytes = secrets.token_bytes(64)
    verifier = _b64url(verifier_bytes)

    # challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def _generate_device_id() -> str:
    """
    Сгенерировать device_id в формате, который принимает VK ID.

    Формат: base64url(16 random bytes) без padding -> 22 символа.
    Пример: '341b4b93-542e-4f46-aa6f-4589e584c660' (визуально похож на UUID,
    но это base64url от 16 случайных байт).

    VK ID НЕ принимает UUID v4 (32 hex-символа с дефисами) — нужен именно
    такой формат. Источник: vk-init.js из neuro-teacher-pro/api/auth/.
    """
    return _b64url(secrets.token_bytes(16))


def _build_auth_url(state: str, code_challenge: str, device_id: str) -> str:
    """Собрать URL для https://id.vk.ru/authorize."""
    from urllib.parse import urlencode

    params = {
        "response_type": "code",
        "client_id": VK_CLIENT_ID,
        "redirect_uri": VK_REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": SCOPE,
        "device_id": device_id,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _prompt_code_and_device_id() -> tuple[str, str]:
    """
    Прочитать URL редиректа от пользователя, извлечь code + device_id.

    device_id из redirect (86 chars base64url в code_v2) — именно его
    ждёт VK в token-exchange. Проверено 04.07.2026: при отправке нашего
    собственного device_id ВК возвращает 'device_id is invalid'.

    Источник: тест oauth_get_tokens.py (см. сессию 04.07).
    """
    print()
    print("[*] После того как ты разрешил доступ, браузер редиректнул")
    print("    на https://www.neuro-teacher.pro/api/auth/vk-callback?code=...&state=...&device_id=...&type=code_v2")
    print("    Скопируй ВЕСЬ URL из адресной строки и вставь сюда.")
    print()
    raw = input(">>> URL: ").strip()
    if not raw:
        print("[ERR] Пустой ввод.")
        sys.exit(1)

    if "code=" not in raw:
        print("[ERR] Нужен ПОЛНЫЙ URL из адресной строки (там есть code и device_id).")
        sys.exit(1)

    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(raw)
    qs = parse_qs(parsed.query)
    codes = qs.get("code", [])
    devices = qs.get("device_id", [])

    if not codes:
        print("[ERR] В URL нет параметра code.")
        sys.exit(1)
    if not devices:
        print("[ERR] В URL нет параметра device_id (ВК должен его подставить).")
        sys.exit(1)

    return codes[0], devices[0]


def _exchange_code(code: str, code_verifier: str, state: str, device_id: str, ip: str = None) -> dict:
    """POST на id.vk.ru/oauth2/auth для обмена code на токены.

    Схема (текущая):
        - service_token в body (как в нашем backend vk-callback.js)
        - code_verifier в body (PKCE обязателен; ВК проверяет SHA256(code_verifier) == code_challenge)
        - device_id — из РЕДИРЕКТА (code_v2: ВК перезаписывает на свой 64-байтный)
        - ip — IP авторизации, должен быть в whitelist "IP-адрес сервера"
        - БЕЗ Basic Auth (используем service_token для аутентификации)

    Источник: `neuro-teacher-pro/api/auth/vk-callback.js` (lines 126-141) +
    RFC 7636 (PKCE обязателен для OAuth 2.1).
    """
    payload = {
        "grant_type": "authorization_code",
        "code_verifier": code_verifier,
        "redirect_uri": VK_REDIRECT_URI,
        "code": code,
        "client_id": VK_CLIENT_ID,
        "device_id": device_id,
        "state": state,
        "service_token": VK_APP_SERVICE_KEY,
    }
    if ip:
        payload["ip"] = ip
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
            f"VK ID вернул ошибку: {result.get('error')}: "
            f"{result.get('error_description', '(нет описания)')}"
        )
    return result


def _save_tokens(access_token: str, refresh_token: str, expires_in: int):
    """Сохранить токены в .env, не затирая остальные переменные."""
    expires_at = int(time.time()) + int(expires_in)

    set_key(ENV_PATH, "VK_ACCESS_TOKEN", access_token, quote_mode="never")
    set_key(ENV_PATH, "VK_REFRESH_TOKEN", refresh_token, quote_mode="never")
    set_key(ENV_PATH, "VK_TOKEN_EXPIRES_AT", str(expires_at), quote_mode="never")

    print()
    print(f"[OK] Токены сохранены в {ENV_PATH}")
    print(f"     VK_ACCESS_TOKEN     = {access_token[:25]}... (expires in {expires_in}s)")
    print(f"     VK_REFRESH_TOKEN    = {refresh_token[:25]}...")
    print(f"     VK_TOKEN_EXPIRES_AT = {expires_at} ({time.ctime(expires_at)})")


def main():
    _check_config()

    print("=" * 70)
    print("VK ID OAuth 2.1 + PKCE — получение access_token + refresh_token")
    print("=" * 70)
    print(f"client_id     = {VK_CLIENT_ID}")
    print(f"redirect_uri  = {VK_REDIRECT_URI}")
    print(f"scope         = {SCOPE}")
    print()

    # 1) Генерируем PKCE + state + device_id
    code_verifier, code_challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)
    device_id = _generate_device_id()

    # 2) Строим URL и выводим
    auth_url = _build_auth_url(state, code_challenge, device_id)
    print("[1] Открой этот URL в браузере (залогиненным как владелец группы 239683607):")
    print()
    print(f"    {auth_url}")
    print()
    print("    Разреши приложению доступ. После этого браузер редиректнёт")
    print("    на адрес с ?code=...&state=...&device_id=... Скопируй URL.")
    print()

    # 3) Ждём code + device_id из URL редиректа.
    # В code_v2 ВК подменяет device_id на свой 64-байтный — именно его
    # ждёт ВК в token-exchange (проверено: 22-char наш → 'device_id is invalid').
    code, redirect_device_id = _prompt_code_and_device_id()
    print(f"[*] code = {code[:30]}...")
    print(f"[*] device_id (из редиректа) = {redirect_device_id[:30]}... (длина {len(redirect_device_id)})")

    # 4) Обмениваем code на токены.
    # Схема: service_token в body, наш code_verifier, device_id из redirect.
    print()
    print("[2] Обмениваю code на токены...")
    if VK_AUTHORIZE_IP:
        print(f"[*] ip (из .env VK_AUTHORIZE_IP) = {VK_AUTHORIZE_IP}")
    try:
        result = _exchange_code(
            code, code_verifier, state, redirect_device_id, ip=VK_AUTHORIZE_IP
        )
    except Exception as e:
        print(f"[ERR] {e}")
        sys.exit(1)

    access_token = result.get("access_token")
    refresh_token = result.get("refresh_token")
    expires_in = result.get("expires_in", 3600)
    user_id = result.get("user_id")

    if not access_token or not refresh_token:
        print(f"[ERR] В ответе нет access_token или refresh_token: {result}")
        sys.exit(1)

    print(f"[OK] Получен user_id={user_id}, expires_in={expires_in}s")
    print()
    print("[3] Тестирую токен через wall.get...")

    # 5) Безопасная проверка через wall.get
    test = requests.post(
        "https://api.vk.com/method/wall.get",
        data={
            "owner_id": f"-{os.getenv('VK_GROUP_ID', '239683607')}",
            "count": 1,
            "access_token": access_token,
            "v": "5.199",
        },
        timeout=15,
    )
    test_result = test.json()
    if "error" in test_result:
        err = test_result["error"]
        print(f"[WARN] wall.get вернул ошибку: {err['error_code']} {err['error_msg']}")
        print("       Но токены получены и сохранены. Возможно, нужно проверить scope.")
    else:
        cnt = test_result["response"]["count"]
        print(f"[OK] wall.get: в группе {cnt} постов. Токен рабочий.")

    # 6) Сохраняем
    _save_tokens(access_token, refresh_token, expires_in)
    print()
    print("Готово. Теперь vk_poster.py может пользоваться этим токеном.")


if __name__ == "__main__":
    main()
