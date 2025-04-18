from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes

from bot.settings.config import ADMINS
from bot.data.db import get_source, set_pattern
from bot.private.common import cancel_handler, text_filter

PATTERN = "new_pattern"
PATTERN_SOURCE_ID = 'pattern_source_id'

ADD_PATTERN_SOURCE, NEW_PATTERN, SAVE_PATTERN = range(3)


async def add_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data["new_pattern"] = None
    context.chat_data["pattern_source_id"] = None

    await update.message.reply_text(
        "Bitte leite mir nun eine Nachricht des Kanals mit dem hinzuzufügenden Footer-pattern weiter.")
    return ADD_PATTERN_SOURCE


async def add_pattern_source(update: Update, context: CallbackContext) -> int | None:
    if not (sender_chat_id := update.message.sender_chat.id):
        await update.message.reply_text("fwd-chat-id is none")
        return ConversationHandler.END

    if update.message.sender_chat.type != ChatType.CHANNEL:
        await update.message.reply_text("Ich kenne nur Kanäle.")
        return ConversationHandler.END

    if not (result := get_source(sender_chat_id)):
        await update.message.reply_text(
            f"Tut mir leid. Eine Quelle mit der ID <code>{sender_chat_id}</code> ist nicht in meiner Datenbank hinterlegt. Mit /add_source kannst du einen Kanal hinzufügen.")
        return ConversationHandler.END

    text = update.message.caption_html_urled or update.message.text_html_urled

    context.chat_data[PATTERN_SOURCE_ID] = sender_chat_id

    await update.message.reply_text(
        f"Quelle: {sender_chat_id} - {update.message.sender_chat.username}\n\nBitte sende mir nun das Pattern. Kopiere es aus der folgenden Nachricht oder schreibe Regex.\n{text}",
        parse_mode=None)
    return NEW_PATTERN


async def new_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pattern_text = update.message.text
    context.chat_data[PATTERN] = pattern_text
    await update.message.reply_text(
        f"Neues Pattern für Quelle {context.chat_data[PATTERN_SOURCE_ID]}:\n\n"
        f"{pattern_text}\n\n"
        "Passt das so?\n\n"
        "Mit /save kannst du dieses Pattern hinzufügen, mit /cancel das ganze abbrechen.",
        parse_mode=None
    )
    return SAVE_PATTERN


async def save_pattern(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    set_pattern(context.chat_data[PATTERN_SOURCE_ID], context.chat_data[PATTERN])
    await update.message.reply_text(
        f"Pattern für Quelle <code>{context.chat_data[PATTERN_SOURCE_ID]}</code> hinzugefügt."
    )
    return ConversationHandler.END


add_pattern_handler = ConversationHandler(
    entry_points=[CommandHandler("add_pattern", add_pattern, filters=filters.Chat(ADMINS))],
    states={
        ADD_PATTERN_SOURCE: [MessageHandler(filters.FORWARDED, add_pattern_source)],
        NEW_PATTERN: [MessageHandler(text_filter, new_pattern)],
        SAVE_PATTERN: [
            CommandHandler("save", save_pattern)
        ],
    },
    fallbacks=cancel_handler
)
