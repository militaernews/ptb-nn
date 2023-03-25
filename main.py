import logging
import os
from datetime import datetime
from warnings import filterwarnings

from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    ChatJoinRequestHandler
from telegram.warnings import PTBUserWarning

import config
from channel.crawl_api import setup_crawl
from channel.meme import post_media_meme_nx, post_text_meme_nx
from channel.ukraine_russia import append_footer, append_footer_text
from config import NX_MEME, TELEGRAM, ADMINS
from data.db import get_destination_ids
from group.bingo import bingo_field, reset_bingo
from group.command import donbass, maps, loss, peace, genozid, stats, setup, support, channels, admin, short, cia, \
    mimimi, sofa, bot
from group.dictionary import handle_other_chats
from private.join_request import join_request_buttons
from private.pattern import add_pattern_handler
from private.source.add import add_source_handler
from private.source.edit import edit_source_handler
from private.source.lookup import lookup

filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

LOG_FILENAME = rf"./logs/{datetime.now().strftime('%Y-%m-%d')}/{datetime.now().strftime('%H-%M-%S')}.log"
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)
logging.basicConfig(
    format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
    encoding="utf-8",
    filename=LOG_FILENAME,
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM).defaults(
        Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)) \
        .persistence(PicklePersistence(filepath="persistence")) \
        .build()

    app.add_handler(ChatJoinRequestHandler(callback=join_request_buttons, chat_id=get_destination_ids(), block=False))

    filter_media =(filters.PHOTO | filters.VIDEO | filters.ANIMATION)

    filter_meme = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=NX_MEME) & ~filters.FORWARDED
    app.add_handler(
        MessageHandler(filter_meme & filter_media, post_media_meme_nx))
    app.add_handler(MessageHandler(filter_meme & filters.TEXT, post_text_meme_nx))

    filter_ru_ua = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=config.CHANNEL_UA_RU) & ~filters.FORWARDED
    app.add_handler(MessageHandler(filter_ru_ua & filter_media, append_footer))
    app.add_handler(MessageHandler(filter_ru_ua & filters.TEXT, append_footer_text))

    app.add_handler(CommandHandler("maps", maps))
    app.add_handler(CommandHandler("donbass", donbass))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("short", short))
    app.add_handler(CommandHandler("peace", peace))
    app.add_handler(CommandHandler("channels", channels))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("genozid", genozid))

    app.add_handler(CommandHandler("sofa", sofa))
    app.add_handler(CommandHandler("bot", bot))
    app.add_handler(CommandHandler("mimimi", mimimi))
    app.add_handler(CommandHandler("cia", cia))

    app.add_handler(CommandHandler("setup", setup, filters.Chat(ADMINS)))
    app.add_handler(CommandHandler("crawl", setup_crawl, filters.Chat(ADMINS)))

    app.add_handler(add_source_handler)
    app.add_handler(edit_source_handler)
    app.add_handler(add_pattern_handler)

    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, lookup))

    app.add_handler(MessageHandler(filters.Chat(chat_id=config.GROUPS) & filters.Regex("^@admin"), admin))

    app.add_handler(CommandHandler("bingo", bingo_field, filters.User(ADMINS)))
    app.add_handler(CommandHandler("reset_bingo", reset_bingo, filters.Chat(ADMINS)))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.User(ADMINS) & ~filters.IS_AUTOMATIC_FORWARD,
                       handle_other_chats))

    print("### Run Local ###")
    app.run_polling()
