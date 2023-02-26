import datetime
import logging
import os

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, Defaults, ApplicationBuilder, filters, CommandHandler, PicklePersistence, \
    ConversationHandler, CallbackContext, ChatJoinRequestHandler, CallbackQueryHandler

import config
from channel.meme import post_media_meme_nx, post_text_meme_nx
from config import NX_MEME, TELEGRAM, ADMINS, NX_MAIN
from group.command import donbass, maps, loss, peace, genozid, stats, setup, support, channels, admin
from private.join_request import join_request_buttons, accept_join_request
from private.pattern import save_pattern, new_pattern, add_pattern_source, add_pattern, ADD_PATTERN_SOURCE, NEW_PATTERN, \
    SAVE_PATTERN
from private.sources import lookup

LOG_FILENAME = r'C:\Users\Pentex\PycharmProjects\ptb-nyx-news\logs\log-' + f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.out"
if not os.path.exists(LOG_FILENAME):
    open(LOG_FILENAME, "w")
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)s - %(funcName)20s()]: %(message)s ",
    level=logging.INFO, filename=LOG_FILENAME
)


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Konversation gecancelt.")
    return ConversationHandler.END


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM).defaults(
        Defaults(parse_mode=ParseMode.HTML, disable_web_page_preview=True)) \
        .persistence(PicklePersistence(filepath="persistence")) \
        .build()

    app.add_handler(ChatJoinRequestHandler(callback=join_request_buttons,  block=False))
    app.add_handler(CallbackQueryHandler(accept_join_request, pattern="join"))

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST &
            (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
            & filters.Chat(chat_id=NX_MEME), post_media_meme_nx))
    app.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST & filters.TEXT & filters.Chat(chat_id=NX_MEME),
                       post_text_meme_nx))

    app.add_handler(CommandHandler("maps", maps))
    app.add_handler(CommandHandler("donbass", donbass))
    app.add_handler(CommandHandler("loss", loss))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("peace", peace))
    app.add_handler(CommandHandler("channels", channels))
    app.add_handler(CommandHandler("support", support))
    app.add_handler(CommandHandler("genozid", genozid))

    app.add_handler(CommandHandler("setup", setup, filters.Chat(chat_id=ADMINS)))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_pattern", add_pattern)],
        states={
            ADD_PATTERN_SOURCE: [MessageHandler(filters.FORWARDED, add_pattern_source)],
            NEW_PATTERN: [MessageHandler(filters.TEXT, new_pattern)],
            SAVE_PATTERN: [
                MessageHandler(filters.Regex("Speichern"), save_pattern),
                MessageHandler(filters.Regex("Überarbeiten"), new_pattern)
            ],

        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, lookup))

    app.add_handler(MessageHandler(filters.Chat(chat_id=config.GROUP_UA) & filters.Regex("@admin"), admin))

    print("### Run Local ###")
    app.run_polling()
