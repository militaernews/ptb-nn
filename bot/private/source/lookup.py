from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext

from bot.config import GROUP_SOURCE
from bot.data.db import get_source


async def lookup(update: Update, context: CallbackContext):
    sender_chat = update.message.sender_chat
    print(sender_chat)

    await update.message.reply_text(f"Quelle: {sender_chat.id} - {sender_chat.username}")

    if sender_chat.type != ChatType.CHANNEL:
        return await update.message.reply_text("Ich habe nur Kanäle gespeichert.")

    result = get_source(sender_chat.id)

    if result is None:
        await context.bot.send_message(GROUP_SOURCE,
                                       f"‼️ Neue Quelle\n\nchannel_id: <code>{sender_chat.id}</code>\n\nchannel_name: <code>{sender_chat.title}</code>\n\nusername: <code>{update.message.sender_chat.username}</code>")
        await update.message.forward(GROUP_SOURCE)
        return await update.message.reply_text(
            f"Tut mir leid. Eine Quelle mit der ID <code>{sender_chat.id}</code> ist nicht in meiner Datenbank hinterlegt.")

    await update.message.reply_text(
        f"Quelle mit der ID <code>{sender_chat.id}</code> gefunden!\n\n{result.username} {result.bias} {result.display_name}")
