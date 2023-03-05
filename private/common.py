from telegram import Update
from telegram.ext import filters, ConversationHandler, CallbackContext, CommandHandler

text_filter = filters.TEXT & ~filters.Regex(r"/cancel")


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Änderungen verworfen.")
    return ConversationHandler.END


cancel_handler = [CommandHandler("cancel", cancel)]
