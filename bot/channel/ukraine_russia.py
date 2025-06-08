import logging

from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, filters, Application, MessageHandler

from bot. settings.config import CHANNEL_UA_RU
from bot. settings.constant import FOOTER_UA_RU


async def append_footer_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"append footer :: {update}")

    if update.channel_post.media_group_id is not None:
        return  # await append_footer_multiple(update,context)

    original_caption = update.channel_post.caption_html_urled or ""

    try:
        await update.channel_post.edit_caption(original_caption + FOOTER_UA_RU)
    except Exception as e:
        logging.error(f"Error editing single :: {e}", )


async def append_footer_multiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    original_caption = update.channel_post.caption_html_urled or ""
    prev_list = {update.channel_post.id}

    for job in context.job_queue.get_jobs_by_name(update.channel_post.media_group_id):
        logging.info(f"Removed job {job}")
        prev_list.update(job.data["ids"])
        original_caption = job.data.get("text", original_caption)
        job.schedule_removal()

    data = {"ids": list(prev_list), "text": original_caption}
    context.job_queue.run_once(append_footer_mg, 10, data, update.channel_post.media_group_id)


async def append_footer_text(update: Update, _: ContextTypes.DEFAULT_TYPE):
    logging.info(f"append_footer_text :: {update}")

    original_caption = update.channel_post.text_html_urled

    try:
        await update.channel_post.edit_text(original_caption + FOOTER_UA_RU)
    except Exception as e:
        logging.exception(f"Error editing single :: {e}")


async def append_footer_mg(context: CallbackContext):
    logging.info(f"append_footer_mg :: {context} :: job-data :: {context.job.data}")

    posts = sorted(context.job.data["ids"])

    for post in posts[1:]:
        try:
            await context.bot.edit_message_caption(CHANNEL_UA_RU, post, caption=None)
        except Exception as e:
            logging.exception(f"Error editing mediagroup other :: {e}", )

    try:
        await context.bot.edit_message_caption(CHANNEL_UA_RU, posts[0], caption=context.job.data["text"] + FOOTER_UA_RU)
    except Exception as e:
        logging.exception(f"Error editing mediagroup text :: {e}")


def register_ua_ru(app: Application):
    filter_media = (filters.PHOTO | filters.VIDEO | filters.ANIMATION)
    filter_ru_ua = filters.UpdateType.CHANNEL_POST & filters.Chat(chat_id=CHANNEL_UA_RU) & ~filters.FORWARDED

    app.add_handler(
        MessageHandler(filter_ru_ua & filter_media & ~filters.CaptionRegex(FOOTER_UA_RU), append_footer_single))

    filter_ru_ua_text = filter_ru_ua & ~filters.Regex(FOOTER_UA_RU) & filters.TEXT
    ###   app.add_handler(MessageHandler(filter_ru_ua_text & filters.Regex(PATTERN_TWITTER), handle_twitter))
    app.add_handler(MessageHandler(filter_ru_ua_text, append_footer_text))
