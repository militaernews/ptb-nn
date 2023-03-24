from telegram import Update, BotCommandScopeChat
from telegram.error import BadRequest
from telegram.ext import CallbackContext

import config
from util.helper import reply_html, reply_photo


async def setup(update: Update, context: CallbackContext):
    general_commands = [
        ("maps", "Karten"),
        ("loss", "Verluste"),
        ("stats", "Statistiken"),
        ("short", "Abkürzungen"),
        ("support", "Unterstützung der Ukrainer"),
        ("channels", "Ukrainekrieg auf Telegram"),
        ("peace", "Russlands Kriege"),
        ("donbass", "Beschuss des Donbass seit 2014"),
        ("genozid", "Kein Genozid im Donbass")
    ]
    await context.bot.set_my_commands(general_commands)

    admin_commands = general_commands + [
        ("add_source", "Quelle hinzufügen"),
        ("edit_source", "Quelle bearbeiten"),
        ("add_pattern", "Zu entfernenden Footer hinzufügen"),
    ]
    for chat_id in config.ADMINS:
        try:
            await context.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))
        except BadRequest:  # to ignore chat not found
            pass

    await update.message.reply_text("Commands updated.")


async def maps(update: Update, context: CallbackContext):
    await reply_html(update, context, "maps")


async def loss(update: Update, context: CallbackContext):
    await reply_html(update, context, "loss")


async def stats(update: Update, context: CallbackContext):
    await reply_html(update, context, "stats")


async def short(update: Update, context: CallbackContext):
    await reply_html(update, context, "short")


async def donbass(update: Update, context: CallbackContext):
    await reply_html(update, context, "donbass")


async def channels(update: Update, context: CallbackContext):
    await reply_html(update, context, "channels")


async def genozid(update: Update, context: CallbackContext):
    await reply_html(update, context, "genozid")


async def peace(update: Update, context: CallbackContext):
    await reply_html(update, context, "peace")


async def support(update: Update, context: CallbackContext):
    await reply_photo(update, context, "support_ua.jpg", "support")


async def admin(update: Update, context: CallbackContext):
    print("update", update.message)

    await update.message.delete()

    if update.message.reply_to_message is not None:
        if update.message.reply_to_message.is_automatic_forward:
            text = f"💬  <a href='{update.message.reply_to_message.link}'>Kanalpost</a>"
            response = "Danke für deine Meldung, wir Admins prüfen das 😊"
        else:
            text = f"‼️ <a href='{update.message.reply_to_message.link}'>Nachricht</a> des Nutzers {update.message.reply_to_message.from_user.mention_html()}"
            response = "Ein Nutzer hat deine Nachricht gemeldet. Wir Admins prüfen das. Bitte beachte, dass diese Gruppe eigentlich nicht zu chatten gedacht ist."

        text += f" gemeldet von {update.message.from_user.mention_html()}:\n\n"

        if update.message.reply_to_message.caption is not None:
            text += update.message.reply_to_message.caption_html_urled
        else:
            text += update.message.reply_to_message.text_html_urled

        await context.bot.send_message(config.ADMIN_GROUP, text, message_thread_id=206)

        await update.message.reply_to_message.reply_text(response)


async def sofa(update: Update, context: CallbackContext):
    await reply_photo(update, context, "sofa.jpg")


async def bot(update: Update, context: CallbackContext):
    await reply_photo(update, context, "bot.jpg")


async def mimimi(update: Update, context: CallbackContext):
    await reply_photo(update, context, "mimimi.jpg")


async def cia(update: Update, context: CallbackContext):
    await reply_photo(update, context, "cia.jpg")
