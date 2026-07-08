from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict
import ui


def get_categories_keyboard(categories: List[Dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        category_id = category.get('id')
        category_name = category.get('name', 'Без названия')
        disabled = category.get('disabled', False)
        prefix = 'disabled_cat_' if disabled else 'category_'
        builder.button(
            text=category_name,
            callback_data=f"{prefix}{category_id}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text='🏠 В главное меню', callback_data='back_to_main'))
    return builder.as_markup()


def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Создать товар', callback_data='create_item', **ui.btn_extra('create', ui.SUCCESS))
    builder.button(text='Мои товары',    callback_data='my_items',    **ui.btn_extra('my_items'))
    builder.button(text='Управление',    callback_data='manage',      **ui.btn_extra('manage'))
    builder.button(text='Профиль',       callback_data='profile',     **ui.btn_extra('profile'))
    builder.adjust(2)
    return builder.as_markup()


def get_management_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Изменить цены',         callback_data='mass_price',         **ui.btn_extra('price'))
    builder.button(text='🔓 Открыть все товары', callback_data='mass_open',          **ui.btn_extra('open', ui.SUCCESS))
    builder.button(text='🔒 Закрыть все товары',  callback_data='mass_close',         **ui.btn_extra('close'))
    builder.button(text='Удалить закрытые',      callback_data='mass_delete_closed', **ui.btn_extra('delete', ui.DANGER))
    builder.button(text='Экспорт ссылок',        callback_data='export_links',       **ui.btn_extra('export'))
    builder.button(text='⬅️ Назад',              callback_data='back_to_main',       **ui.btn_extra('back'))
    builder.adjust(1)
    return builder.as_markup()


def get_price_mode_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='📉 Снизить на процент',  callback_data='mass_price_percent')
    builder.button(text='💵 Задать цены вручную', callback_data='mass_price_fixed')
    builder.button(text='⬅️ Назад',               callback_data='manage')
    builder.adjust(1)
    return builder.as_markup()


def get_items_list_keyboard(items: List[Dict], show: str,
                            page: int, total_pages: int) -> InlineKeyboardMarkup:
    rows: List[List[InlineKeyboardButton]] = []

    for it in items:
        item_id = it.get('item_id')
        state   = it.get('item_state', '')
        icon    = '✅' if state == 'active' else '🔒'
        title   = (it.get('title') or 'Без названия').strip()
        if len(title) > 28:
            title = title[:27] + '…'
        price = it.get('price', '—')
        rows.append([InlineKeyboardButton(
            text=f"{icon} {title} • {price}₽",
            callback_data=f"mi_view_{item_id}"
        )])

    if total_pages > 1:
        nav: List[InlineKeyboardButton] = []
        if page > 1:
            nav.append(InlineKeyboardButton(text='◀️', callback_data=f"mi_page_{show}_{page - 1}"))
        nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=f"mi_page_{show}_{page}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton(text='▶️', callback_data=f"mi_page_{show}_{page + 1}"))
        rows.append(nav)

    if show == 'active':
        rows.append([InlineKeyboardButton(text='🔒 Показать закрытые', callback_data='mi_page_closed_1')])
    else:
        rows.append([InlineKeyboardButton(text='✅ Показать активные', callback_data='mi_page_active_1')])

    rows.append([
        InlineKeyboardButton(text='🔄 Обновить', callback_data=f"mi_page_{show}_{page}"),
        InlineKeyboardButton(text='🏠 Меню',     callback_data='back_to_main'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_item_detail_keyboard(item_id: int, is_active: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text='Изменить цену', callback_data=f"mi_price_{item_id}", **ui.btn_extra('price'))],
    ]
    if is_active:
        rows.append([InlineKeyboardButton(text='🔒 Закрыть', callback_data=f"mi_close_{item_id}", **ui.btn_extra('close'))])
    else:
        rows.append([InlineKeyboardButton(text='🔓 Открыть', callback_data=f"mi_open_{item_id}", **ui.btn_extra('open', ui.SUCCESS))])
    rows.append([InlineKeyboardButton(text='Удалить', callback_data=f"mi_delask_{item_id}", **ui.btn_extra('delete', ui.DANGER))])
    rows.append([
        InlineKeyboardButton(text='⬅️ К списку', callback_data='mi_back'),
        InlineKeyboardButton(text='🏠 Меню',     callback_data='back_to_main'),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_delete_confirm_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Да, удалить', callback_data=f"mi_delyes_{item_id}", **ui.btn_extra('delete', ui.DANGER))],
        [InlineKeyboardButton(text='⬅️ Отмена',    callback_data=f"mi_view_{item_id}")],
    ])


def get_price_edit_keyboard(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⬅️ Отмена', callback_data=f"mi_view_{item_id}")],
    ])


def get_mass_delete_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Да, удалить все закрытые', callback_data='mass_delete_closed_yes', **ui.btn_extra('delete', ui.DANGER))],
        [InlineKeyboardButton(text='⬅️ Отмена',               callback_data='manage')],
    ])


def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Мои товары', callback_data='my_items', **ui.btn_extra('my_items')),
         InlineKeyboardButton(text='🏠 Меню',    callback_data='back_to_main')],
    ])


def get_field_keyboard(required: bool = True, back: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not required:
        builder.button(text='⏭ Пропустить', callback_data='field_skip')
    if back:
        builder.button(text='⬅️ Назад', callback_data='back_to_creation')
    builder.adjust(1)
    return builder.as_markup()


def get_choice_keyboard(choices: Dict, back: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for num, (value, label) in choices.items():
        builder.button(text=label, callback_data=f"field_choice_{value}")
    if back:
        builder.button(text='⬅️ Назад', callback_data='back_to_creation')
    builder.adjust(1)
    return builder.as_markup()


def get_publish_options_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Опубликовать открытым',  callback_data='confirm_publish',        **ui.btn_extra('publish', ui.SUCCESS))
    builder.button(text='🔒 Опубликовать закрытым', callback_data='confirm_publish_closed', **ui.btn_extra('publish', ui.SUCCESS))
    builder.button(text='✏️ Редактировать',          callback_data='edit_item')
    builder.button(text='❌ Отмена',                 callback_data='cancel_publish',         **ui.btn_extra('cancel', ui.DANGER))
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return get_publish_options_keyboard()


def get_back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='⬅️ Назад', callback_data='back_to_creation')
    return builder.as_markup()


def get_cookies_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='⏭ Без куки',  callback_data='cookies_skip')
    builder.button(text='⬅️ Назад',    callback_data='back_to_creation')
    builder.adjust(1)
    return builder.as_markup()


def get_cookies_input_keyboard(required: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='✅ Готово', callback_data='cookies_done', **ui.btn_extra('done', ui.SUCCESS))
    if not required:
        builder.button(text='⏭ Пропустить', callback_data='field_skip')
    builder.button(text='⬅️ Назад', callback_data='back_to_creation')
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='📊 Статистика', callback_data='stats')
    builder.button(text='⬅️ Назад',      callback_data='back_to_main')
    builder.adjust(1)
    return builder.as_markup()
