from telegram import Update
from telegram.ext import CallbackContext

from data.db import get_source


async def lookup(update: Update, context: CallbackContext):
    print(update.message.forward_from_chat)

    source_id = update.message.forward_from_chat.id

    await update.message.reply_text(f"Quelle: {source_id} - {update.message.forward_from_chat.username}")

    if update.message.forward_from_chat.id is None:
        return await update.message.reply_text("fwd-chat-id is none")

    result = get_source(source_id)

    if result is None:
        return await update.message.reply_text(
            f"Eine Quelle mit ID {source_id} ist nicht in meiner Datenbank hinterlegt.")
    # todo: save source that is not present yet

    await update.message.reply_text(
        f"Quelle mit ID {source_id} gefunden!\n\n{result.username} {result.bias} {result.display_name}")
