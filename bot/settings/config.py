import json
import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv()

TELEGRAM = os.getenv('TELEGRAM')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMINS = json.loads(os.getenv('ADMINS'))

# Base URL of the mix-sv frontend (Vercel deployment), used for the WebApp
# "Edit in mix-sv" / "Create in mix-sv" buttons in source/edit.py and
# source/add.py. Those buttons are hidden when this isn't set.
MIX_SV_URL = os.getenv('MIX_SV_URL', '').rstrip('/')

NX_MEME = -1001482614635
NX_MAIN = -1001839268196

LOG_GROUP_ID = int(os.getenv('LOG_GROUP_ID', -1001338514957))
LOG_GROUP = LOG_GROUP_ID
THREAD_ID = int(os.getenv('THREAD_ID', 478))  # PTB-NN topic
ADMIN_GROUP = -1001723195485

UG_ADMINS = json.loads(os.getenv('UG_ADMINS'))
UG_LZ = -1001263239083
UG_CHANNEL = -1001777893083
UG_ADMIN = -802186561

GROUP_SOURCE = -1001694922864

CHANNEL_UA_RU = -1001640548153
GROUP_UA_RU = -1001618190222

MSG_REMOVAL_PERIOD = 1200

ADMIN_GROUPS = {
    -1001845172955: ADMIN_GROUP,  # NN_UA
    -1001888944217: ADMIN_GROUP,  # NN_AFRIKA - still present?
    UG_LZ: UG_ADMIN,  # UKR_GER
    -1001618190222: -1001895565760,  # UA_Krieg
    -1002104916595: ADMIN_GROUP,  # Israel
}

CONTAINER: Final[bool] = bool(os.getenv('CONTAINER', False), )

# Absolute path to bot/res, resolved from this file's location rather than a
# "./res" relative path. The container runs "python -m bot.main" with
# WorkingDir=/, so a relative path resolved to the nonexistent /res instead
# of /bot/res - silently breaking every font/image/string lookup that goes
# through RES_PATH (e.g. crawl_osint's chart lost its coat-of-arms images
# and all text, since resvg had no fonts and no images to find).
RES_PATH: Final[str] = str(Path(__file__).resolve().parent.parent / "res")
