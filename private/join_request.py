import logging
import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from util.helper import get_text2
from util.regex import JOIN_ID


async def join_request_buttons(update: Update, context: CallbackContext):

    print("join: ", update.chat_join_request)

    share_text = "\n🚨 Nyx News — Aggregierte Nachrichten aus aller Welt mit Quellenangabe und gekennzeichneter Voreingenommenheit der Quelle."

    try:
        await context.bot.approve_chat_join_request(update.chat_join_request.chat.id, update.effective_user.id)

        await update.chat_join_request.from_user.send_photo(
            open("res/nn_info.jpg", "rb"),
            caption=(
                f"Herzlich Willkommen, {update.chat_join_request.from_user.name} ✌🏼\n\n{get_text2(update.chat_join_request.from_user,'how')}"),
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton("Kanal teilen ⏩",
                                     url=f"https://t.me/share/url?url=https://t.me/nyx_news&text={share_text}")))
    except Exception as e:
        logging.error(e)
        pass


async def accept_join_request(update: Update, context: CallbackContext):

    print(update.callback_query)

    chat_id = re.findall(JOIN_ID, update.callback_query.data)[0]

    try:
        await context.bot.approve_chat_join_request(chat_id, update.effective_user.id)
    except Exception as e:
        logging.error(e)
        pass
    share_text = "\n🚨 Nyx News — Aggregierte Nachrichten aus aller Welt mit Quellenangabe und gekennzeichneter Voreingenommenheit der Quelle."
    await update.callback_query.edit_message_caption(
        f"{get_text2(update.callback_query.from_user,'how')}\n\n<b>Herzlich Willkommen! Bitte teile Nyx News mit deinen Kontakten</b> 😊",
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton("Kanal teilen ⏩",
                                 url=f"https://t.me/share/url?url=https://t.me/nyx_news&text={share_text}")))
    await update.callback_query.answer()
