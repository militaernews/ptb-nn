from telegram import Update
from telegram.ext import CallbackContext

from util.helper import reply_html, reply_photo


async def setup(update: Update, context: CallbackContext):
    general_commands = [
        ("maps", "Karten"),
        ("loss", "Verluste"),
        ("stats", "Statistiken"),
        ("support", "Unterstützung der Ukrainer"),
        ("channels", "Ukrainekrieg auf Telegram"),
        ("peace", "Russlands Kriege"),
        ("donbass", "Beschuss des Donbass seit 2014"),
        ("genozid", "Kein Genozid im Donbass")
    ]
    await context.bot.set_my_commands(general_commands)

    await update.message.reply_text("Commands updated.")

async def maps(update: Update, context: CallbackContext):
    await reply_html(update, context, "maps")


async def loss(update: Update, context: CallbackContext):
    await reply_html(update, context, "loss")

async def stats(update: Update, context: CallbackContext):
    await reply_html(update, context, "stats")

async def donbass(update: Update, context: CallbackContext):
    await reply_html(update, context, "donbass")


async def channels(update: Update, context: CallbackContext):
    await reply_html(update, context, "channels")

async def genozid(update: Update, context: CallbackContext):
    await reply_html(update, context, "genozid")


async def peace(update: Update, context: CallbackContext):
    await reply_html(update, context, "peace")

async def support(update: Update, context: CallbackContext):
    await reply_photo(update, context, "support_ua.jpg","support" )
