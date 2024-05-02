import base64
import logging
import os.path

from resvg_py import svg_to_base64
from telegram import Update, User
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from config import MSG_REMOVAL_PERIOD, LOG_GROUP
from constant import FOOTER

CHAT_ID = "chat_id"
MSG_ID = "msg_id"


async def delete(context: CallbackContext):
    await context.bot.delete_message(context.job.data[CHAT_ID], context.job.data[MSG_ID])


def get_text2(from_user: User, filename: str) -> str:
    code = from_user.language_code or "de"
    print(from_user.language_code, code)

    path = f"res/strings/{code}/{filename}.html"

    if not os.path.exists(path):
        path = f"res/strings/de/{filename}.html"

    with open(path, "r", encoding='utf-8') as f:
        return f.read()


def get_text(update: Update, filename: str) -> str:
    return get_text2(update.message.from_user, filename)


async def reply_html_greet(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        print("needs admin:", e)
        pass

    try:

        text = f'{get_text(update, file_name)}'.format(update.message.from_user.name)

        await context.bot.send_message(update.message.chat_id, text)

    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file mention {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass


async def reply_html(update: Update, context: CallbackContext, file_name: str):
    try:
        await update.message.delete()
    except TelegramError as e:
        print("needs admin:", e)
        pass

    try:

        text = f'{get_text(update, file_name)}\n{FOOTER}'

        print(text)

        if update.message.reply_to_message is not None:
            if update.message.reply_to_message.from_user.first_name == "Telegram":
                msg = await update.message.reply_text(text)

            else:
                msg = await update.message.reply_to_message.reply_text(text)
        else:
            msg = await context.bot.send_message(update.message.chat.id, text)

        context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, {CHAT_ID: msg.chat.id, MSG_ID: msg.message_id})

    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass


async def reply_photo(update: Update, context: CallbackContext, file_name: str, caption: str = None):
    try:
        await update.message.delete()
    except  TelegramError as e:
        print("needs admin:", e)
        pass

    if caption is not None:
        try:
            caption = get_text(update, caption)
        except Exception as e:
            await context.bot.send_message(
                LOG_GROUP,
                f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
                f"<b>Caused by Update</b>\n<code>{update}</code>",
            )
            pass

    try:
        with open(f"res/img/{file_name}", "rb") as f:
            if update.message.reply_to_message is not None:
                msg = await update.message.reply_to_message.reply_photo(f, caption=caption)
            else:
                msg = await context.bot.send_photo(update.message.chat_id, f, caption=caption)

            context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, msg.chat_id, str(msg.message_id))


    except Exception as e:
        await context.bot.send_message(
            LOG_GROUP,
            f"<b>⚠️ Error when trying to read html-file {file_name}</b>\n<code>{e}</code>\n\n"
            f"<b>Caused by Update</b>\n<code>{update}</code>",
        )
        pass


def export_svg(svg: str, filename: str):
    logging.info(svg)
    encoded = svg_to_base64(svg, dpi=300, font_dirs=["/res/fonts"],
                            text_rendering="geometric_precision")
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(encoded))
