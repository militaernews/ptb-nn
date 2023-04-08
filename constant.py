from config import CHANNEL_UA_RU, NX_MEME
from data.db import get_footer_by_channel_id

FOOTER_MEME = get_footer_by_channel_id(NX_MEME)
FOOTER_UA_RU = get_footer_by_channel_id(CHANNEL_UA_RU)
FOOTER = '\n\n<b>Verbinde dich mit weiteren Unterstützern</b>!\n👉🏼 <a href="https://t.me/ukr_ger">Deutsch 🤝 Ukraine️</a>'