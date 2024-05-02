from asyncio import run

from config import CHANNEL_UA_RU, NX_MEME
from data.db import get_footer_by_channel_id

FOOTER_MEME: str = run(get_footer_by_channel_id(NX_MEME))
FOOTER_UA_RU: str = run(get_footer_by_channel_id(CHANNEL_UA_RU))
FOOTER = '\n――――――――――――\n\n<b>Verpasse nichts zum Ukrainekrieg mit unserem Newsticker!</b>!\n👉 https://t.me/+tUVB94nMmH85NmQy'
