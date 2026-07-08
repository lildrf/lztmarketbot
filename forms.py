from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from typing import Dict, Optional, List
import logging
import html

from data.user_states import user_forms, UserFormData
from keyboards import (
    get_field_keyboard, get_choice_keyboard, get_cookies_keyboard,
    get_cookies_input_keyboard,
    get_publish_options_keyboard, get_main_menu,
    get_categories_keyboard,
)
from api_client import api_client
import ui

logger = logging.getLogger(__name__)


CATEGORY_ID_TO_NAME = {
    1:  'steam',            3:  'ea',           4:  'warface',
    5:  'uplay',            6:  'llm',          7:  'socialclub',
    8:  'hytale',
    9:  'fortnite',         10: 'instagram',    11: 'battlenet',
    12: 'epicgames',        13: 'riot',         14: 'world-of-tanks',
    15: 'supercell',        16: 'wot-blitz',    17: 'mihoyo',
    18: 'escape-from-tarkov', 19: 'vpn',        20: 'tiktok',
    22: 'discord',          24: 'telegram',     28: 'minecraft',
    30: 'gifts',            31: 'roblox',
}


MARKET_CATEGORIES = [
    {'id': 1,  'name': 'Steam',              'icon': '♨️'},
    {'id': 3,  'name': 'EA App',             'icon': '🔶'},
    {'id': 4,  'name': 'Warface',            'icon': '🎯'},
    {'id': 5,  'name': 'Ubisoft Connect',    'icon': '🌀'},
    {'id': 6,  'name': 'ChatGPT / LLM',      'icon': '🧠'},
    {'id': 7,  'name': 'Social Club',        'icon': '🌆'},
    {'id': 8,  'name': 'Hytale',             'icon': '🐉'},
    {'id': 9,  'name': 'Fortnite',           'icon': '🌪'},
    {'id': 10, 'name': 'Instagram',          'icon': '🌈'},
    {'id': 11, 'name': 'Battle.net',         'icon': '❄️'},
    {'id': 12, 'name': 'Epic Games',         'icon': '🎇'},
    {'id': 13, 'name': 'Riot Games',         'icon': '⚔️'},
    {'id': 14, 'name': 'World of Tanks',     'icon': '🎖'},
    {'id': 15, 'name': 'Supercell',          'icon': '👑'},
    {'id': 16, 'name': 'WoT Blitz',          'icon': '⚡'},
    {'id': 17, 'name': 'miHoYo',             'icon': '🌌'},
    {'id': 18, 'name': 'Escape from Tarkov', 'icon': '🪖'},
    {'id': 19, 'name': 'VPN',                'icon': '🛡'},
    {'id': 20, 'name': 'TikTok',             'icon': '🎶'},
    {'id': 22, 'name': 'Discord',            'icon': '🎧'},
    {'id': 24, 'name': 'Telegram',           'icon': '✈️'},
    {'id': 28, 'name': 'Minecraft',          'icon': '⛏'},
    {'id': 30, 'name': 'Gifts',              'icon': '🎁'},
    {'id': 31, 'name': 'Roblox',             'icon': '🧩'},
]

CATEGORY_TITLE_EXAMPLES = {
    1:  'Steam • CS2 Prime, 1500 часов, инвентарь 50$',
    3:  'EA App • Apex Legends + Battlefield 2042',
    4:  'Warface • 70 ранг, топ оружие в инвентаре',
    5:  'Ubisoft • Rainbow Six Siege, много R6 кредитов',
    6:  'ChatGPT Plus • GPT-4o, история чистая',
    7:  'GTA V Online • 100 лвл, 20кк на счету',
    8:  'Hytale • ранний доступ, редкий ник',
    9:  'Fortnite • 50 скинов, OG аккаунт 2018',
    10: 'Instagram • 10к живых подписчиков',
    11: 'Battle.net • Overwatch 2 + Diablo IV',
    12: 'Epic Games • GTA V + RDR2, почта чистая',
    13: 'Valorant • Immortal, редкие скины ножей',
    14: 'World of Tanks • топ-10 танки, ЛБЗ выполнены',
    15: 'Brawl Stars • 30к кубков, все бойцы',
    16: 'WoT Blitz • топ-10, премиум танки',
    17: 'Genshin Impact • AR55, пять 5★ персонажей',
    18: 'Escape from Tarkov • EOD издание, 40 лвл',
    19: 'VPN • Premium подписка на 1 год',
    20: 'TikTok • 50к подписчиков, монетизация',
    22: 'Discord • Nitro + красивый тег',
    24: 'Telegram • аккаунт 2019 года, Premium',
    28: 'Minecraft • полный доступ, редкий ник',
    30: 'Telegram Premium • подписка 3 месяца',
    31: 'Roblox • 10к Robux, лимитированные items',
}

DISABLED_CATEGORIES: set = set()


ORIGINS_BY_CATEGORY: Dict[int, List[str]] = {
    1:  ['personal', 'resale', 'brute', 'stealer', 'phishing', 'dummy', 'retrieve_via_support'],
    3:  ['personal', 'resale', 'brute', 'stealer', 'phishing'],
    4:  ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    5:  ['personal', 'resale', 'brute', 'stealer', 'phishing'],
    6:  ['personal', 'resale', 'autoreg'],
    7:  ['personal', 'resale', 'brute', 'stealer', 'phishing'],
    8:  ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    9:  ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing', 'retrieve_via_support'],
    10: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    11: ['personal', 'resale', 'brute', 'stealer', 'phishing'],
    12: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    13: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    14: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    15: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    16: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    17: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    18: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    19: ['personal', 'resale', 'autoreg'],
    20: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    22: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    24: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing', 'self_registration'],
    28: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
    30: ['personal', 'resale'],
    31: ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'],
}


_category_params_cache: Dict[int, Dict] = {}


def clear_category_cache():
    _category_params_cache.clear()


def _iter_category_entries(response: Dict):
    container = None
    if isinstance(response, dict):
        for key in ('category', 'categories'):
            if key in response:
                container = response[key]
                break
        if container is None:
            container = response
    else:
        container = response

    if isinstance(container, dict):
        for cid, data in container.items():
            yield cid, data
    elif isinstance(container, list):
        for data in container:
            if isinstance(data, dict):
                cid = data.get('category_id') or data.get('id') or data.get('categoryId')
                yield cid, data


def _is_upload_disabled(data: Dict) -> bool:
    if not isinstance(data, dict):
        return False
    for key in ('upload_enabled', 'uploadable', 'can_upload', 'allow_upload'):
        if key in data:
            return not bool(data[key])
    for key in ('upload_disabled', 'disabled', 'is_disabled'):
        if key in data:
            return bool(data[key])
    return False


async def refresh_category_status():
    global DISABLED_CATEGORIES
    try:
        response = await api_client.get_categories()
        disabled = set()
        for cid, data in _iter_category_entries(response):
            if cid is None:
                continue
            try:
                cid_int = int(cid)
            except (ValueError, TypeError):
                continue
            if _is_upload_disabled(data):
                disabled.add(cid_int)
        DISABLED_CATEGORIES = disabled
        logger.info(f"Category status refreshed. Disabled: {sorted(DISABLED_CATEGORIES)}")
    except Exception as e:
        logger.error(f"Failed to refresh category status: {e}")


class ItemCreationStates(StatesGroup):
    selecting_category  = State()
    filling_fields      = State()
    confirming          = State()
    waiting_for_cookies = State()


def _origin_choices(cat_id: int) -> Dict:
    origins = ORIGINS_BY_CATEGORY.get(cat_id, ['personal', 'resale', 'autoreg', 'brute', 'stealer', 'phishing'])
    labels = {
        'personal':             '👤 Личный',
        'resale':               '🔄 Перепродажа',
        'autoreg':              '🤖 Авторег',
        'brute':                '💻 Брут',
        'stealer':              '🪝 Стилер',
        'phishing':             '🎣 Фишинг',
        'self_registration':    '✍️ Саморег',
        'dummy':                '🎭 Пустой (dummy)',
        'retrieve_via_support': '📞 Через поддержку',
    }
    return {str(i+1): (v, labels.get(v, v)) for i, v in enumerate(origins)}


def _f(name, label, placeholder='', required=True, ftype='text', choices=None,
       is_extra=False, extra_key=None, cookies_format=None):
    f = {'name': name, 'label': label, 'type': ftype, 'required': required, 'placeholder': placeholder}
    if choices is not None:
        f['choices'] = choices
    if is_extra:
        f['is_extra'] = True
    if extra_key:
        f['extra_key'] = extra_key
    if cookies_format:
        f['cookies_format'] = cookies_format
    return f


def _base_fields(cat_id=None):
    example = CATEGORY_TITLE_EXAMPLES.get(
        cat_id, 'Кратко и по делу: игра, уровень, что внутри аккаунта'
    )
    return [
        _f('title', 'Название товара', example),
        _f('price', 'Цена (в рублях)', '150', ftype='number'),
    ]

def _origin_field(cat_id: int):
    return _f('item_origin', 'Происхождение аккаунта', ftype='choice', choices=_origin_choices(cat_id))

def _desc_field():
    return _f('description', 'Описание товара', 'Описание аккаунта', required=False, ftype='textarea')

_LOGIN   = _f('login_data', 'Логин:Пароль', 'login:password')
_LOGIN_EMAIL = _f('account_login_data', 'Email аккаунта:Пароль', 'account@email.com:Password')
_EMAIL_OPT  = _f('email_login_data', 'Почта:Пароль от почты', 'email@mail.ru:MailPass', required=False)
_EMAIL_TEMP = _f('email_login_data', 'Почта:Пароль от почты', 'email@mail.ru:MailPass\n(необязательно — если к аккаунту привязана почта с доступом)', required=False)
_EMAIL_REQ  = _f('email_login_data', 'Привязанная почта:Пароль', 'linked@mail.ru:LinkedPass')

_EMAIL_LINKED = _f('email_login_data', 'Почта аккаунта:Пароль от почты',
                   'linked@mail.ru:MailPass\n(данные почтового ящика — нужны и для родной, и для авторег)')

_EMAIL_TYPE = _f('email_type', 'Тип почты аккаунта', ftype='choice', choices={
    '1': ('native',   '📧 Родная (аккаунт создан на эту почту)'),
    '2': ('autoreg',  '🤖 Авторег (зареган продавцом под аккаунт)'),
})

_EMAIL_TYPE_FM = _f('email_type', 'Тип почты аккаунта', ftype='choice', choices={
    '1': ('native',     '📧 Родная (аккаунт создан на эту почту)'),
    '2': ('autoreg',    '🤖 Авторег (зареган продавцом под аккаунт)'),
    '3': ('force_mail', '📭 Без своей почты — временную выдаст маркет'),
})

_GUARANTEE = _f('guarantee_duration', 'Длительность гарантии', ftype='choice', choices={
    '1': ('86400',  '🛡 24 часа'),
    '2': ('259200', '🟢 3 дня (расширенная)'),
})


def _build_category_fields(cat_id: int) -> List[Dict]:
    base   = _base_fields(cat_id)
    origin = _origin_field(cat_id)
    desc   = _desc_field()

    if cat_id == 1:
        return [*base, origin, desc, _LOGIN, _EMAIL_TEMP,
                _f('mfa_file', 'Steam Guard maFile (base64)', 'Содержимое .maFile в base64', required=False, is_extra=True, extra_key='mfa_file')]

    if cat_id == 3:
        return [*base, origin, desc, _LOGIN, _EMAIL_OPT]

    if cat_id == 4:
        return [*base, origin, desc, _LOGIN]

    if cat_id == 5:
        return [*base, origin, desc, _LOGIN, _EMAIL_OPT]

    if cat_id == 6:
        service_choices = {
            '1': ('chatgpt',  '🤖 ChatGPT'),
            '2': ('claude',   '🟠 Claude'),
            '3': ('cursor',   '🖱 Cursor'),
            '4': ('grok',     '𝕏 Grok'),
        }
        return [*base, origin, desc,
                _f('service', 'Сервис LLM', ftype='choice', choices=service_choices, is_extra=True, extra_key='service'),
                _LOGIN, _EMAIL_OPT]

    if cat_id == 7:
        return [*base, origin, desc, _LOGIN, _EMAIL_OPT,
                _f('cookies', 'Куки Social Club (JSON)', 'Откройте DevTools (F12) на https://socialclub.rockstargames.com/\n→ Application → Storage → Cookies → socialclub.rockstargames.com\n→ выберите все, скопируйте JSON', is_extra=True, extra_key='cookies')]

    if cat_id == 8:
        return [*base, origin, desc, _LOGIN, _EMAIL_OPT]

    if cat_id == 9:
        return [*base, origin, desc,
                _LOGIN_EMAIL,
                _EMAIL_TYPE_FM,
                _EMAIL_LINKED,
                _f('cookies', 'Куки Fortnite (JSON)', '⚠️ Нужен русский IP (🇷🇺 VPN РФ) — иначе ссылка вернёт authorizationCode: null.\n1) Войдите в аккаунт на epicgames.com\n2) Откройте в ТОМ ЖЕ браузере спец-ссылку (обновляет сессию и куки):\nhttps://www.epicgames.com/id/api/redirect?responseType=code&clientId=3f69e56c7649492c8cc29f1af08a8a12\n3) Экспортируйте куки расширением Cookie-Editor (Export → JSON) и вставьте сюда.\nМожно несколькими сообщениями или файлом .json', is_extra=True, extra_key='cookies'),
                _GUARANTEE]

    if cat_id == 10:
        return [*base, origin, desc, _LOGIN,
                _f('cookies', 'Куки Instagram (JSON)', 'Откройте DevTools (F12) на https://www.instagram.com/\n→ Application → Storage → Cookies → www.instagram.com\n→ выберите все, скопируйте JSON', is_extra=True, extra_key='cookies')]

    if cat_id == 11:
        return [*base, origin, desc, _LOGIN, _EMAIL_OPT]

    if cat_id == 12:
        return [*base, origin, desc,
                _LOGIN_EMAIL,
                _EMAIL_TYPE_FM,
                _EMAIL_LINKED,
                _f('cookies', 'Куки Epic Games (JSON)', 'Откройте DevTools (F12) на https://store.epicgames.com/\n→ Application → Cookies → скопируйте JSON', is_extra=True, extra_key='cookies'),
                _GUARANTEE]

    if cat_id == 13:
        region_choices = {
            '1': ('EUW',  '🇪🇺 EUW'),
            '2': ('EUNE', '🇪🇺 EUNE'),
            '3': ('NA',   '🇺🇸 NA'),
            '4': ('RU',   '🇷🇺 RU'),
            '5': ('TR',   '🇹🇷 TR'),
            '6': ('BR',   '🇧🇷 BR'),
            '7': ('LAS',  '🌎 LAS'),
            '8': ('LAN',  '🌎 LAN'),
            '9': ('OCE',  '🌏 OCE'),
            '10': ('JP',  '🇯🇵 JP'),
            '11': ('KR',  '🇰🇷 KR'),
        }
        return [*base, origin, desc, _LOGIN,
                _f('region', 'Регион сервера', ftype='choice', required=False, choices=region_choices, is_extra=True, extra_key='region')]

    if cat_id == 14:
        region_choices = {
            '1': ('RU',  '🇷🇺 RU'),
            '2': ('EU',  '🇪🇺 EU'),
            '3': ('NA',  '🇺🇸 NA'),
            '4': ('ASIA','🌏 ASIA'),
        }
        return [*base, origin, desc, _LOGIN,
                _f('region', 'Регион сервера', ftype='choice', choices=region_choices, is_extra=True, extra_key='region')]

    if cat_id == 15:
        system_choices = {
            '1': ('laser',  '⚡ Brawl Stars'),
            '2': ('scroll', '👑 Clash Royale'),
            '3': ('magic',  '⚔️ Clash of Clans'),
        }
        return [*base, origin, desc,
                _f('system', 'Игра Supercell', ftype='choice', choices=system_choices, is_extra=True, extra_key='system'),
                _EMAIL_TYPE_FM,
                _EMAIL_REQ,
                _GUARANTEE]

    if cat_id == 16:
        region_choices = {
            '1': ('RU',  '🇷🇺 RU'),
            '2': ('EU',  '🇪🇺 EU'),
            '3': ('NA',  '🇺🇸 NA'),
            '4': ('ASIA','🌏 ASIA'),
        }
        return [*base, origin, desc, _LOGIN,
                _f('region', 'Регион сервера', ftype='choice', choices=region_choices, is_extra=True, extra_key='region')]

    if cat_id == 17:
        region_choices = {
            '1': ('os_usa',    '🇺🇸 America'),
            '2': ('os_euro',   '🇪🇺 Europe'),
            '3': ('os_asia',   '🌏 Asia'),
            '4': ('os_cht',    '🇹🇼 TW/HK/MO'),
            '5': ('cn_gf01',   '🇨🇳 CN Official'),
            '6': ('cn_qd01',   '🇨🇳 CN Bilibili'),
        }
        return [*base, origin, desc, _LOGIN,
                _f('region', 'Регион (необязательно)', ftype='choice', required=False, choices=region_choices, is_extra=True, extra_key='region')]

    if cat_id == 18:
        return [*base, origin, desc,
                _LOGIN_EMAIL,
                _EMAIL_TYPE,
                _EMAIL_LINKED]

    if cat_id == 19:
        service_choices = {
            '1':  ('windscribeVPN',    '🌬 Windscribe'),
            '2':  ('tunnelbearVPN',    '🐻 TunnelBear'),
            '3':  ('vanishVPN',        '👻 Vanish'),
            '4':  ('mullvadVPN',       '🔐 Mullvad'),
            '5':  ('PIAVPN',           '🛡 PIA'),
            '6':  ('AdguardVPN',       '🛡 AdGuard'),
            '7':  ('pureVPN',          '💎 PureVPN'),
            '8':  ('ultraVPN',         '⚡ UltraVPN'),
            '9':  ('cyberghostVPN',    '👻 CyberGhost'),
            '10': ('vyprVPN',          '🔒 VyprVPN'),
            '11': ('hotspotShieldVPN', '🔥 Hotspot Shield'),
            '12': ('planetVPN',        '🌍 Planet VPN'),
        }
        return [*base, origin, desc,
                _f('service', 'VPN сервис', ftype='choice', choices=service_choices, is_extra=True, extra_key='service'),
                _LOGIN]

    if cat_id == 20:
        return [*base, origin, desc, _LOGIN,
                _f('cookies', 'Куки TikTok (JSON)', 'Откройте DevTools (F12) на https://www.tiktok.com/\n→ Application → Storage → Cookies → www.tiktok.com\n→ выберите все, скопируйте JSON', is_extra=True, extra_key='cookies')]

    if cat_id == 22:
        return [*base, origin, desc,
                _f('login_data', 'Токен Discord аккаунта', 'MTIz...xyz (токен пользователя, не бота)'),
                _EMAIL_OPT]

    if cat_id == 24:
        return [*base, origin, desc,
                _f('telegramJson', 'Session JSON (содержимое session.json)',
                   'Пришлите содержимое файла session.json (Telegram-сессия).\nМожно текстом, несколькими сообщениями или файлом .json',
                   is_extra=True, extra_key='telegramJson'),
                _f('tg_password', '2FA пароль (если есть)', 'Оставьте пустым если нет', required=False, is_extra=True, extra_key='password')]

    if cat_id == 28:
        return [*base, origin, desc, _LOGIN]

    if cat_id == 30:
        service_choices = {
            '1': ('telegram',       '✈️ Telegram Premium'),
            '2': ('discord',        '💜 Discord Nitro'),
            '3': ('discord_trial',  '💜 Discord Nitro Trial'),
        }
        return [*base, origin, desc,
                _f('service', 'Тип подарка', ftype='choice', choices=service_choices, is_extra=True, extra_key='service'),
                _f('login_data', 'Код подарка / ссылка', 'https://discord.gift/... или код')]

    if cat_id == 31:
        return [*base, origin, desc, _LOGIN]

    return [*base, origin, desc, _LOGIN, _EMAIL_OPT]


async def show_categories_menu(message: Message, state: FSMContext):
    await state.set_state(ItemCreationStates.selecting_category)
    cats_display = []
    for c in MARKET_CATEGORIES:
        if c['id'] in DISABLED_CATEGORIES:
            cats_display.append({**c, 'disabled': True, 'icon': '🚧',
                                 'name': c['name'] + ' · тех.работы'})
        else:
            cats_display.append(c)

    disabled_n = len(DISABLED_CATEGORIES)
    note = (f"🚧 <i>{disabled_n} категор. на техработах — залив временно закрыт</i>"
            if disabled_n else "✅ <i>Все категории доступны для залива</i>")

    text = ui.hub(
        "📂 <b>Выберите категорию</b>",
        "Нажмите на категорию, чтобы начать залив аккаунта.",
        note,
    )
    await message.answer(text, reply_markup=get_categories_keyboard(cats_display))


async def start_item_creation(message: Message, state: FSMContext,
                               category_id: int, category_name: str,
                               user_id: int = None):
    if user_id is None:
        user_id = message.from_user.id

    fields = _build_category_fields(category_id)

    form_data = UserFormData(
        user_id=user_id,
        category_id=category_id,
        category_name=category_name,
        fields={},
        current_field_index=0,
        total_fields=len(fields),
        form_structure={'fields': fields}
    )
    user_forms[user_id] = form_data
    await state.update_data(category_id=category_id, category_name=category_name)
    await ask_field(message, state, form_data)


def _is_json_blob(field: Dict) -> bool:
    return (field.get('extra_key') in ('cookies', 'telegramJson')
            and field.get('cookies_format', 'json') == 'json')


async def ask_field(message: Message, state: FSMContext, form_data: UserFormData):
    fields = form_data.form_structure.get('fields', [])
    idx = form_data.current_field_index

    if idx >= len(fields):
        await show_confirmation(message, state, form_data)
        return

    field = fields[idx]

    if field.get('name') == 'email_login_data' and form_data.fields.get('email_type') == 'force_mail':
        form_data.fields['email_login_data'] = ''
        form_data.current_field_index += 1
        await ask_field(message, state, form_data)
        return

    if field.get('name') == 'guarantee_duration' and form_data.fields.get('email_type') != 'force_mail':
        form_data.fields['guarantee_duration'] = ''
        form_data.current_field_index += 1
        await ask_field(message, state, form_data)
        return

    await state.set_state(ItemCreationStates.filling_fields)

    required = field.get('required', True)
    prompt = ui.step(idx + 1, len(fields), field['label'], required) + "\n\n"

    if field.get('type') == 'choice':
        prompt += "👇 <b>Выберите вариант:</b>"
        kb = get_choice_keyboard(field['choices'])
    elif _is_json_blob(field):
        form_data.cookies_buffer = ''
        placeholder = field.get('placeholder', '')
        if placeholder:
            prompt += f"💡 <i>{html.escape(placeholder)}</i>\n\n"
        prompt += (
            "📥 Пришлите данные <b>одним или несколькими сообщениями</b> "
            "или прикрепите файл <code>.json</code>/<code>.txt</code>.\n"
            "Когда всё отправите — нажмите «✅ Готово»."
        )
        kb = get_cookies_input_keyboard(required=required)
    else:
        placeholder = field.get('placeholder', '')
        if placeholder:
            prompt += f"💡 <i>{html.escape(placeholder)}</i>\n\n"
        prompt += "✍️ <b>Введите значение:</b>"
        kb = get_field_keyboard(required=required)

    await message.answer(prompt, reply_markup=kb)


async def _read_incoming(message: Message) -> Optional[str]:
    if message.text is not None:
        return message.text

    document = getattr(message, 'document', None)
    if document is not None:
        try:
            buf = await message.bot.download(document)
            raw = buf.read() if hasattr(buf, 'read') else buf
            return raw.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"Failed to download cookie file: {e}")
            return None
    return None


async def handle_form_input(message: Message, state: FSMContext):
    user_id = message.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await message.answer("⚠️ Сессия не найдена. Начните заново через /start.")
        return

    fields = form_data.form_structure.get('fields', [])
    idx = form_data.current_field_index
    if idx >= len(fields):
        return

    field = fields[idx]
    if field.get('type') == 'choice':
        await message.answer("⚠️ Пожалуйста, выберите вариант кнопкой выше.")
        return

    if _is_json_blob(field):
        content = await _read_incoming(message)
        if content is None:
            await message.answer(
                "⚠️ Пришлите данные текстом или файлом <code>.json</code>/<code>.txt</code>.",
                reply_markup=get_cookies_input_keyboard(field.get('required', True))
            )
            return

        form_data.cookies_buffer += content
        buffer = form_data.cookies_buffer.strip()

        import json as _json
        try:
            _json.loads(buffer)
            valid = True
        except _json.JSONDecodeError:
            valid = False

        if valid:
            note = (f"✅ Данные получены — символов: <b>{len(buffer)}</b>, корректный JSON.\n"
                    f"Нажмите «✅ Готово», чтобы продолжить (или дошлите ещё).")
        else:
            note = (f"📥 Принято символов: <b>{len(buffer)}</b>.\n"
                    f"Если это ещё не всё — пришлите остаток (сообщением или файлом).\n"
                    f"Когда закончите — нажмите «✅ Готово».")
        await message.answer(note, reply_markup=get_cookies_input_keyboard(field.get('required', True)))
        return

    if message.text is None:
        await message.answer(f"⚠️ Пришлите значение для поля «{field['label']}» текстом.")
        return

    value = message.text.strip()
    validated = await validate_field_input(value, field)
    if validated is None:
        await message.answer(f"⚠️ Некорректное значение для поля «{field['label']}».")
        return

    form_data.fields[field['name']] = validated
    form_data.current_field_index += 1
    await ask_field(message, state, form_data)


async def handle_cookies_done(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await callback.answer("Сессия не найдена. Начните заново через /start.", show_alert=True)
        return

    fields = form_data.form_structure.get('fields', [])
    idx = form_data.current_field_index
    if idx >= len(fields):
        await callback.answer()
        return

    field = fields[idx]
    if not _is_json_blob(field):
        await callback.answer()
        return

    buffer = form_data.cookies_buffer.strip()
    required = field.get('required', True)

    if not buffer:
        if required:
            await callback.answer("Данные ещё не получены. Пришлите их сообщением или файлом.", show_alert=True)
            return
        form_data.fields[field['name']] = ''
        form_data.cookies_buffer = ''
        form_data.current_field_index += 1
        await callback.message.edit_reply_markup(reply_markup=None)
        await ask_field(callback.message, state, form_data)
        await callback.answer()
        return

    import json as _json
    try:
        _json.loads(buffer)
    except _json.JSONDecodeError:
        form_data.cookies_buffer = ''
        await callback.answer(
            "❌ Полученные данные — не корректный JSON. Проверьте и пришлите заново.",
            show_alert=True
        )
        return

    form_data.fields[field['name']] = buffer
    form_data.cookies_buffer = ''
    form_data.current_field_index += 1
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_field(callback.message, state, form_data)
    await callback.answer()


async def validate_field_input(value: str, field: Dict) -> Optional[str]:
    required = field.get('required', True)
    if required and not value:
        return None
    if not value:
        return ''
    if field.get('type') == 'number':
        try:
            num = float(value.replace(',', '.'))
            return None if num < 1 else str(num)
        except ValueError:
            return None
    return value


async def handle_field_skip(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await callback.answer("Сессия не найдена.", show_alert=True)
        return

    fields = form_data.form_structure.get('fields', [])
    idx = form_data.current_field_index
    if idx < len(fields):
        field = fields[idx]
        if field.get('required', True):
            await callback.answer("Это поле обязательно для заполнения.", show_alert=True)
            return
        form_data.fields[field['name']] = ''
        form_data.current_field_index += 1
        if field.get('extra_key') == 'cookies':
            form_data.cookies_buffer = ''

    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_field(callback.message, state, form_data)
    await callback.answer()


async def handle_field_choice(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await callback.answer("Сессия не найдена.", show_alert=True)
        return

    value = callback.data[len('field_choice_'):]
    fields = form_data.form_structure.get('fields', [])
    idx = form_data.current_field_index
    if idx >= len(fields):
        await callback.answer()
        return

    field = fields[idx]
    chosen_label = value
    for _, (val, lbl) in field.get('choices', {}).items():
        if val == value:
            chosen_label = lbl
            break

    form_data.fields[field['name']] = value
    form_data.current_field_index += 1

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Выбрано: <b>{chosen_label}</b>",
        reply_markup=None
    )
    await ask_field(callback.message, state, form_data)
    await callback.answer()


async def show_confirmation(message: Message, state: FSMContext, form_data: UserFormData):
    await state.set_state(ItemCreationStates.confirming)

    fields = form_data.form_structure.get('fields', [])
    rows = [f"🏷 <b>Категория:</b> {html.escape(form_data.category_name)}"]

    for field in fields:
        value = form_data.fields.get(field['name'], '')
        label = html.escape(field['label'])
        if field['name'] == 'email_login_data' and form_data.fields.get('email_type') == 'force_mail':
            rows.append(f"• <b>{label}:</b> 📭 временная почта от маркета")
        elif not value:
            rows.append(f"• <b>{label}:</b> <i>не указано</i>")
        elif field.get('type') == 'choice':
            display = value
            for _, (val, lbl) in field.get('choices', {}).items():
                if val == value:
                    display = lbl
                    break
            rows.append(f"• <b>{label}:</b> {html.escape(str(display))}")
        elif field['name'] in ('login_data', 'email_login_data', 'account_login_data') and ':' in value:
            user_part = value.partition(':')[0]
            rows.append(f"• <b>{label}:</b> {html.escape(user_part)}:●●●●●●")
        elif field['name'] in ('auth_key', 'cookies', 'telegramJson') and len(value) > 20:
            rows.append(f"• <b>{label}:</b> <code>{html.escape(value[:18])}…</code> "
                        f"<i>({len(value)} симв.)</i>")
        else:
            rows.append(f"• <b>{label}:</b> {html.escape(str(value))}")

    text = ui.hub(
        "📋 <b>Проверьте перед публикацией</b>",
        "\n".join(rows),
        "",
        "🔒 <i>Приватные данные скрыты и увидит только покупатель.</i>",
        "Выберите, как опубликовать объявление 👇",
    )
    await message.answer(text, reply_markup=get_publish_options_keyboard())


async def confirm_publish(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await callback.message.edit_text("⚠️ Данные не найдены. Начните заново с /start.")
        await callback.answer()
        return

    close_after = callback.data == 'confirm_publish_closed'
    await state.update_data(close_after=close_after)
    await callback.answer()
    await callback.message.edit_text("⏳ <b>Создаём объявление...</b>")

    try:
        item_data = prepare_item_data(form_data)
        response = await api_client.add_item(item_data)
        item = response.get('item', {})
        item_id = item.get('item_id')

        if not item_id:
            errors = response.get('errors', [str(response)])
            await callback.message.edit_text("❌ <b>Ошибка:</b>\n" + '\n'.join(errors))
            user_forms.pop(user_id, None)
            await state.clear()
            await callback.message.answer("🏠 Главное меню", reply_markup=get_main_menu())
            return

        await state.update_data(pending_item_id=item_id)
        await callback.message.edit_text("⏳ <b>Проверяем аккаунт...</b>")
        await _run_goods_check(callback.message, state, form_data, item_id)

    except Exception as e:
        logger.error(f"Publish error: {e}")
        await callback.message.edit_text(f"❌ <b>Ошибка:</b>\n{e}")
        user_forms.pop(user_id, None)
        await state.clear()
        await callback.message.answer("🏠 Главное меню", reply_markup=get_main_menu())


async def _run_goods_check(message: Message, state: FSMContext,
                            form_data: UserFormData, item_id: int):
    user_id = form_data.user_id
    state_data = await state.get_data()
    close_after = state_data.get('close_after', False)
    try:
        check_data = prepare_check_data(form_data, close_item=close_after)
        status_msg = await message.answer("⏳ <b>Проверяем аккаунт...</b>\n<i>Может занять до нескольких минут</i>")
        await api_client.goods_check(item_id, check_data)
        try:
            await status_msg.delete()
        except Exception:
            pass
        if close_after:
            try:
                await api_client.close_item(item_id)
            except Exception as e:
                logger.error(f"Fallback close_item {item_id}: {e}")

        actual_closed = None
        try:
            info = await api_client.get_item(item_id)
            it = info.get('item', info) if isinstance(info, dict) else {}
            st = it.get('item_state')
            if st == 'closed':
                actual_closed = True
            elif st == 'active':
                actual_closed = False
        except Exception as e:
            logger.error(f"get_item after publish {item_id}: {e}")

        is_closed = actual_closed if actual_closed is not None else close_after
        status_text = "🔒 закрыто" if is_closed else "✅ открыто"
        warn = ""
        if close_after and actual_closed is False:
            warn = ("\n⚠️ <b>Не удалось закрыть автоматически!</b> "
                    "Закройте вручную в 📊 /my → карточка товара → «Закрыть».")
        await message.answer(
            f"✅ <b>Товар опубликован!</b>\n\n"
            f"🆔 ID: <code>{item_id}</code>\n"
            f"📌 Статус: {status_text}{warn}\n"
            f"🔗 https://lzt.market/{item_id}\n\n"
            f"• /my — мои товары\n• /manage — управление"
        )
    except Exception as e:
        logger.error(f"goods/check error: {e}")
        await message.answer(f"❌ <b>Ошибка при проверке аккаунта:</b>\n{e}")

    user_forms.pop(user_id, None)
    await state.clear()
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())


def prepare_item_data(form_data: UserFormData) -> Dict:
    cat_id = form_data.category_id

    data: Dict = {
        'category_id': cat_id,
        'price':       float(form_data.fields.get('price', 1)),
        'currency':    'rub',
        'item_origin': form_data.fields.get('item_origin', 'personal'),
    }

    gd = form_data.fields.get('guarantee_duration', '')
    if gd:
        try:
            data['guarantee_duration'] = int(gd)
        except (ValueError, TypeError):
            pass

    if form_data.fields.get('title'):
        data['title'] = form_data.fields['title']
    if form_data.fields.get('description'):
        data['description'] = form_data.fields['description']

    info_parts = []

    if cat_id == 24:
        pass
    elif cat_id in {9, 12, 18}:
        account_raw = form_data.fields.get('account_login_data', '')
        if account_raw:
            acc_email, _, acc_pass = account_raw.partition(':') if ':' in account_raw else (account_raw, '', '')
            if acc_email: info_parts.append(f"Email аккаунта: {acc_email}")
            if acc_pass:  info_parts.append(f"Пароль: {acc_pass}")
        linked_raw = form_data.fields.get('email_login_data', '')
        if linked_raw:
            l_email, _, l_pass = linked_raw.partition(':') if ':' in linked_raw else (linked_raw, '', '')
            if l_email: info_parts.append(f"Привязанная почта: {l_email}")
            if l_pass:  info_parts.append(f"Пароль от почты: {l_pass}")
    else:
        login_raw = form_data.fields.get('login_data', '')
        if login_raw:
            login, _, password = login_raw.partition(':') if ':' in login_raw else (login_raw, '', '')
            if login:    info_parts.append(f"Логин: {login}")
            if password: info_parts.append(f"Пароль: {password}")
        email_raw = form_data.fields.get('email_login_data', '')
        if email_raw:
            email, _, email_pw = email_raw.partition(':') if ':' in email_raw else (email_raw, '', '')
            if email:    info_parts.append(f"Почта: {email}")
            if email_pw: info_parts.append(f"Пароль от почты: {email_pw}")

    if info_parts:
        data['information'] = '\n'.join(info_parts)

    if cat_id in {9, 12, 18}:
        email_type = form_data.fields.get('email_type', 'native')
        if email_type == 'force_mail':
            data['forceTempEmail'] = True
            data['has_email_login_data'] = False
        else:
            data['email_type'] = email_type
            linked_raw = form_data.fields.get('email_login_data', '')
            if linked_raw:
                data['email_login_data'] = linked_raw
                data['has_email_login_data'] = True
            else:
                data['has_email_login_data'] = False

    if cat_id == 15:
        email_type = form_data.fields.get('email_type', 'native')
        if email_type == 'force_mail':
            data['forceTempEmail'] = True
            data['has_email_login_data'] = False
        else:
            data['email_type'] = email_type
            email_raw = form_data.fields.get('email_login_data', '')
            if email_raw:
                data['email_login_data'] = email_raw
                data['has_email_login_data'] = True
            else:
                data['has_email_login_data'] = False

    return data


def prepare_check_data(form_data: UserFormData, close_item: bool = False) -> Dict:
    cat_id = form_data.category_id
    fields = form_data.form_structure.get('fields', [])

    data: Dict = {}
    extra: Dict = {}

    for field in fields:
        if not field.get('is_extra'):
            continue
        key = field.get('extra_key') or field['name']
        val = form_data.fields.get(field['name'], '')
        if not val:
            continue
        if key == 'dc_id':
            try:
                extra[key] = int(float(val))
            except ValueError:
                pass
        else:
            extra[key] = val

    if cat_id == 24:
        pass

    elif cat_id in {9, 12, 18}:
        account_raw = form_data.fields.get('account_login_data', '')
        email, _, password = account_raw.partition(':') if ':' in account_raw else (account_raw, '', '')
        data['login'] = email
        data['password'] = password
        email_type = form_data.fields.get('email_type', 'native')
        if email_type == 'force_mail':
            data['has_email_login_data'] = False
        else:
            data['email_type'] = email_type
            linked_raw = form_data.fields.get('email_login_data', '')
            if linked_raw:
                data['email_login_data'] = linked_raw
                data['has_email_login_data'] = True
            else:
                data['has_email_login_data'] = False

    elif cat_id == 15:
        email_type = form_data.fields.get('email_type', 'native')
        if email_type == 'force_mail':
            data['has_email_login_data'] = False
        else:
            email_raw = form_data.fields.get('email_login_data', '')
            email, _, password = email_raw.partition(':') if ':' in email_raw else (email_raw, '', '')
            data['login'] = email
            data['password'] = password
            data['email_type'] = email_type

    else:
        login_raw = form_data.fields.get('login_data', '')
        if ':' in login_raw:
            login, _, password = login_raw.partition(':')
        else:
            login, password = login_raw, ''
        data['login'] = login
        data['password'] = password

        email_raw = form_data.fields.get('email_login_data', '')
        if email_raw:
            email, _, email_pw = email_raw.partition(':') if ':' in email_raw else (email_raw, '', '')
            if email:    data['email'] = email
            if email_pw: data['email_password'] = email_pw

    extra['close_item'] = bool(close_item)
    data['extra'] = extra

    return data


async def cancel_publish(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_forms.pop(user_id, None)
    await state.clear()
    await callback.message.edit_text("❌ <b>Создание товара отменено.</b>")
    await callback.message.answer("🏠 <b>Главное меню</b>", reply_markup=get_main_menu())
    await callback.answer()


async def edit_item_form(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    form_data = user_forms.get(user_id)
    if not form_data:
        await callback.answer("Данные не найдены. Начните заново с /start.", show_alert=True)
        return
    form_data.current_field_index = 0
    form_data.fields = {}
    await callback.message.edit_text("✏️ <b>Начнём заполнение заново.</b>")
    await ask_field(callback.message, state, form_data)
    await callback.answer()
