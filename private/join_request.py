import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import CallbackContext

import config


async def join_request_buttons(update: Update, context: CallbackContext):
    with open("res/how.html", "r", encoding='utf-8') as f:
        text = f.read()

    await update.chat_join_request.from_user.send_photo(
        open("res/nn_info.jpg", "rb"),
        caption=(f"Hey {update.chat_join_request.from_user.name} ✌🏼\n\n{text}\n\n<b>Bitte bestätige deinen Beitritt</b> 😉"),
        reply_markup=InlineKeyboardMarkup.from_button(
           InlineKeyboardButton("Kanal beitreten ✅",
                                 callback_data="join")
        )
   )


async def accept_join_request(update: Update, context: CallbackContext):
    with open("res/how.html","r", encoding='utf-8') as f:
        text = f.read()

    try:
        await context.bot.approve_chat_join_request(config.NX_MAIN, update.effective_user.id)
    except Exception as e:
        logging.error(e)
        pass
    share_text = "\n🚨 Nyx News — Aggregierte Nachrichten aus aller Welt mit Quellenangabe und gekennzeichneter Voreingenommenheit der Quelle."
    await update.callback_query.edit_message_caption(f"{text}\n\n<b>Herzlich Willkommen! Bitte teile Nyx News mit deinen Kontakten</b> 😊",
                                                  reply_markup=InlineKeyboardMarkup.from_button(
                                                      InlineKeyboardButton("Kanal teilen ⏩",url=f"https://t.me/share/url?url=https://t.me/nyx_news&text={share_text}")))
    await update.callback_query.answer()


