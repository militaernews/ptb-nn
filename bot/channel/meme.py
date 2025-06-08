import logging

from telegram import Update, MessageOrigin
from telegram.ext import CallbackContext, filters, MessageHandler, Application

from bot. settings.config import NX_MEME
from bot. settings.constant import FOOTER_MEME


async def post_media_meme_nx(update: Update, context: CallbackContext):
    if update.channel_post.media_group_id is None or update.channel_post.media_group_id not in context.chat_data:
        await add_footer_meme(update, context)

        if update.channel_post.media_group_id is None:
            return

        context.job_queue.run_once(
            remove_media_group_id,
            20,
            update.channel_post.media_group_id,
            str(update.channel_post.media_group_id),
        )


# TODO: make method more generic
# TODO: apply footer only to 1st entry of mediagroup
async def add_footer_meme(update: Update, context: CallbackContext):
    context.chat_data[update.channel_post.media_group_id] = update.channel_post.id
    original_caption = update.channel_post.caption_html_urled or ""

    try:
        await update.channel_post.edit_caption(await format_meme_footer(original_caption))
    except Exception as e:
        logging.error(f"Error when posting media: {e}")


async def remove_media_group_id(context: CallbackContext):
    print(f"remove_media_group_id {context.job.data}")
    del context.chat_data[context.job.data]


async def post_text_meme_nx(update: Update, _: CallbackContext):
    try:
        await update.channel_post.edit_text(
            await format_meme_footer(update.channel_post.text_html_urled), disable_web_page_preview=False
        )
    except Exception as e:
        logging.error(f"Error when posting text: {e}")


async def format_meme_footer(original_text: str) -> str:
    return f"{original_text}{FOOTER_MEME}"


async def repost_forward(update: Update, _: CallbackContext):
    print(update.channel_post)
    if update.channel_post.forward_origin.type is not MessageOrigin.CHANNEL:
        await update.channel_post.copy(NX_MEME,
                                       caption=await format_meme_footer(update.channel_post.caption))
        await update.channel_post.delete()


async def append_buttons_news(update: Update, _: CallbackContext):
    text = update.message.text_html_urled or update.message.caption_html_urled
    if text is not None:
        logging.info("Appending buttons")


def register_meme(app: Application):
    filter_media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)

    filter_meme = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=NX_MEME) & ~filters.FORWARDED
    app.add_handler(MessageHandler(filter_meme & filters.TEXT & ~filters.Regex(FOOTER_MEME), post_text_meme_nx))
    app.add_handler(
        MessageHandler(filter_meme & filter_media & ~filters.CaptionRegex(FOOTER_MEME), post_media_meme_nx))
    app.add_handler(
        MessageHandler(filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=NX_MEME) & filters.FORWARDED,
                       repost_forward))
