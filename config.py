import json
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM = os.getenv('TELEGRAM')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMINS = json.loads(os.getenv('ADMINS'))

CHANNEL_MEME = -1001486678205
NX_MEME = -1001482614635
NX_MAIN = -1001839268196
GROUP_UA = -1001845172955

LOG_GROUP = -1001739784948
ADMIN_GROUP = -1001723195485

GROUPS = (
    -1001845172955,  # Ukraine
    -1001888944217,  # Afrika
    -1001263239083  # ukrger
)

FOOTER = '\n\n<b>Verbinde dich mit weiteren Unterstützern</b>!\n👉🏼 <a href="https://t.me/ukr_ger">Deutsch 🤝 Ukraine️</a>'

GROUP_SOURCE = -1001694922864

CHANNEL_UA_RU = -1001640548153

MSG_REMOVAL_PERIOD = 1200
