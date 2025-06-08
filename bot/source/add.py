import logging
import re

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext, ConversationHandler, ContextTypes, CommandHandler, MessageHandler, filters

from bot. data.db import get_source, set_source, get_free_account_id
from bot. data.model import SourceInsert
from bot. private.common import text_filter, cancel_handler
from bot. settings.config import ADMINS

SOURCE_INVITE = "new_source_invite"
SOURCE_USERNAME = "new_source_username"
SOURCE_TITLE = "new_source_title"
SOURCE_DISPLAY = "new_source_display"
SOURCE_BIAS = "new_source_bias"
SOURCE_ID = "new_source_id"

ADD_SOURCE, NEEDS_INVITE, NEEDS_DISPLAY, NEEDS_BIAS, SAVE_SOURCE = range(5)


async def add_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[SOURCE_ID] = None
    context.chat_data[SOURCE_TITLE] = None
    context.chat_data[SOURCE_DISPLAY] = None
    context.chat_data[SOURCE_BIAS] = None
    context.chat_data[SOURCE_INVITE] = None
    context.chat_data[SOURCE_USERNAME] = None

    await update.message.reply_text(
        "Bitte leite mir nun eine Nachricht des hinzuzufügenden Kanals weiter. Mit /cancel kannst du abbrechen und von vorne starten.")
    return ADD_SOURCE


async def add_source_channel(update: Update, context: CallbackContext) -> int | None:
    print(update.message)
    source = update.message.forward_origin.chat

    if source.id is None:
        await update.message.reply_text("fwd-chat-id is None")
        return ConversationHandler.END

    if source.type != ChatType.CHANNEL:
        await update.message.reply_text("Ich habe nur Kanäle gespeichert.")
        return ConversationHandler.END

    result = get_source(source.id)

    if result is not None:
        await update.message.reply_text(
            f"Eine Quelle mit der ID <code>{source.id}</code> ist bereits in meiner Datenbank hinterlegt. Mit /edit_source kannst du einen Kanal überarbeiten.")
        return ConversationHandler.END

    context.chat_data[SOURCE_ID] = source.id
    context.chat_data[SOURCE_TITLE] = source_name = source.title
    context.chat_data[SOURCE_USERNAME] = source_username = source.username

    text = f"Passt das so?\n\nID: {source.id}\n\nName: {source_name}"

    if source_username is None:
        text += "\n\nEs ist leider kein Nutzername (@beispielUsername) hinterlegt. Nutzer benötigen zum Beitreten dieses privaten Kanal einen Einladungslink. Bitte sende mir den Einladungslink im Format https://t.me/+123abcInvitehashblabla69"
        await update.message.reply_text(text)
        return NEEDS_INVITE

    text += f"\n\nUsername: {source_username}\n\n" \
            f"Da manche Kanäle kyrillische, arabische oder auch sehr lange Namen haben, wäre es sinnvoll wenn du mir einen kürzeren für diesen Kanal vorschlägst.\n\n" \
            f"Wenn der Name bereits recht prägnant, kurz und verständlich ist, dann tippe einfach /skip"
    await update.message.reply_text(text)
    return NEEDS_DISPLAY


async def add_source_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    invite_match = re.findall(r"t.me/\+(.*)$", update.message.text)

    if len(invite_match) != 1:
        await update.message.reply_text(
            "Bitte sende mir den Einladungslink im Format https://t.me/+123abcInvitehashblabla69")
        return NEEDS_INVITE

    context.chat_data[SOURCE_INVITE] = source_invite = invite_match[0]

    text = f"Passt das so?\n\n" \
           f"ID: {context.chat_data[SOURCE_ID]}\n\n" \
           f"Name: {context.chat_data[SOURCE_TITLE]}\n\n" \
           f"Einladungshash: {source_invite}\n\n" \
           f"Da manche Kanäle kyrillische, arabische oder auch sehr lange Namen haben, wäre es sinnvoll wenn du mir einen kürzeren für diesen Kanal vorschlägst.\n\n" \
           f"Wenn der Name bereits recht prägnant, kurz und verständlich ist, dann tippe einfach /skip"
    await update.message.reply_text(text)
    return NEEDS_DISPLAY


async def add_source_display(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if len(update.message.text) > 20:
        await update.message.reply_text(
            "Der Displayname ist über 20 Zeichen lang, bitte sende mir etwas kürzeres. Du kann dich auch am Nutzernamen inspirieren lassen oder abkürzen.\n\n"
            "Wenn du doch keinen Displaynamen senden möchtest, dann einfach /skip")
        return NEEDS_DISPLAY

    context.chat_data[SOURCE_DISPLAY] = source_display = update.message.text

    text = "Passt das so?\n\n" \
           f"ID: {context.chat_data[SOURCE_ID]}\n\n" \
           f"Name: {context.chat_data[SOURCE_TITLE]}\n\n" \
           f"Username: {context.chat_data[SOURCE_USERNAME]}\n\n" \
           f"Einladungshash: {context.chat_data[SOURCE_INVITE]}\n\n" \
           f"Anzeigename: {source_display}\n\n" \
           "Viele Kanäle sind klar voreingenommen, berichten also sehr positiv oder ausschließlich über eine Seite und negativ oder nur über Misserfolge der anderen. Bitte sende mir nun in einer Nachricht ein oder mehrere Flaggen-Emojis für die entsprechende Voreingenommenheit des Kanals. Gebe hierzu einen Doppelpunkt ein und suche dann das Land auf English, beispielweise :russia:\n\n" \
           "Wenn der Kanal keine klar ersichtliche Voreingenommenheit aufweist, dann tippe einfach /skip"

    await update.message.reply_text(text)
    return NEEDS_BIAS


async def add_source_bias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.chat_data[SOURCE_BIAS] = source_bias = update.message.text

    text = "Passt das so?\n\n" \
           f"ID: {context.chat_data[SOURCE_ID]}\n\n" \
           f"Name: {context.chat_data[SOURCE_TITLE]}\n\n" \
           f"Username: {context.chat_data[SOURCE_USERNAME]}\n\n" \
           f"Einladungshash: {context.chat_data[SOURCE_INVITE]}\n\n" \
           f"Anzeigename: {context.chat_data[SOURCE_DISPLAY]}\n\n" \
           f"Voreingenommenheit: {source_bias}\n\n" \
           "Möchtest du den Kanal so speichern? Dann tippe /save oder wenn du abbrechen willst, dann /cancel"

    await update.message.reply_text(text)
    return SAVE_SOURCE


async def skip_display(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Setzen des Nutzernamens übersprungen.\n\n"
                                    "Viele Kanäle sind klar voreingenommen, berichten also sehr positiv oder ausschließlich über eine Seite und negativ oder nur über Misserfolge der anderen. Bitte sende mir nun in einer Nachricht ein oder mehrere Flaggen-Emojis für die entsprechende Voreingenommenheit des Kanals. Gebe hierzu einen Doppelpunkt ein und suche dann das Land auf English, beispielweise :russia:\n\n"
                                    "Wenn der Kanal keine klar ersichtliche Voreingenommenheit aufweist, dann tippe einfach /skip"

                                    )

    return NEEDS_BIAS


async def skip_bias(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Setzen der Voreingenommenheit übersprungen.\n\n"

                                    f"ID: {context.chat_data[SOURCE_ID]}\n\n"
                                    f"Name: {context.chat_data[SOURCE_TITLE]}\n\n"
                                    f"Username: {context.chat_data[SOURCE_USERNAME]}\n\n"
                                    f"Einladungshash: {context.chat_data[SOURCE_INVITE]}\n\n"
                                    f"Anzeigename: {context.chat_data[SOURCE_DISPLAY]}\n\n"
                                    f"Voreingenommenheit: {context.chat_data[SOURCE_BIAS]}\n\n"
                                    "Möchtest du den Kanal so speichern? Dann tippe /save oder wenn du abbrechen willst, dann /cancel")

    return SAVE_SOURCE


async def save_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    account = get_free_account_id()

    set_source(SourceInsert(
        context.chat_data[SOURCE_ID],
        account.api_id,
        context.chat_data[SOURCE_TITLE],
        context.chat_data[SOURCE_DISPLAY],
        context.chat_data[SOURCE_BIAS],
        context.chat_data[SOURCE_INVITE],
        context.chat_data[SOURCE_USERNAME],

    ))

    joining = f"Ich werde nun versuchen mit dem Account '{account.name}' beizutreten. Bitte einen kurzen Augenblick Geduld."

    await update.message.reply_text(
        f"Kanal '{context.chat_data[SOURCE_TITLE]}' wurde in der Datenbank gespeichert. Wenn du ihn überarbeiten willst, dann tippe /edit_source.\n\n{joining}")

    await context.bot.send_message(account.user_id,
                                   f"/join {context.chat_data[SOURCE_INVITE] or f'@{context.chat_data[SOURCE_USERNAME]}'} {update.message.from_user.id}")

    return ConversationHandler.END


add_source_handler = ConversationHandler(
    entry_points=[CommandHandler("add_source", add_source, filters=filters.Chat(ADMINS))],
    states={
        ADD_SOURCE: [MessageHandler(filters.FORWARDED, add_source_channel)],
        NEEDS_INVITE: [MessageHandler(text_filter, add_source_invite)],
        NEEDS_DISPLAY: [CommandHandler("skip", skip_display),
                        MessageHandler(text_filter, add_source_display),
                        ],
        NEEDS_BIAS: [CommandHandler("skip", skip_bias),
                     MessageHandler(text_filter, add_source_bias),

                     ],
        SAVE_SOURCE: [CommandHandler("save", save_source)]

    },
    fallbacks=cancel_handler,
)


async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(" ")[1:]
    logging.info(f"handling nm join. args: {args}")

    if len(args) < 3:
        await update.message.reply_text("Arguments required:\n\n1. Joined Chat ID\n2. By User ID\n3. Result")
        logging.error("handling nm join. missing args.")
        return

    joined_chat = args[0]
    joined_by = args[1]
    joined_result = args[2]

    await context.bot.send_message(joined_by, f"Tried joining Chat: {joined_chat}\n---\nResult: {joined_result}")
    logging.info(f"handling nm join. {joined_chat} {joined_by} - RESULT: {joined_result}")
