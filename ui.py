BRAND = "🟢 <b>LZT MARKET</b>"

DIV = "───────────────"


def hub(title: str, *lines: str) -> str:
    body = "\n".join(l for l in lines if l is not None)
    head = f"{BRAND}\n{DIV}\n{title}"
    return f"{head}\n\n{body}" if body else head


def step(index: int, total: int, label: str, required: bool) -> str:
    mark = "🔴 обязательно" if required else "⚪️ можно пропустить"
    return f"📝 <b>Шаг {index}/{total}</b> · {mark}\n<b>{label}</b>\n{DIV}"


BUTTON_STYLES = True

SUCCESS = 'success'
DANGER  = 'danger'
PRIMARY = 'primary'

CUSTOM_EMOJI: dict = {
    'create':   '5893255507380014983',
    'my_items': '5893321843149902412',
    'manage':   '5893161718179173515',
    'profile':  '5902335789798265487',
    'price':    '5893473283696759404',
    'delete':   '5904542823167824187',
    'export':   '5902449142575141204',
}


def btn_extra(emoji_key: str = None, style: str = None) -> dict:
    kw = {}
    if BUTTON_STYLES and style:
        kw['style'] = style
    cid = CUSTOM_EMOJI.get(emoji_key) if emoji_key else None
    if cid:
        kw['icon_custom_emoji_id'] = cid
    return kw


def te(emoji_key: str, fallback: str) -> str:
    cid = CUSTOM_EMOJI.get(emoji_key)
    return f'<tg-emoji emoji-id="{cid}">{fallback}</tg-emoji>' if cid else fallback
