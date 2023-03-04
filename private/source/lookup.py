from telegram import Update
from telegram.ext import CallbackContext

from config import GROUP_SOURCE
from data.db import get_source


async def lookup(update: Update, context: CallbackContext):
    print(update.message.forward_from_chat)
  #  await update.message.reply_text(update.message.caption_html_urled,parse_mode=None)

    source_id = update.message.forward_from_chat.id

    await update.message.reply_text(f"Quelle: {source_id} - {update.message.forward_from_chat.username}")

    if update.message.forward_from_chat.id is None:
        return await update.message.reply_text("fwd-chat-id is none")

    if update.message.forward_from_chat.type != update.message.forward_from_chat.CHANNEL:
        return await update.message.reply_text("Ich habe nur Kanäle gespeichert.")

    result = get_source(source_id)

    if result is None:
        await context.bot.send_message(GROUP_SOURCE, f"‼️ Neue Quelle\n\nchannel_id: <code>{source_id}</code>\n\nchannel_name: <code>{update.message.forward_from_chat.title}</code>\n\nusername: <code>{update.message.forward_from_chat.username}</code>")
        await update.message.forward(GROUP_SOURCE)

        await update.message.reply_text(
            f"Tut mir leid. Eine Quelle mit der ID <code>{source_id}</code> ist nicht in meiner Datenbank hinterlegt.")
        return

    await update.message.reply_text(
        f"Quelle mit der ID <code>{source_id}</code> gefunden!\n\n{result.username} {result.bias} {result.display_name}")
