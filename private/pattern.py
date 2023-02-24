from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from data import db

ADD_PATTERN_SOURCE, NEW_PATTERN, SAVE_PATTERN = range(3)


async def add_pattern(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(  "Bitte leite mir nun eine Nachricht des Kanals mit dem hinzuzufügenden Footer-pattern weiter.")
    return ADD_PATTERN_SOURCE


async def add_pattern_source(update: Update, context: CallbackContext) -> int | None:
    if update.message.forward_from_chat.id is None:
        await update.message.reply_text("fwd-chat-id is none")
        return

    if update.message.forward_from_chat.type != update.message.forward_from_chat.CHANNEL:
        await update.message.reply_text("Ich habe nur Kanäle gespeichert.")
        return

    source_id = update.message.forward_from_chat.id

    text = update.message.caption_html_urled or update.message.text_html_urled

    context.chat_data["pattern_source_id"] = source_id

    await update.message.reply_text(
        f"Quelle: {source_id} - {update.message.forward_from_chat.username}\n\nBitte sende mir nun das Pattern. Kopiere es aus der folgenden Nachricht oder schreibe Regex.")
    await update.message.reply_text(text, parse_mode=None)
    return NEW_PATTERN


async def new_pattern(update: Update, context: CallbackContext) -> int:
    context.chat_data["new_pattern"] = update.message.text_html_urled
    await update.message.reply_text(
        f"Neues Pattern für Quelle {context.chat_data['pattern_source_id']}:\n\n{update.message.text_html_urled}\n\nPasst das so?",
        parse_mode=None, reply_markup=ReplyKeyboardMarkup(
            [["Speichern"], ["Überarbeiten"]],
            resize_keyboard=True,
            one_time_keyboard=True))
    return SAVE_PATTERN


async def save_pattern(update: Update, context: CallbackContext) -> int:
    db.set_pattern(context.chat_data["pattern_source_id"], context.chat_data["new_pattern"])
    return ConversationHandler.END
