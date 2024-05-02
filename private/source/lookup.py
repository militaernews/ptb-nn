from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext

from config import GROUP_SOURCE
from data.db import get_source


async def lookup(update: Update, context: CallbackContext):
    print(update.message.sender_chat)
    #  await update.message.reply_text(update.message.caption_html_urled,parse_mode=None)

    sender_chat = update.message.sender_chat
    source_id = sender_chat.id

    await update.message.reply_text(f"Quelle: {source_id} - {sender_chat.username}")

    if sender_chat.id is None:
        return await update.message.reply_text("fwd-chat-id is none")

    if sender_chat.type != ChatType.CHANNEL:
        return await update.message.reply_text("Ich habe nur Kanäle gespeichert.")

    result = await get_source(source_id)

    if result is None:
        await context.bot.send_message(GROUP_SOURCE,
                                       f"‼️ Neue Quelle\n\nchannel_id: <code>{source_id}</code>\n\nchannel_name: <code>{sender_chat.title}</code>\n\nusername: <code>{update.message.forward_from_chat.username}</code>")
        await update.message.forward(GROUP_SOURCE)

        await update.message.reply_text(
            f"Tut mir leid. Eine Quelle mit der ID <code>{source_id}</code> ist nicht in meiner Datenbank hinterlegt.")
        return

    await update.message.reply_text(
        f"Quelle mit der ID <code>{source_id}</code> gefunden!\n\n{result.username} {result.bias} {result.display_name}")
