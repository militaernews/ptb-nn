from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters

from data import db
from data.db import get_source
from private.common import cancel_handler, text_filter

ADD_PATTERN_SOURCE, NEW_PATTERN, SAVE_PATTERN = range(3)


async def add_pattern(update: Update, context: CallbackContext) -> int:
    context.chat_data["new_pattern"] = None
    context.chat_data["pattern_source_id"] = None

    await update.message.reply_text(
        "Bitte leite mir nun eine Nachricht des Kanals mit dem hinzuzufügenden Footer-pattern weiter.")
    return ADD_PATTERN_SOURCE


async def add_pattern_source(update: Update, context: CallbackContext) -> int | None:
    if update.message.forward_from_chat.id is None:
        await update.message.reply_text("fwd-chat-id is none")
        return ConversationHandler.END

    if update.message.forward_from_chat.type != update.message.forward_from_chat.CHANNEL:
        await update.message.reply_text("Ich habe nur Kanäle gespeichert.")
        return ConversationHandler.END

    source_id = update.message.forward_from_chat.id

    result = get_source(source_id)

    if result is None:
        await update.message.reply_text(
            f"Tut mir leid. Eine Quelle mit der ID <code>{source_id}</code> ist nicht in meiner Datenbank hinterlegt. Mit /add_source kannst du einen Kanal hinzufügen.")
        return ConversationHandler.END

    text = update.message.caption_html_urled or update.message.text_html_urled

    context.chat_data["pattern_source_id"] = source_id

    await update.message.reply_text(
        f"Quelle: {source_id} - {update.message.forward_from_chat.username}\n\nBitte sende mir nun das Pattern. Kopiere es aus der folgenden Nachricht oder schreibe Regex.")
    await update.message.reply_text(text, parse_mode=None)
    return NEW_PATTERN


async def new_pattern(update: Update, context: CallbackContext) -> int:
    context.chat_data["new_pattern"] = update.message.text_html_urled
    await update.message.reply_text(
        f"Neues Pattern für Quelle {context.chat_data['pattern_source_id']}:\n\n"
        f"{update.message.text_html_urled}\n\n"
        "Passt das so?\n\n"
        "Mit /save kannst du dieses Pattern hinzufügen, mit /cancel das ganze abbrechen.",
        parse_mode=None
    )
    return SAVE_PATTERN


async def save_pattern(update: Update, context: CallbackContext) -> int:

    db.set_pattern(context.chat_data["pattern_source_id"], context.chat_data["new_pattern"])
    return ConversationHandler.END


add_pattern_handler = ConversationHandler(
        entry_points=[CommandHandler("add_pattern", add_pattern)],
        states={
            ADD_PATTERN_SOURCE: [MessageHandler(filters.FORWARDED, add_pattern_source)],
            NEW_PATTERN: [MessageHandler(text_filter, new_pattern)],
            SAVE_PATTERN: [
                CommandHandler("save",  save_pattern)
            ],

        },
        fallbacks=cancel_handler,
    )