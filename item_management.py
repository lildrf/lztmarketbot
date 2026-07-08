import html
import logging
from math import ceil

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from api_client import api_client
from keyboards import (
    get_items_list_keyboard, get_item_detail_keyboard,
    get_delete_confirm_keyboard, get_price_edit_keyboard,
    get_main_menu,
)
import ui

logger = logging.getLogger(__name__)

PAGE_SIZE = 6

STATE_LABELS = {
    'active':  '✅ Активен',
    'closed':  '🔒 Закрыт',
    'paid':    '💸 Продан',
    'deleted': '🗑 Удалён',
    'awaiting': '⏳ Проверяется',
}


class ItemManageStates(StatesGroup):
    waiting_single_price = State()


def _extract_item(response: dict) -> dict:
    if isinstance(response, dict) and isinstance(response.get('item'), dict):
        return response['item']
    return response if isinstance(response, dict) else {}


async def _show(message: Message, text: str, kb, edit: bool):
    if edit:
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except TelegramBadRequest as e:
            if 'not modified' in str(e).lower():
                return
        except Exception:
            pass
    await message.answer(text, reply_markup=kb)


async def render_items_list(message: Message, state: FSMContext,
                            show: str = 'active', page: int = 1,
                            edit: bool = False, notice: str = ''):
    try:
        all_items = await api_client.get_all_user_items(show)
    except Exception as e:
        logger.error(f"Failed to load items list: {e}")
        await _show(message, f"❌ Не удалось загрузить товары:\n{e}", get_main_menu(), edit)
        return

    label = 'активных' if show == 'active' else 'закрытых'

    if not all_items:
        other = 'closed' if show == 'active' else 'active'
        other_label = 'закрытые' if show == 'active' else 'активные'
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"Показать {other_label}", callback_data=f"mi_page_{other}_1")],
            [InlineKeyboardButton(text='🏠 Меню', callback_data='back_to_main')],
        ])
        text = (notice + "\n\n" if notice else "") + f"📭 Нет {label} товаров."
        await _show(message, text, kb, edit)
        return

    total = len(all_items)
    total_pages = max(1, ceil(total / PAGE_SIZE))
    page = max(1, min(page, total_pages))
    chunk = all_items[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    await state.update_data(list_show=show, list_page=page)

    title = ("✅ <b>Активные товары</b>" if show == 'active'
             else "🔒 <b>Закрытые товары</b>")
    text = ui.hub(
        title,
        (notice if notice else None),
        f"Всего: <b>{total}</b>  •  Страница {page} из {total_pages}",
        "",
        "👇 Нажмите на товар, чтобы открыть карточку.",
    )

    kb = get_items_list_keyboard(chunk, show, page, total_pages)
    await _show(message, text, kb, edit)


async def render_item_detail(message: Message, state: FSMContext,
                            item_id: int, edit: bool = True, notice: str = ''):
    try:
        response = await api_client.get_item(item_id)
        item = _extract_item(response)
    except Exception as e:
        logger.error(f"Failed to load item {item_id}: {e}")
        await _show(message, f"❌ Не удалось загрузить товар <code>{item_id}</code>:\n{e}",
                    get_main_menu(), edit)
        return

    if not item or not item.get('item_id'):
        await _show(message, f"❌ Товар <code>{item_id}</code> не найден.", get_main_menu(), edit)
        return

    item_state = item.get('item_state', '')
    is_active  = item_state == 'active'
    title      = item.get('title') or 'Без названия'
    price      = item.get('price', '—')
    currency   = (item.get('price_currency') or 'rub')
    cur_sign   = '₽' if currency == 'rub' else currency.upper()
    origin     = item.get('item_origin', '—')
    state_label = STATE_LABELS.get(item_state, item_state or '—')

    lines = [
        f"🆔 ID: <code>{item.get('item_id')}</code>",
        f"💰 Цена: <b>{price}</b> {cur_sign}",
        f"📌 Статус: {state_label}",
        f"🧬 Происхождение: {html.escape(str(origin))}",
        f"🔗 https://lzt.market/{item.get('item_id')}",
    ]
    description = item.get('description')
    if description:
        short = str(description).strip()
        if len(short) > 300:
            short = short[:300] + '…'
        lines += ["", f"📝 {html.escape(short)}"]

    text = ui.hub(
        f"🏷 <b>{html.escape(str(title))}</b>",
        (notice if notice else None),
        "\n".join(lines),
    )
    kb = get_item_detail_keyboard(item.get('item_id'), is_active)
    await _show(message, text, kb, edit)


async def items_page_callback(callback: CallbackQuery, state: FSMContext):
    payload = callback.data[len('mi_page_'):]
    show, _, page_str = payload.rpartition('_')
    try:
        page = int(page_str)
    except ValueError:
        page = 1
    if show not in ('active', 'closed'):
        show = 'active'
    await render_items_list(callback.message, state, show, page, edit=True)
    await callback.answer()


async def item_view_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_view_'):])
    await render_item_detail(callback.message, state, item_id, edit=True)
    await callback.answer()


async def item_back_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    show = data.get('list_show', 'active')
    page = data.get('list_page', 1)
    await render_items_list(callback.message, state, show, page, edit=True)
    await callback.answer()


async def item_open_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_open_'):])
    await callback.answer('Открываю…')
    try:
        await api_client.open_item(item_id)
        notice = '🔓 <b>Товар открыт.</b>'
    except Exception as e:
        logger.error(f"open_item {item_id} failed: {e}")
        notice = f'❌ Не удалось открыть: {e}'
    await render_item_detail(callback.message, state, item_id, edit=True, notice=notice)


async def item_close_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_close_'):])
    await callback.answer('Закрываю…')
    try:
        await api_client.close_item(item_id)
        notice = '🔒 <b>Товар закрыт.</b>'
    except Exception as e:
        logger.error(f"close_item {item_id} failed: {e}")
        notice = f'❌ Не удалось закрыть: {e}'
    await render_item_detail(callback.message, state, item_id, edit=True, notice=notice)


async def item_price_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_price_'):])
    await state.update_data(edit_item_id=item_id)
    await state.set_state(ItemManageStates.waiting_single_price)
    await callback.message.edit_text(
        f"💰 <b>Изменение цены товара</b> <code>{item_id}</code>\n\n"
        f"Введите новую цену в рублях (например: <code>250</code>).\n"
        f"Или нажмите «Отмена».",
        reply_markup=get_price_edit_keyboard(item_id)
    )
    await callback.answer()


async def handle_single_price_input(message: Message, state: FSMContext):
    data = await state.get_data()
    item_id = data.get('edit_item_id')
    if not item_id:
        await state.set_state(None)
        return

    try:
        new_price = float(message.text.replace(',', '.').strip())
        if new_price < 1:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer("⚠️ Введите корректное число ≥ 1 (например: <code>250</code>). Или /cancel.")
        return

    await message.answer(f"⏳ Меняю цену товара <code>{item_id}</code> на {new_price} ₽…")
    try:
        price_val = int(new_price) if float(new_price).is_integer() else new_price
        await api_client.edit_item(item_id, {'price': price_val, 'currency': 'rub'})
        notice = f'✅ <b>Цена обновлена:</b> {new_price} ₽'
    except Exception as e:
        logger.error(f"edit price {item_id} failed: {e}")
        notice = f'❌ Не удалось изменить цену: {e}'

    await state.set_state(None)
    await state.update_data(edit_item_id=None)
    await render_item_detail(message, state, item_id, edit=False, notice=notice)


async def item_delete_ask_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_delask_'):])
    await callback.message.edit_text(
        f"🗑 <b>Удалить товар</b> <code>{item_id}</code>?\n\n"
        f"⚠️ Действие необратимо — объявление будет снято с продажи.",
        reply_markup=get_delete_confirm_keyboard(item_id)
    )
    await callback.answer()


async def item_delete_yes_callback(callback: CallbackQuery, state: FSMContext):
    item_id = int(callback.data[len('mi_delyes_'):])
    await callback.answer('Удаляю…')
    try:
        await api_client.delete_item(item_id)
        notice = f'🗑 <b>Товар</b> <code>{item_id}</code> <b>удалён.</b>'
    except Exception as e:
        logger.error(f"delete_item {item_id} failed: {e}")
        await render_item_detail(callback.message, state, item_id, edit=True,
                                 notice=f'❌ Не удалось удалить: {e}')
        return

    data = await state.get_data()
    show = data.get('list_show', 'active')
    page = data.get('list_page', 1)
    await render_items_list(callback.message, state, show, page, edit=True, notice=notice)
