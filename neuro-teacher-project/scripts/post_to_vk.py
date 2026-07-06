"""
Публикация поста в сообщество ВКонтакте.

Пайплайн:
  1) photos.getWallUploadServer(group_id) -> upload_url
  2) multipart POST картинки на upload_url -> {server, photo, hash}
  3) photos.saveWallPhoto(group_id, photo, server, hash) -> {id, owner_id}
  4) wall.post(owner_id=-group_id, from_group=1, message, attachments=f"{owner_id}_{id}")

DRY-RUN: флаг --dry-run пропускает шаг 4 (wall.post) и не публикует.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import dotenv_values


API_BASE = "https://api.vk.com/method"
API_VERSION = "5.199"


def _env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def load_config() -> dict:
    env_file = _env_path()
    if not env_file.exists():
        sys.exit(f"[FATAL] .env не найден: {env_file}")
    cfg = dotenv_values(env_file)
    token = cfg.get("VK_ACCESS_TOKEN", "").strip()
    group_id = cfg.get("VK_GROUP_ID", "").strip()
    if not token:
        sys.exit("[FATAL] VK_ACCESS_TOKEN пуст в .env")
    if not group_id.lstrip("-").isdigit():
        sys.exit("[FATAL] VK_GROUP_ID в .env не похож на число")
    return {
        "token": token,
        "group_id": int(group_id),
        "api_version": API_VERSION,
    }


def api_call(method: str, params: dict, *, timeout: int = 30) -> dict:
    """Один вызов VK API. Бросает RuntimeError при ошибке."""
    params = {**params, "access_token": params.get("access_token", ""), "v": API_VERSION}
    # access_token не дублируем, если передан
    url = f"{API_BASE}/{method}"
    resp = requests.post(url, data=params, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"VK API error in {method}: {data['error']}")
    return data.get("response", data)


def step_get_upload_server(token: str, group_id: int) -> str:
    print(f"[1/4] photos.getWallUploadServer group_id={group_id}")
    data = api_call(
        "photos.getWallUploadServer",
        {"access_token": token, "group_id": group_id},
    )
    upload_url = data.get("upload_url")
    if not upload_url:
        sys.exit(f"[FATAL] нет upload_url в ответе: {data}")
    print(f"      upload_url получен ({len(upload_url)} chars)")
    return upload_url


def step_upload_photo(upload_url: str, image_path: Path) -> dict:
    print(f"[2/4] POST картинки на upload_url: {image_path.name} ({image_path.stat().st_size} bytes)")
    with image_path.open("rb") as f:
        files = {"photo": (image_path.name, f, "image/png")}
        resp = requests.post(upload_url, files=files, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if not {"server", "photo", "hash"}.issubset(data):
        sys.exit(f"[FATAL] неожиданный ответ upload: {data}")
    print(f"      server={data['server']}, hash={data['hash'][:8]}..., photo=<{len(data['photo'])} chars>")
    return data


def step_save_wall_photo(token: str, group_id: int, uploaded: dict) -> dict:
    print(f"[3/4] photos.saveWallPhoto group_id={group_id}")
    data = api_call(
        "photos.saveWallPhoto",
        {
            "access_token": token,
            "group_id": group_id,
            "photo": uploaded["photo"],
            "server": uploaded["server"],
            "hash": uploaded["hash"],
        },
    )
    if not isinstance(data, list) or not data or "id" not in data[0]:
        sys.exit(f"[FATAL] неожиданный ответ saveWallPhoto: {data}")
    saved = data[0]
    print(f"      saved id={saved['id']}, owner_id={saved['owner_id']}")
    return saved


def step_wall_post(token: str, group_id: int, message: str, attachment: str) -> dict:
    print(f"[4/4] wall.post owner_id=-{group_id}, attachment={attachment}")
    data = api_call(
        "wall.post",
        {
            "access_token": token,
            "owner_id": -abs(group_id),
            "from_group": 1,
            "message": message,
            "attachments": attachment,
        },
    )
    print(f"      post_id={data.get('post_id')}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description="Публикация поста в VK сообщество")
    parser.add_argument("--content", required=True, type=Path, help="JSON с контентом (platforms.vk)")
    parser.add_argument("--image", required=True, type=Path, help="путь к картинке")
    parser.add_argument(
        "--group-id",
        type=int,
        default=None,
        help="переопределить VK_GROUP_ID из .env (например, 1075782587)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="пропустить wall.post (всё загрузить, но не публиковать)",
    )
    parser.add_argument(
        "--response-out",
        type=Path,
        default=None,
        help="куда записать ответ wall.post (по умолчанию tmp/vk-post-YYYY-MM-DD-response.json)",
    )
    args = parser.parse_args()

    cfg = load_config()
    group_id = args.group_id if args.group_id is not None else cfg["group_id"]
    if group_id <= 0:
        sys.exit("[FATAL] group_id должен быть положительным числом (сообщество)")
    cfg["group_id"] = group_id

    print(f"Config: group_id={cfg['group_id']}, api v={cfg['api_version']}")
    print(f"Dry-run: {args.dry_run}")
    print()

    content = json.loads(args.content.read_text(encoding="utf-8"))
    message = content["platforms"]["vk"]
    if not message.strip():
        sys.exit("[FATAL] platforms.vk в JSON пуст")

    image_path = args.image
    if not image_path.exists():
        sys.exit(f"[FATAL] картинка не найдена: {image_path}")

    token = cfg["token"]
    upload_url = step_get_upload_server(token, cfg["group_id"])
    uploaded = step_upload_photo(upload_url, image_path)
    saved = step_save_wall_photo(token, cfg["group_id"], uploaded)

    attachment = f"{saved['owner_id']}_{saved['id']}"
    print()
    print(f"Готово к публикации. Attachment: {attachment}")
    print(f"Длина текста: {len(message)} символов")

    if args.dry_run:
        print("\n[DRY-RUN] wall.post пропущен. Пост НЕ опубликован.")
        return

    print()
    result = step_wall_post(token, cfg["group_id"], message, attachment)

    out = args.response_out
    if out is None:
        today = __import__("datetime").date.today().isoformat()
        out = Path(__file__).resolve().parent.parent / "tmp" / f"vk-post-{today}-response.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "group_id": cfg["group_id"],
                "attachment": attachment,
                "post_id": result.get("post_id"),
                "raw": result,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nОтвет wall.post записан: {out}")
    print(f"Пост опубликован: post_id={result.get('post_id')}")


if __name__ == "__main__":
    main()
