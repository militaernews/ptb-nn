import logging
from typing import Sequence, Union, Final

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, PhotoSize, Animation, Video
from telegram.ext import CommandHandler, ConversationHandler, filters, MessageHandler, CallbackContext, ContextTypes, \
    Application

from bot. settings.config import UG_CHANNEL,UG_ADMINS
from bot. private.common import cancel_handler
from bot. util.helper import get_text

ADVERTISEMENT_MEDIA: Final[str] = "new_ADVERTISEMENT_MEDIA"
ADVERTISEMENT_TEXT: Final[str] = "new_ADVERTISEMENT_TEXT"
ADVERTISEMENT_BUTTON: Final[str] = "new_ADVERTISEMENT_BUTTON"
ADVERTISEMENT_URL: Final[str] = "new_ADVERTISEMENT_URL"

NEEDS_MEDIA, NEEDS_TEXT, NEEDS_BUTTON, NEEDS_URL, SAVE_ADVERTISEMENT = range(5)


async def cancel(update: Update, _: CallbackContext) -> int:
    await update.message.reply_text("Werbung verworfen.")
    return ConversationHandler.END


async def add_advertisement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[ADVERTISEMENT_MEDIA] = None
    context.chat_data[ADVERTISEMENT_TEXT] = None
    context.chat_data[ADVERTISEMENT_BUTTON] = None
    context.chat_data[ADVERTISEMENT_URL] = None

    await update.message.reply_text(get_text(update,"advertisement/intro"))
    print(update, context.chat_data)
    return NEEDS_MEDIA


async def add_advertisement_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    print(update)
    logging.info(update.message.effective_attachment)

    context.chat_data[ADVERTISEMENT_MEDIA] = update.message.effective_attachment

    await update.message.reply_text(get_text(update,"advertisement/needs_media"))

    return NEEDS_TEXT


async def skip_media(update: Update, _: CallbackContext) -> int:
    await update.message.reply_text(get_text(update,"advertisement/skip_media"))

    return NEEDS_TEXT


async def add_advertisement_text(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_TEXT] = update.message.text_html_urled

    await update.message.reply_text( get_text(update,"advertisement/needs_text"))

    return NEEDS_BUTTON


async def send_preview(update: Update, context: CallbackContext, button: InlineKeyboardMarkup = None):
    media: Union[Animation, Sequence[PhotoSize], Video, None] = context.chat_data[ADVERTISEMENT_MEDIA]
    text = context.chat_data[ADVERTISEMENT_TEXT]

    try:
        if isinstance(media, Animation):
            await update.message.reply_animation(media, caption=text, reply_markup=button)
        elif isinstance(media, Sequence):
            await update.message.reply_photo(media[-1], caption=text, reply_markup=button)
        elif isinstance(media, Video):
            await update.message.reply_video(media, caption=text, reply_markup=button)
        else:
            await update.message.reply_text(text, reply_markup=button)

        await update.message.reply_text(get_text(update,"advertisement/ready"))
    except Exception as e:
        await update.message.reply_text("Error on sending you the preview! Restart with /cancel."
                                        f"\n\n<code>{e}</code>")


async def skip_button(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(get_text(update,"advertisement/skip_button"))
    await send_preview(update, context)

    return SAVE_ADVERTISEMENT


async def add_advertisement_button(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_BUTTON] = update.message.text

    await update.message.reply_text(get_text(update,"advertisement/needs_button_text"))

    return NEEDS_URL


async def add_advertisement_url(update: Update, context: CallbackContext) -> int:
    context.chat_data[ADVERTISEMENT_URL] = update.message.text

    logging.info(context.chat_data)

    button = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(context.chat_data[ADVERTISEMENT_BUTTON], url=context.chat_data[ADVERTISEMENT_URL]))

    await send_preview(update, context, button)

    return SAVE_ADVERTISEMENT


async def save_advertisement(update: Update, context: CallbackContext) -> int:
    media: Union[Animation, Sequence[PhotoSize], Video, None] = context.chat_data[ADVERTISEMENT_MEDIA]
    text = context.chat_data[ADVERTISEMENT_TEXT]

    if context.chat_data[ADVERTISEMENT_BUTTON] is None:
        button = None
    else:
        button = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(context.chat_data[ADVERTISEMENT_BUTTON], url=context.chat_data[ADVERTISEMENT_URL]))

    if isinstance(media, Animation):
        await context.bot.send_animation(UG_CHANNEL, media, caption=text, reply_markup=button)
    elif isinstance(media, Sequence):
        await context.bot.send_photo(UG_CHANNEL, media[-1], caption=text, reply_markup=button)
    elif isinstance(media, Video):
        await context.bot.send_video(UG_CHANNEL, media, caption=text, reply_markup=button)
    else:
        await context.bot.send_text(UG_CHANNEL, text, reply_markup=button)

    await update.message.reply_text(get_text(update,"advertisement/done"))

    return ConversationHandler.END


def register_advertisement(app: Application):
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add_advertisement", add_advertisement, filters=filters.Chat(UG_ADMINS))],
        states={
            NEEDS_MEDIA: [
                CommandHandler("skip", skip_media),
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.ANIMATION, add_advertisement_media),
            ],
            NEEDS_TEXT: [MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_text)],
            NEEDS_BUTTON: [CommandHandler("skip", skip_button),
                           MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_button),
                           ],
            NEEDS_URL: [MessageHandler(filters.TEXT & ~filters.Regex(r"/cancel"), add_advertisement_url)],
            SAVE_ADVERTISEMENT: [CommandHandler("save", save_advertisement)]

        },
        fallbacks=cancel_handler,
    ))
