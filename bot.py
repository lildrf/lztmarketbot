import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats,
)
from config import config
from handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        config.validate()
        logger.info("✅ Конфигурация загружена успешно")
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        return

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    register_handlers(dp)

    commands = [
        BotCommand(command='start',   description='🏠 Главное меню'),
        BotCommand(command='my',      description='📊 Мои товары'),
        BotCommand(command='manage',  description='⚙️ Управление товарами'),
        BotCommand(command='profile', description='👤 Профиль и баланс'),
        BotCommand(command='help',    description='📖 Справка'),
        BotCommand(command='cancel',  description='❌ Отменить действие'),
    ]
    scopes = [BotCommandScopeDefault(), BotCommandScopeAllPrivateChats()]
    for scope in scopes:
        for lang in (None, 'ru', 'en'):
            try:
                await bot.delete_my_commands(scope=scope, language_code=lang)
            except Exception as e:
                logger.warning(f"delete_my_commands failed ({scope}, {lang}): {e}")
    for scope in scopes:
        try:
            await bot.set_my_commands(commands, scope=scope)
        except Exception as e:
            logger.warning(f"set_my_commands failed ({scope}): {e}")
    logger.info("✅ Команды меню обновлены")

    logger.info("🚀 Бот запущен!")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        from api_client import api_client
        await api_client.close()

if __name__ == "__main__":
    asyncio.run(main())
