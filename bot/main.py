import logging
from datetime import datetime, timedelta
from os import path, makedirs
from typing import Final
from warnings import filterwarnings

from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, ChatJoinRequestHandler, \
    InlineQueryHandler, CallbackQueryHandler
from telegram.warnings import PTBUserWarning

from private import setup
from private.advertisement import register_advertisement
# from channel.crawl_tweet import PATTERN_TWITTER, handle_twitter
from channel.loss_osint import get_osint_losses, setup_osint_crawl
from channel.loss_uamod import get_uamod_losses, setup_uamod_crawl
from channel.meme import register_meme
from channel.ukraine_russia import register_ua_ru
from data.db import get_destination_ids, get_accounts
from group.bingo import bingo_field, reset_bingo
from group.command import admin, inline_query, unwarn_user, warn_user, report_user, register_commands
from group.dictionary import handle_other_chats
from private.feedback import fwd, respond_feedback
from private.join_request import join_request_buttons, join_request_ug, accept_rules_ug, decline_request_ug, \
    accept_request_ug
from private.pattern import add_pattern_handler
from settings.config import TELEGRAM, ADMINS, ADMIN_GROUP, CONTAINER, UG_LZ, ADMIN_GROUPS
from source.add import add_source_handler, handle_join
from source.edit import edit_source_handler
from source.lookup import lookup


def add_logging():
    filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

    if CONTAINER:
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",

            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.StreamHandler(),
                #     logging.FileHandler('logs/log')
            ]
        )

    else:
        log_filename: Final[str] = rf"../logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
        makedirs(path.dirname(log_filename), exist_ok=True)
        logging.basicConfig(
            format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
            encoding="utf-8",
            filename=log_filename,
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    app = ApplicationBuilder().token(TELEGRAM).defaults(
        Defaults(parse_mode=ParseMode.HTML)) \
        .read_timeout(15).get_updates_read_timeout(50) \
        .build()

    #  .persistence(PicklePersistence(filepath="persistence")) \

    app.add_handler(CommandHandler("setup", setup, filters.Chat(ADMINS)))

    app.add_handler(
        ChatJoinRequestHandler(callback=join_request_buttons, chat_id=get_destination_ids(), block=False))
    app.add_handler(ChatJoinRequestHandler(callback=join_request_ug, chat_id=UG_LZ, block=False))
    app.add_handler(CallbackQueryHandler(accept_rules_ug, r"ugreq_\d+"))
    app.add_handler(CallbackQueryHandler(accept_request_ug, r"ugyes_\d+_\d+"))
    app.add_handler(CallbackQueryHandler(decline_request_ug, r"ugno_\d+_\d+"))

    register_meme(app)
    register_ua_ru(app)
    register_advertisement(app)
    register_commands(app)

    app.add_handler(InlineQueryHandler(inline_query))

    app.add_handler(add_source_handler)
    app.add_handler(edit_source_handler)
    app.add_handler(add_pattern_handler)

    for account in get_accounts().values():
        app.add_handler(CommandHandler("join", handle_join, filters.Chat(account.user_id), has_args=True))

    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, lookup))

    app.add_handler(MessageHandler(filters.Chat(chat_id=ADMIN_GROUPS.keys()) & filters.Regex("^@admin"), admin))

    #  app.add_handler(MessageHandler(filters.Regex(YT_PATTERN) & ~filters.ChatType.CHANNEL, get_youtube_video))

    app.add_handler(CommandHandler("bingo", bingo_field, filters.User(ADMINS)))
    app.add_handler(CommandHandler("reset_bingo", reset_bingo, filters.Chat(ADMINS)))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.User(
            ADMINS) & ~filters.IS_AUTOMATIC_FORWARD & filters.UpdateType.MESSAGE,
                       handle_other_chats))
    app.add_handler(CommandHandler("warn", warn_user))
    app.add_handler(CommandHandler("unwarn", unwarn_user))
    app.add_handler(CommandHandler("tartaros", report_user))

    app.add_handler(CommandHandler("crawl_uamod", setup_uamod_crawl))
    app.add_handler(CommandHandler("crawl_osint", setup_osint_crawl))
    app.job_queue.run_repeating(get_uamod_losses, timedelta(hours=0.5))
    app.job_queue.run_repeating(get_osint_losses, timedelta(days=7))

    # feedback
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.VIDEO | filters.ANIMATION | filters.PHOTO) & filters.ChatType.PRIVATE & ~filters.User(
            ADMINS), fwd))
    app.add_handler(MessageHandler(filters.REPLY & filters.Chat(ADMIN_GROUP),
                                   respond_feedback))

    print("### Run Local ###")
    app.run_polling(poll_interval=1)


if __name__ == "__main__":
    add_logging()
    main()
