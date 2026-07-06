"""
Публикация постов в ВК-группу «Нейроучитель: AI в школе».

Использование:
    python vk_poster.py <text.md> [image.png]

Шаги:
1. photos.getWallUploadServer — получаем upload_url
2. multipart upload файла на upload_url
3. photos.saveWallPhoto — сохраняем фото в группе (group_id обязателен)
4. wall.post с attachments=photo{owner_id}_{photo_id}

Важно: после успешной отправки — вручную обновить
content/logs/published.md (статус, post_id, ссылка на пост вида
https://vk.com/wall-{group_id}_{post_id}). Без отметки публикация
считается неподтверждённой.

Технические публикации (smoke-test, проверка токена) тоже
фиксируются в журнале — в отдельном блоке «технические тесты»
с префиксом T в номере. Скрытые/удалённые посты помечаются явно.
"""
import os
import sys

# Фикс эмодзи в print на Windows-консоли (cp1251 по умолчанию).
os.environ["PYTHONIOENCODING"] = "utf-8"
# Переконфигурировать stdout уже после того, как интерпретатор инициализирован.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    # Python < 3.7 или консоль не переконфигурируется — хватит переменной окружения.
    pass

from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

# Приоритет токенов:
#   VK_USER_ACCESS_TOKEN — пользовательский токен администратора группы.
#                          Нужен для wall.get, photos.getWallUploadServer,
#                          wall.post с attachments от имени сообщества.
#   VK_ACCESS_TOKEN      — fallback. Сервисный токен приложения.
#                          Ограничен: не пускает wall.get и upload фото.
ACCESS_TOKEN = os.getenv("VK_USER_ACCESS_TOKEN") or os.getenv("VK_ACCESS_TOKEN")
TOKEN_KIND = "user" if os.getenv("VK_USER_ACCESS_TOKEN") else "service"
GROUP_ID = os.getenv("VK_GROUP_ID")
API_VERSION = "5.199"

BASE_URL = "https://api.vk.com/method"


def _vk_call(method: str, params: dict) -> dict:
    """POST к VK API. Параметры уходят как form-data."""
    params = {**params, "access_token": ACCESS_TOKEN, "v": API_VERSION}
    response = requests.post(f"{BASE_URL}/{method}", data=params)
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(f"VK API error in {method}: {result['error']}")
    return result["response"]


def warn_if_service_token():
    """Сервисный токен не пускает wall.get и upload. Предупреждаем заранее."""
    if TOKEN_KIND == "service":
        print("[WARN] Используется сервисный токен. Методы wall.get, "
              "photos.getWallUploadServer будут недоступны.")
        print("[WARN] Чтобы публиковать с картинкой, положи VK_USER_ACCESS_TOKEN в .env")


def upload_photo(image_path: str) -> dict:
    """Шаг 1+2: получить upload_url и загрузить файл. Возвращает {server, photo, hash}."""
    upload_url = _vk_call(
        "photos.getWallUploadServer",
        {"group_id": GROUP_ID},
    )["upload_url"]

    with open(image_path, "rb") as f:
        # VK upload ожидает multipart с полем photo. Никаких заголовков не надо.
        upload_response = requests.post(upload_url, files={"photo": f}).json()

    if "error" in upload_response:
        raise RuntimeError(f"Upload error: {upload_response['error']}")

    return upload_response  # {server, photo, hash}


def save_wall_photo(server: str, photo: str, hash: str) -> dict:
    """Шаг 3: сохранить фото в группе. Возвращает {id, owner_id, ...}."""
    saved = _vk_call(
        "photos.saveWallPhoto",
        {
            "group_id": GROUP_ID,
            "server": server,
            "photo": photo,
            "hash": hash,
        },
    )
    return saved[0]  # VK возвращает массив из одного элемента


def publish_post(message: str, image_path: str | None = None) -> dict:
    """Шаг 4: публикация на стене группы. Возвращает {post_id, url}."""
    warn_if_service_token()
    attachments = None
    if image_path:
        uploaded = upload_photo(image_path)
        saved = save_wall_photo(**uploaded)
        attachments = f"photo{saved['owner_id']}_{saved['id']}"
        print(f"[OK] Фото загружено: {attachments}")

    params = {
        "owner_id": f"-{GROUP_ID}",
        "message": message,
        "from_group": 1,
    }
    if attachments:
        params["attachments"] = attachments

    result = _vk_call("wall.post", params)
    post_id = result["post_id"]
    owner_id = f"-{GROUP_ID}"
    url = f"https://vk.com/wall{owner_id}_{post_id}"
    print(f"[OK] Пост опубликован! ID: {post_id}")
    print(f"[OK] Ссылка: {url}")
    return {"post_id": post_id, "url": url}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python vk_poster.py <text.md> [image.png]")
        sys.exit(1)

    text_path = Path(sys.argv[1])
    image_path = sys.argv[2] if len(sys.argv) > 2 else None

    if not text_path.exists():
        print(f"[ERR] Файл не найден: {text_path}")
        sys.exit(1)

    message = text_path.read_text(encoding="utf-8")
    publish_post(message, image_path)
