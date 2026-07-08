#!/usr/bin/env python3
import os
import sys
import asyncio
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

REQUIRED = [
    ("BOT_TOKEN", "Токен Telegram-бота — получите у @BotFather"),
    ("LOLZTEAM_TOKEN", "Токен LZT Market API — lzt.market → Settings → API"),
]
DEFAULTS = [
    ("API_BASE_URL", "https://prod-api.lzt.market"),
]


def ensure_dependencies():
    try:
        import aiogram, aiohttp, pydantic, dotenv
        return
    except ImportError:
        pass
    print("📦 Устанавливаю зависимости...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")]
        )
    except Exception as e:
        print(f"❌ Не удалось установить зависимости автоматически: {e}")
        print(f"   Выполните вручную: pip install -r {ROOT / 'requirements.txt'}")
        sys.exit(1)


def read_env():
    data = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            data[k.strip()] = v.strip()
    return data


def write_env(data):
    lines = [f"{k}={v}" for k, v in data.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_tokens(data):
    changed = False
    for key, hint in REQUIRED:
        if data.get(key):
            continue
        print(f"\n🔑 {hint}")
        value = ""
        while not value:
            value = input(f"   {key} = ").strip()
            if not value:
                print("   ⚠️ Пусто — попробуйте ещё раз.")
        data[key] = value
        changed = True
    for key, default in DEFAULTS:
        if not data.get(key):
            data[key] = default
            changed = True
    return changed


def main():
    print("🛒 LZT Market Bot — установка и запуск")
    ensure_dependencies()

    data = read_env()
    if collect_tokens(data):
        write_env(data)
        print(f"\n✅ Настройки сохранены в {ENV_PATH.name}")
    else:
        print("✅ Настройки уже заданы.")

    os.environ.update({k: str(v) for k, v in data.items()})

    print("\n🚀 Запуск бота... (Ctrl+C для остановки)\n")
    from bot import main as bot_main
    asyncio.run(bot_main())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Остановлено.")
