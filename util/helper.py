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
    path = f"res/strings/{code}/{filename}.html"
    if not os.path.exists(path):
        path = f"res/strings/de/{filename}.html"
    return read_file(path)


def get_text(update: Update, filename: str) -> str:
    return get_text2(update.message.from_user, filename)


async def attempt_message_deletion(update: Update):
    try:
        await update.message.delete()
    except TelegramError as e:
        print("needs admin:", e)


async def log_error(context: CallbackContext, update: Update, file_name: str, e: Exception, mention: bool = False):
    mention_text = " mention" if mention else ""
    await context.bot.send_message(
        LOG_GROUP,
        f"<b>⚠️ Error when trying to read html-file{mention_text} {file_name}</b>\n<code>{e}</code>\n\n"
        f"<b>Caused by Update</b>\n<code>{update}</code>",
    )


async def reply_html(update: Update, context: CallbackContext, file_name: str):
    await attempt_message_deletion(update)
    try:
        text = get_text(update, file_name)
        if "{}" in text:
            text = text.format(update.message.from_user.name)
        else:
            text = f'{text}{FOOTER}'
        logging.info(text)
        msg = await send_message_based_on_reply(update, context, text)
        context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, {CHAT_ID: msg.chat.id, MSG_ID: msg.message_id})
    except Exception as e:
        await log_error(context, update, file_name, e, mention=greet)


async def reply_photo(update: Update, context: CallbackContext, file_name: str, caption: str = None):
    await attempt_message_deletion(update)
    if caption is not None:
        try:
            caption = get_text(update, caption)
        except Exception as e:
            await log_error(context, update, file_name, e)
    try:
        with open(f"res/img/{file_name}", "rb") as f:
            msg = await send_photo_based_on_reply(update, context, f, caption)
            context.job_queue.run_once(delete, MSG_REMOVAL_PERIOD, {CHAT_ID: msg.chat.id, MSG_ID: msg.message_id})
    except Exception as e:
        await log_error(context, update, file_name, e)


def export_svg(svg: str, filename: str):
    logging.info(svg)
    encoded = svg_to_base64(svg, dpi=300, font_dirs=["/res/fonts"], text_rendering="geometric_precision")
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(encoded))


def read_file(path: str) -> str:
    with open(path, "r", encoding='utf-8') as f:
        return f.read()


async def send_message_based_on_reply(update: Update, context: CallbackContext, text: str):
    if update.message.reply_to_message is None:
        return await context.bot.send_message(update.message.chat.id, text)
    elif update.message.reply_to_message.from_user.first_name == "Telegram":
        return await update.message.reply_text(text)
    else:
        return await update.message.reply_to_message.reply_text(text)


async def send_photo_based_on_reply(update: Update, context: CallbackContext, photo, caption: str = None):
    if update.message.reply_to_message is not None:
        return await update.message.reply_to_message.reply_photo(photo, caption=caption)
    else:
        return await context.bot.send_photo(update.message.chat_id, photo, caption=caption)
