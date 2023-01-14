from telegram import Update
from telegram.ext import CallbackContext

from util.helper import reply_html


async def maps(update: Update, context: CallbackContext):
    await reply_html(update, context, "maps")


async def loss(update: Update, context: CallbackContext):
    await reply_html(update, context, "loss")


async def donbas(update: Update, context: CallbackContext):
    await reply_html(update, context, "donbas")


async def genozid(update: Update, context: CallbackContext):
    await reply_html(update, context, "genozid")


async def peace(update: Update, context: CallbackContext):
    await reply_html(update, context, "peace")
