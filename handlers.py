from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from keyboards import (
    get_main_menu, get_management_menu, get_profile_keyboard,
    get_mass_delete_confirm_keyboard, get_price_mode_keyboard,
)
from forms import (
    show_categories_menu, start_item_creation,
    handle_form_input, handle_field_skip, handle_field_choice,
    handle_cookies_done,
    confirm_publish, cancel_publish, edit_item_form,
    ItemCreationStates, user_forms, MARKET_CATEGORIES, DISABLED_CATEGORIES,
    refresh_category_status, clear_category_cache,
)
from item_management import (
    ItemManageStates, render_items_list, render_item_detail,
    handle_single_price_input,
    items_page_callback, item_view_callback, item_back_callback,
    item_open_callback, item_close_callback, item_price_callback,
    item_delete_ask_callback, item_delete_yes_callback,
)
from api_client import api_client
from data.user_states import UserManagementState
import ui
import html
import re
import logging

logger = logging.getLogger(__name__)

management_states = {}


class ManagementStates(StatesGroup):
    percent_links = State()
    percent_value = State()
    fixed_lines   = State()


def parse_item_ids(text: str) -> list:
    ids = []
    for m in re.finditer(r'(?:lzt|lolz)\.market/(\d+)', text or ''):
        ids.append(int(m.group(1)))
    if not ids:
        for m in re.finditer(r'\b(\d{4,})\b', text or ''):
            ids.append(int(m.group(1)))
    seen, out = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def parse_fixed_lines(text: str) -> list:
    result = []
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.search(r'(?:lzt|lolz)\.market/(\d+)', line)
        if m:
            item_id = int(m.group(1))
            rest = line[m.end():]
        else:
            parts = line.split(None, 1)
            if parts and parts[0].isdigit():
                item_id = int(parts[0])
                rest = parts[1] if len(parts) > 1 else ''
            else:
                continue
        pm = re.search(r'(\d+(?:[.,]\d+)?)', rest)
        if not pm:
            continue
        price = float(pm.group(1).replace(',', '.'))
        if price < 1:
            continue
        result.append((item_id, price))
    return result


async def start_command(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_forms.pop(user_id, None)
    management_states.pop(user_id, None)
    clear_category_cache()
    await refresh_category_status()
    await message.answer(
        ui.hub(
            "👋 <b>Добро пожаловать!</b>",
            "Ваш карманный маркетплейс аккаунтов LZT Market.",
            "",
            f"{ui.te('create', '📦')}  <b>Создать товар</b> — залив за пару минут",
            f"{ui.te('my_items', '📊')}  <b>Мои товары</b> — карточки, цены, статусы",
            f"{ui.te('manage', '⚙️')}  <b>Управление</b> — массовые операции",
            f"{ui.te('profile', '👤')}  <b>Профиль</b> — баланс и статистика",
            "",
            "<i>Выберите действие ниже</i> 👇",
        ),
        reply_markup=get_main_menu()
    )


async def help_command(message: Message):
    await message.answer(
        f"{ui.BRAND}\n{ui.DIV}\n"
        "📖 <b>Справка</b>\n\n"
        "<b>Создание товара:</b>\n"
        "1. Нажмите «📦 Создать товар»\n"
        "2. Выберите категорию (🚧 — на техработах)\n"
        "3. Заполните поля формы\n"
        "4. Проверьте данные и опубликуйте\n\n"
        "<b>Форматы данных по категориям:</b>\n"
        "• Логин:Пароль — <code>login:password</code>\n"
        "• Email:Пароль — <code>email@mail.ru:pass</code>\n"
        "• Telegram — содержимое файла <code>session.json</code>\n"
        "• Куки — JSON из DevTools (F12) → Application → Cookies\n\n"
        "<b>Категории с куками:</b>\n"
        "Epic Games, Fortnite, Social Club, Instagram, TikTok\n\n"
        "<b>Категории с почтой (обязательно):</b>\n"
        "Epic Games, Fortnite, EFT, Supercell\n\n"
        "<b>Категории с регионом:</b>\n"
        "WoT, WoT Blitz — обязательно\n"
        "Riot, miHoYo — необязательно\n\n"
        "<b>Мои товары (📊 /my):</b>\n"
        "• Список с постраничной навигацией\n"
        "• Карточка товара: изменить цену, открыть/закрыть, удалить\n\n"
        "<b>Управление (⚙️ /manage):</b>\n"
        "• Изменить цены: снизить на % или задать вручную по ссылкам\n"
        "• Массово открывать/закрывать и удалять закрытые товары\n"
        "• Экспортировать список товаров\n\n"
        "<b>Профиль (👤 /profile):</b>\n"
        "• Имя, баланс и статистика по товарам\n\n"
        "/start /my /manage /profile /help /cancel",
        reply_markup=get_main_menu()
    )


async def cancel_command(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    user_forms.pop(user_id, None)
    management_states.pop(user_id, None)
    await message.answer("❌ <b>Действие отменено.</b>", reply_markup=get_main_menu())


async def my_items_command(message: Message, state: FSMContext):
    await render_items_list(message, state, show='active', page=1, edit=False)


async def profile_command(message: Message, edit: bool = False):
    try:
        info = await api_client.get_user_info()
        user = info.get('user', info) if isinstance(info, dict) else {}

        username = user.get('username') or user.get('name') or '—'
        user_id  = user.get('user_id') or user.get('userId') or '—'
        balance  = user.get('balance')
        hold     = user.get('hold')

        active = await api_client.get_all_user_items('active')
        closed = await api_client.get_all_user_items('closed')

        lines = [
            f"🧑 Пользователь: <b>{html.escape(str(username))}</b>",
            f"🆔 ID: <code>{user_id}</code>",
        ]
        if balance is not None:
            lines.append(f"💰 Баланс: <b>{balance}</b> ₽")
        if hold is not None:
            lines.append(f"⏳ В холде: {hold} ₽")
        lines += [
            "",
            f"{ui.te('my_items', '📦')} <b>Товары</b>",
            f"✅ Активных: <b>{len(active)}</b>",
            f"🔒 Закрытых: <b>{len(closed)}</b>",
        ]
        text = ui.hub(f"{ui.te('profile', '👤')} <b>Профиль</b>", "\n".join(lines))
    except Exception as e:
        logger.error(f"Profile error: {e}")
        text = f"❌ Не удалось загрузить профиль:\n{e}"

    if edit:
        try:
            await message.edit_text(text, reply_markup=get_profile_keyboard())
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=get_profile_keyboard())


MANAGE_TEXT = ui.hub(
    f"{ui.te('manage', '⚙️')} <b>Управление товарами</b>",
    "Массовые операции сразу по всем вашим товарам:",
    "",
    f"{ui.te('price', '💰')}  изменить цену   🔓  открыть   🔒  закрыть",
    f"{ui.te('delete', '🗑')}  удалить закрытые   {ui.te('export', '📤')}  экспорт ссылок",
)


async def manage_command(message: Message):
    await message.answer(MANAGE_TEXT, reply_markup=get_management_menu())


async def create_item_callback(callback: CallbackQuery, state: FSMContext):
    await show_categories_menu(callback.message, state)
    await callback.answer()


async def my_items_callback(callback: CallbackQuery, state: FSMContext):
    await render_items_list(callback.message, state, show='active', page=1, edit=True)
    await callback.answer()


async def manage_callback(callback: CallbackQuery):
    try:
        await callback.message.edit_text(MANAGE_TEXT, reply_markup=get_management_menu())
    except Exception:
        await callback.message.answer(MANAGE_TEXT, reply_markup=get_management_menu())
    await callback.answer()


async def profile_callback(callback: CallbackQuery):
    await profile_command(callback.message, edit=True)
    await callback.answer()


MAIN_TEXT = ui.hub("🏠 <b>Главное меню</b>", "Выберите действие 👇")


async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    user_forms.pop(user_id, None)
    try:
        await callback.message.edit_text(MAIN_TEXT, reply_markup=get_main_menu())
    except Exception:
        await callback.message.answer(MAIN_TEXT, reply_markup=get_main_menu())
    await callback.answer()


async def back_to_creation(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_forms.pop(user_id, None)
    await show_categories_menu(callback.message, state)
    await callback.answer()


async def category_callback(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.replace('category_', ''))

    if category_id in DISABLED_CATEGORIES:
        await callback.answer("🚧 Категория на техработах. Залив временно закрыт.", show_alert=True)
        return

    category_name = next(
        (c['name'] for c in MARKET_CATEGORIES if c['id'] == category_id),
        'Неизвестная категория'
    )
    await callback.message.edit_text(
        f"📝 <b>Создание товара: {category_name}</b>\n\nЗаполните поля формы:"
    )
    await start_item_creation(
        callback.message, state, category_id, category_name,
        user_id=callback.from_user.id
    )
    await callback.answer()


async def disabled_category_callback(callback: CallbackQuery):
    await callback.answer("🚧 Категория на техработах. Залив временно закрыт.", show_alert=True)


async def handle_management_callbacks(callback: CallbackQuery, state: FSMContext):
    action  = callback.data
    user_id = callback.from_user.id

    if action == 'mass_price':
        await callback.message.edit_text(
            ui.hub(
                "💰 <b>Массовое изменение цен</b>",
                "Выберите способ:",
                "",
                "📉 <b>Снизить на процент</b> — пришлёте ссылки, затем %",
                "💵 <b>Задать цены вручную</b> — ссылка + новая цена в строке",
            ),
            reply_markup=get_price_mode_keyboard()
        )

    elif action in ('mass_open', 'mass_close'):
        verb = 'Открытие' if action == 'mass_open' else 'Закрытие'
        await callback.message.edit_text(f"⏳ {verb} всех товаров...")
        await perform_mass_open_close(callback, action == 'mass_open')

    elif action == 'export_links':
        await callback.message.edit_text("⏳ Сбор ссылок...")
        await export_items_links(callback)

    elif action == 'mass_delete_closed':
        await callback.message.edit_text(
            "🗑 <b>Удаление всех закрытых товаров</b>\n\n"
            "Будут безвозвратно удалены <b>все закрытые</b> объявления.\n"
            "⚠️ Действие необратимо. Продолжить?",
            reply_markup=get_mass_delete_confirm_keyboard()
        )

    elif action == 'mass_delete_closed_yes':
        await callback.message.edit_text("⏳ Удаляю закрытые товары...")
        await perform_mass_delete_closed(callback)

    await callback.answer()


async def perform_mass_open_close(callback: CallbackQuery, do_open: bool):
    try:
        show_param = 'closed' if do_open else 'active'
        items = await api_client.get_all_user_items(show_param)

        if not items:
            label = 'закрытых' if do_open else 'активных'
            await callback.message.edit_text(f"📭 Нет {label} товаров для обработки.")
            await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())
            return

        success = failed = 0
        for item in items:
            item_id = item.get('item_id')
            try:
                if do_open:
                    await api_client.open_item(item_id)
                else:
                    await api_client.close_item(item_id)
                success += 1
            except Exception as e:
                logger.error(f"Failed on item {item_id}: {e}")
                failed += 1

        label = 'Открытие' if do_open else 'Закрытие'
        await callback.message.edit_text(
            f"✅ <b>{label} завершено!</b>\n\n✅ Успешно: {success}\n❌ Ошибок: {failed}"
        )
    except Exception as e:
        logger.error(f"Mass open/close error: {e}")
        await callback.message.edit_text(f"❌ Ошибка:\n{e}")

    await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())


async def perform_mass_delete_closed(callback: CallbackQuery):
    try:
        items = await api_client.get_all_user_items('closed')

        if not items:
            await callback.message.edit_text("📭 Нет закрытых товаров для удаления.")
            await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())
            return

        success = failed = 0
        for item in items:
            item_id = item.get('item_id')
            try:
                await api_client.delete_item(item_id)
                success += 1
            except Exception as e:
                logger.error(f"Failed to delete item {item_id}: {e}")
                failed += 1

        await callback.message.edit_text(
            f"🗑 <b>Удаление завершено!</b>\n\n✅ Удалено: {success}\n❌ Ошибок: {failed}"
        )
    except Exception as e:
        logger.error(f"Mass delete error: {e}")
        await callback.message.edit_text(f"❌ Ошибка:\n{e}")

    await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())


async def export_items_links(callback: CallbackQuery):
    try:
        items = (await api_client.get_all_user_items('active')
                 + await api_client.get_all_user_items('closed'))

        if not items:
            await callback.message.edit_text("📭 Нет товаров для экспорта.")
            await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())
            return

        lines = ["Ваши товары на Lolzteam Market", "=" * 40, ""]
        for item in items:
            item_id    = item.get('item_id')
            state_val  = item.get('item_state', '')
            state_icon = '✅' if state_val == 'active' else '🔒'
            lines += [
                f"ID: {item_id}  {state_icon}",
                f"Название: {item.get('title', '—')}",
                f"Цена: {item.get('price', '—')} руб.",
                f"Ссылка: https://lzt.market/{item_id}",
                "-" * 30,
            ]
        lines.append(f"\nВсего: {len(items)}")

        content = "\n".join(lines).encode('utf-8')
        await callback.message.answer_document(
            document=types.BufferedInputFile(content, filename='my_items.txt'),
            caption=f"📤 Экспорт завершён. Всего товаров: {len(items)}"
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        await callback.message.edit_text(f"❌ Ошибка экспорта:\n{e}")

    await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())


def _norm_price(price: float):
    return int(price) if float(price).is_integer() else price


async def mass_price_percent_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManagementStates.percent_links)
    await callback.message.edit_text(
        ui.hub(
            "📉 <b>Снижение на процент</b>",
            "Пришлите <b>ссылки на товары</b> — по одной в строке "
            "(можно прямо выгрузку из «Экспорт ссылок»).",
            "",
            "На следующем шаге спрошу процент снижения.",
        )
    )
    await callback.answer()


async def handle_percent_links(message: Message, state: FSMContext):
    ids = parse_item_ids(message.text or '')
    if not ids:
        await message.answer("⚠️ Не нашёл ссылок или ID. Пришлите ссылки на товары (по одной в строке). Или /cancel.")
        return
    await state.update_data(percent_ids=ids)
    await state.set_state(ManagementStates.percent_value)
    await message.answer(
        f"✅ Принято товаров: <b>{len(ids)}</b>.\n\n"
        f"На сколько процентов снизить цену? Введите число (например, <code>10</code>)."
    )


async def handle_percent_value(message: Message, state: FSMContext):
    try:
        pct = float((message.text or '').replace(',', '.').replace('%', '').strip())
        if not (0 < pct < 100):
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("⚠️ Введите процент от 1 до 99 (например, <code>10</code>). Или /cancel.")
        return

    data = await state.get_data()
    ids = data.get('percent_ids', [])
    await message.answer(f"⏳ Снижаю цены на {pct:g}% для {len(ids)} товаров...")

    success = failed = 0
    for item_id in ids:
        try:
            info = await api_client.get_item(item_id)
            it = info.get('item', info) if isinstance(info, dict) else {}
            cur = float(it.get('price'))
            new_price = round(cur * (1 - pct / 100), 2)
            if new_price < 1:
                new_price = 1.0
            await api_client.edit_item(item_id, {'price': _norm_price(new_price), 'currency': 'rub'})
            success += 1
        except Exception as e:
            logger.error(f"percent price {item_id}: {e}")
            failed += 1

    await state.clear()
    await message.answer(
        f"✅ <b>Цены снижены на {pct:g}%!</b>\n\n"
        f"✅ Успешно: {success}\n❌ Ошибок: {failed}",
        reply_markup=get_main_menu()
    )


async def mass_price_fixed_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManagementStates.fixed_lines)
    await callback.message.edit_text(
        ui.hub(
            "💵 <b>Ручные цены</b>",
            "Пришлите строки в формате «ссылка + новая цена», каждая с новой строки:",
            "",
            "<code>https://lzt.market/235111832 250</code>",
            "<code>https://lzt.market/235111833 1990</code>",
        )
    )
    await callback.answer()


async def handle_fixed_lines(message: Message, state: FSMContext):
    pairs = parse_fixed_lines(message.text or '')
    if not pairs:
        await message.answer(
            "⚠️ Не разобрал ни одной строки.\n"
            "Формат: <code>https://lzt.market/ID цена</code>, каждая с новой строки. Или /cancel."
        )
        return

    await message.answer(f"⏳ Обновляю цены для {len(pairs)} товаров...")
    success = failed = 0
    for item_id, price in pairs:
        try:
            await api_client.edit_item(item_id, {'price': _norm_price(price), 'currency': 'rub'})
            success += 1
        except Exception as e:
            logger.error(f"fixed price {item_id}: {e}")
            failed += 1

    await state.clear()
    await message.answer(
        f"✅ <b>Цены обновлены!</b>\n\n"
        f"✅ Успешно: {success}\n❌ Ошибок: {failed}",
        reply_markup=get_main_menu()
    )


def register_handlers(dp: Dispatcher):
    dp.message.register(start_command,    Command('start'))
    dp.message.register(cancel_command,   Command('cancel'))
    dp.message.register(my_items_command, Command('my'))
    dp.message.register(manage_command,   Command('manage'))
    dp.message.register(profile_command,  Command('profile'))
    dp.message.register(help_command,     Command('help'))

    dp.message.register(handle_form_input, ItemCreationStates.filling_fields)

    dp.message.register(handle_percent_links,      ManagementStates.percent_links)
    dp.message.register(handle_percent_value,      ManagementStates.percent_value)
    dp.message.register(handle_fixed_lines,        ManagementStates.fixed_lines)
    dp.message.register(handle_single_price_input, ItemManageStates.waiting_single_price)

    dp.callback_query.register(create_item_callback, lambda c: c.data == 'create_item')
    dp.callback_query.register(my_items_callback,    lambda c: c.data == 'my_items')
    dp.callback_query.register(manage_callback,      lambda c: c.data == 'manage')
    dp.callback_query.register(profile_callback,     lambda c: c.data == 'profile')
    dp.callback_query.register(back_to_main,         lambda c: c.data == 'back_to_main')
    dp.callback_query.register(back_to_creation,     lambda c: c.data == 'back_to_creation')

    dp.callback_query.register(items_page_callback,      lambda c: c.data and c.data.startswith('mi_page_'))
    dp.callback_query.register(item_view_callback,       lambda c: c.data and c.data.startswith('mi_view_'))
    dp.callback_query.register(item_back_callback,       lambda c: c.data == 'mi_back')
    dp.callback_query.register(item_open_callback,       lambda c: c.data and c.data.startswith('mi_open_'))
    dp.callback_query.register(item_close_callback,      lambda c: c.data and c.data.startswith('mi_close_'))
    dp.callback_query.register(item_price_callback,      lambda c: c.data and c.data.startswith('mi_price_'))
    dp.callback_query.register(item_delete_ask_callback, lambda c: c.data and c.data.startswith('mi_delask_'))
    dp.callback_query.register(item_delete_yes_callback, lambda c: c.data and c.data.startswith('mi_delyes_'))

    dp.callback_query.register(category_callback,
                                lambda c: c.data and c.data.startswith('category_'))
    dp.callback_query.register(disabled_category_callback,
                                lambda c: c.data and c.data.startswith('disabled_cat_'))

    dp.callback_query.register(handle_field_skip,
                                lambda c: c.data == 'field_skip')
    dp.callback_query.register(handle_cookies_done,
                                lambda c: c.data == 'cookies_done')
    dp.callback_query.register(handle_field_choice,
                                lambda c: c.data and c.data.startswith('field_choice_'))

    dp.callback_query.register(confirm_publish,
                                lambda c: c.data in ('confirm_publish', 'confirm_publish_closed'))
    dp.callback_query.register(cancel_publish,  lambda c: c.data == 'cancel_publish')
    dp.callback_query.register(edit_item_form,  lambda c: c.data == 'edit_item')

    dp.callback_query.register(mass_price_percent_start, lambda c: c.data == 'mass_price_percent')
    dp.callback_query.register(mass_price_fixed_start,   lambda c: c.data == 'mass_price_fixed')
    dp.callback_query.register(
        handle_management_callbacks,
        lambda c: c.data in (
            'mass_price', 'mass_open', 'mass_close', 'export_links',
            'mass_delete_closed', 'mass_delete_closed_yes',
        )
    )
