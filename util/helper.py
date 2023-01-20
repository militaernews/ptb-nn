from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from config import MSG_REMOVAL_PERIOD, LOG_GROUP


async def delete(context: CallbackContext):
    await context.bot.delete_message(str(context.job.context), context.job.name)


async def reply_html(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        print("needs admin:", e)
        pass

    try:
        with open(f"res/{file_name}.html", "r", encoding='utf-8') as f:
            text = f.read()
            if update.message.reply_to_message is not None:
                msg = await update.message.reply_to_message.reply_text(text)
            else:
                msg = await context.bot.send_message(update.message.chat_id, text)

            context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, msg.chat_id, str(msg.message_id))

    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass


async def reply_photo(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except  TelegramError as e:
        print("needs admin:", e)
        pass

    try:
        with open(f"res/img/{file_name}", "rb") as f:
            if update.message.reply_to_message is not None:
                msg = await update.message.reply_to_message.reply_photo(f)
            else:
                msg = await context.bot.send_photo(update.message.chat_id, f)

            context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, msg.chat_id, str(msg.message_id))


    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass
