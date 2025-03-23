import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MessageOrigin, MessageOriginChannel
from telegram.constants import ChatType
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, \
    filters

from bot.config import ADMINS
from bot.data.db import get_source, get_destinations, get_accounts, update_source
from bot.data.model import Source, Account
from bot.private.common import text_filter, cancel_handler

SOURCE_INVITE = "edit_source_invite"
SOURCE_USERNAME = "edit_source_username"
SOURCE_TITLE = "edit_source_title"
SOURCE_DISPLAY = "edit_source_display"
SOURCE_BIAS = "edit_source_bias"
SOURCE_ID = "edit_source_id"
SOURCE_RATING = "edit_source_rating"
SOURCE_DESTINATION = "edit_source_destination"
SOURCE_DESCRIPTION = "edit_source_description"
SOURCE_DETAIL = "edit_source_detail"
SOURCE_API = "edit_source_api"
SOURCE_ACTIVE = "edit_source_active"
SOURCE_SPREAD = "edit_source_spread"
DESTINATIONS = "edit_source_destinations"
ACCOUNTS = "edit_source_accounts"

EDIT_SOURCE, SELECT_EDIT, EDIT_NAME, EDIT_INVITE, EDIT_DISPLAY, EDIT_USERNAME, EDIT_RATING, EDIT_DESTINATION, EDIT_DESCRIPTION, EDIT_DETAIL, \
    EDIT_API, EDIT_BIAS, SAVE_EDIT_SOURCE = range(13)

back_button = [InlineKeyboardButton("⬅️ Zurück", callback_data="back")]
back_keyboard = InlineKeyboardMarkup([back_button])


def get_destination(context: CallbackContext) -> str | None:
    if context.chat_data[SOURCE_DESTINATION] is None:
        return None

    context.chat_data[DESTINATIONS] = get_destinations()
    return context.chat_data[DESTINATIONS][context.chat_data[SOURCE_DESTINATION]]


def get_account(context: CallbackContext) -> Account | None:
    if context.chat_data[SOURCE_API] is None:
        return None

    context.chat_data[ACCOUNTS] = get_accounts()
    print("accounts", context.chat_data[ACCOUNTS], context.chat_data[SOURCE_API],
          type(context.chat_data[SOURCE_API]))
    return context.chat_data[ACCOUNTS][context.chat_data[SOURCE_API]]


def get_rating(context: CallbackContext) -> str | None:
    if context.chat_data[SOURCE_RATING] is None:
        return None

    print("rating", context.chat_data[SOURCE_RATING],
          type(context.chat_data[SOURCE_RATING]))
    return "".join("⭐️" for _ in range(context.chat_data[SOURCE_RATING]))


def get_detail(context: CallbackContext) -> str | None:
    if context.chat_data[SOURCE_DETAIL] is not None:

        return f"https://t.me/nn_sources/{context.chat_data[SOURCE_DETAIL]}"
    else:
        return None


def change_overview(context: CallbackContext) -> str:
    account_name = get_account(context).name if get_account(context) is not None else None

    return "✏️ Bearbeiten der Quelle\n\n" \
           f"— title: <code>{context.chat_data[SOURCE_TITLE]}</code>\n\n" \
           f"— chat_id: <code>{context.chat_data[SOURCE_ID]}</code>\n\n" \
           f"— username: <code>{context.chat_data[SOURCE_USERNAME]}</code>\n\n\n" \
           "Editierbar für News:\n\n" \
           f"🔹 Einladungshash: <code>{context.chat_data[SOURCE_INVITE]}</code>\n\n" \
           f"🔹 Anzeigename: <code>{context.chat_data[SOURCE_DISPLAY]}</code>\n\n" \
           f"🔹 Voreingenommenheit: <code>{context.chat_data[SOURCE_BIAS]}</code>\n\n" \
           f"🔹 Ausgabekanal: <code>{get_destination(context)}</code>\n\n" \
           f"🔹 Tracking der Quell-Posts: {'✅' if context.chat_data[SOURCE_ACTIVE] else '✖️'}\n\n" \
           f"🔹 Posten der Quell-Posts: {'✅' if context.chat_data[SOURCE_SPREAD] else '✖️'}\n\n" \
           f"🔹 Account: <code>{account_name}</code>\n\n\n" \
           "Editierbar für @nn_sources:\n\n" \
           f"🔸 Bewertung: <code>{get_rating(context)}</code>\n\n" \
           f"🔸 Beschreibung: <code>{context.chat_data[SOURCE_DESCRIPTION]}</code>\n\n" \
           f"🔸 Detail Nachricht: <code>{get_detail(context)}</code>\n\n" \
           "<i>Drücke /save um die Änderungen zu speichern oder /cancel um alles abzubrechen.</i>"


def change_keyboard(context: CallbackContext) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Display", callback_data=SOURCE_DISPLAY),
            InlineKeyboardButton("Invite", callback_data=SOURCE_INVITE)
        ],
        [
            InlineKeyboardButton("Bias", callback_data=SOURCE_BIAS),
            InlineKeyboardButton("Rating", callback_data=SOURCE_RATING)
        ],
        [
            InlineKeyboardButton("Detail", callback_data=SOURCE_DETAIL),
            InlineKeyboardButton("Beschreibung", callback_data=SOURCE_DESCRIPTION)
        ],
        [
            InlineKeyboardButton("Ausgabekanal", callback_data=SOURCE_DESTINATION),
            InlineKeyboardButton("Account", callback_data=SOURCE_API),
        ]
    ]

    spread_text = "✅ Posten" if context.chat_data[SOURCE_SPREAD] else "✖️ nur Backup"
    last_keyboard = [InlineKeyboardButton(spread_text, callback_data=SOURCE_SPREAD)]

    active_text = "✅ Tracking" if context.chat_data[SOURCE_ACTIVE] else "✖️ Inaktiv"

    if context.chat_data[SOURCE_API] and context.chat_data[SOURCE_DESTINATION] is not None:
        last_keyboard.append(InlineKeyboardButton(active_text, callback_data=SOURCE_ACTIVE))

    keyboard.append(last_keyboard)

    return InlineKeyboardMarkup(keyboard)


async def display_selection(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(change_overview(context), reply_markup=change_keyboard(context))

    return SELECT_EDIT


async def edit_source_back(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(change_overview(context), reply_markup=change_keyboard(context))

    await update.callback_query.answer()
    return SELECT_EDIT


async def edit_source(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_ID] = None
    context.chat_data[SOURCE_TITLE] = None
    context.chat_data[SOURCE_DISPLAY] = None
    context.chat_data[SOURCE_BIAS] = None
    context.chat_data[SOURCE_INVITE] = None
    context.chat_data[SOURCE_USERNAME] = None
    context.chat_data[SOURCE_RATING] = None
    context.chat_data[SOURCE_DESTINATION] = None
    context.chat_data[SOURCE_DESCRIPTION] = None
    context.chat_data[SOURCE_DETAIL] = None
    context.chat_data[SOURCE_API] = None
    context.chat_data[SOURCE_SPREAD] = False
    context.chat_data[SOURCE_ACTIVE] = False
    context.chat_data[ACCOUNTS] = None
    context.chat_data[DESTINATIONS] = None

    await update.message.reply_text(
        "Bitte leite mir nun eine Nachricht des zu bearbeitenden Kanals weiter. Mit /cancel kannst du abbrechen und von vorne starten.")
    return EDIT_SOURCE


async def edit_source_channel(update: Update, context: CallbackContext) -> int:
    source: MessageOrigin = update.message.forward_origin
    if source is None:
        await update.message.reply_text("fwd-chat-id is None")
        return ConversationHandler.END

    if source.type != ChatType.CHANNEL:
        await update.message.reply_text("Ich habe nur Kanäle gespeichert.")
        return ConversationHandler.END

    source: MessageOriginChannel = source
    source_id = source.chat.id

    result = get_source(source_id)

    if result is None:
        await update.message.reply_text(
            f"Eine Quelle mit der ID <code>{source_id}</code> ist nicht in meiner Datenbank hinterlegt. Mit /add_source kannst du einen Kanal hinzufügen.")
        return ConversationHandler.END

    context.chat_data[SOURCE_ID] = source_id
    context.chat_data[SOURCE_TITLE] = source.chat.title or result.channel_name
    context.chat_data[SOURCE_DISPLAY] = result.display_name
    context.chat_data[SOURCE_BIAS] = result.bias
    context.chat_data[SOURCE_INVITE] = result.invite
    context.chat_data[SOURCE_USERNAME] = source.chat.username or result.username
    context.chat_data[SOURCE_RATING] = result.rating
    context.chat_data[SOURCE_DESTINATION] = result.destination
    context.chat_data[SOURCE_DESCRIPTION] = result.description
    context.chat_data[SOURCE_DETAIL] = result.detail_id
    context.chat_data[SOURCE_API] = result.api_id
    context.chat_data[SOURCE_ACTIVE] = result.is_spread
    context.chat_data[SOURCE_ACTIVE] = result.is_active

    await update.message.reply_text(change_overview(context), reply_markup=change_keyboard(context))
    return SELECT_EDIT


async def edit_source_display(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(
        "Sende mir nun einen neuen Anzeigenamen für diesen Kanal. Da manche Kanäle kyrillische, arabische oder auch sehr lange Namen haben, wäre es sinnvoll wenn du mir einen kürzeren für diesen Kanal vorschlägst. Mit /empty kannst du ihn leeren.\n\n"
        f"Zwischengespeichert ist aktuell: <code>{context.chat_data[SOURCE_DISPLAY]}</code>",

        reply_markup=back_keyboard)
    await update.callback_query.answer()

    return EDIT_DISPLAY


async def save_source_display(update: Update, context: CallbackContext) -> int | None:
    if len(update.message.text) > 20:
        await update.message.reply_text(
            "Der Displayname ist über 20 Zeichen lang, bitte sende mir etwas kürzeres. Du kann dich auch am Nutzernamen inspirieren lassen oder abkürzen.")
        return EDIT_DISPLAY

    context.chat_data[SOURCE_DISPLAY] = update.message.text

    return await display_selection(update, context)


async def clear_source_display(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_DISPLAY] = None

    return await display_selection(update, context)


async def edit_source_invite(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(
        "Nutzer benötigen zum Beitreten eines privaten Kanals einen Einladungslink. Bitte sende mir den Einladungslink im Format https://t.me/+123abcInvitehashblabla69 - Mit /empty kannst du ihn leeren.\n\n"
        f"Zwischengespeichert ist aktuell: <code>{context.chat_data[SOURCE_INVITE]}</code>",

        reply_markup=back_keyboard)
    await update.callback_query.answer()

    return EDIT_INVITE


async def save_source_invite(update: Update, context: CallbackContext) -> int | None:
    invite_match = re.findall(r"t\.me/\+(.*)$", update.message.text)

    if len(invite_match) != 1:
        await update.message.reply_text(
            "Bitte sende mir den Einladungslink im Format https://t.me/+123abcInvitehashblabla69")
        return EDIT_INVITE

    context.chat_data[SOURCE_INVITE] = invite_match[0]

    return await display_selection(update, context)


async def clear_source_invite(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_INVITE] = None

    return await display_selection(update, context)


async def edit_source_bias(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(
        "Viele Kanäle sind klar voreingenommen, berichten also sehr positiv oder ausschließlich über eine Seite und negativ oder nur über Misserfolge der anderen. Bitte sende mir nun in einer Nachricht ein oder mehrere Flaggen-Emojis für die entsprechende Voreingenommenheit des Kanals. Gebe hierzu einen Doppelpunkt ein und suche dann das Land auf English, beispielweise :russia:\n\n" \
        "Wenn der Kanal keine klar ersichtliche Voreingenommenheit aufweist, dann tippe einfach /empty\n\n"
        f"Zwischengespeichert ist aktuell: <code>{context.chat_data[SOURCE_BIAS]}</code>",

        reply_markup=back_keyboard)
    await update.callback_query.answer()

    return EDIT_BIAS


async def save_source_bias(update: Update, context: CallbackContext) -> int | None:
    context.chat_data[SOURCE_BIAS] = update.message.text

    return await display_selection(update, context)


async def clear_source_bias(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_BIAS] = None

    return await display_selection(update, context)


async def edit_source_rating(update: Update, context: CallbackContext) -> int:
    keyboard = []

    rating = ""
    for i in range(5):
        rating += "⭐️"

        keyboard.append([InlineKeyboardButton(rating, callback_data=f"{SOURCE_RATING}_{i + 1}")])

    await update.callback_query.edit_message_text(
        "Wähle welches Rating dieser Kanal erhalten soll. Ein Stern ist das schlechteste, fünf Sterne das beste. Achte hierbei auf die Aktualität, Detailvielfalt und Qualität der Meldungen, aber auch ob sie als Primärquelle fungiert, viele Medien hat, reißerisch geschrieben ist.\n\nMit /empty du kein Rating vergeben.\n\n"
        f"Zwischengespeichert ist aktuell: <code>{get_rating(context)}</code>",

        reply_markup=InlineKeyboardMarkup(

            keyboard +
            [back_button]

        ))
    await update.callback_query.answer()

    return EDIT_RATING


async def save_source_rating(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_RATING] = int(update.callback_query.data.split("_")[-1])

    return await edit_source_back(update, context)


async def clear_source_rating(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_RATING] = None

    return await edit_source_back(update, context)


async def edit_source_detail(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(
        "Leite bitte den Detailpost zu diesem Kanal weiter. Wenn bereits ein Link hinterlegt ist, dann kann du keinen mehr hinzufügen.\n\n"
        f"Zwischengespeichert ist aktuell: {get_detail(context)}",

        reply_markup=back_keyboard)
    await update.callback_query.answer()

    return EDIT_DETAIL


async def save_source_detail(update: Update, context: CallbackContext) -> int | None:
    if update.message.sender_chat.id != -1001616523535:
        await update.message.reply_text(
            "Bitte leite mir den Detail-Post zu diesem Kanal aus @nn_sources weiter.")
        return EDIT_DETAIL

    context.chat_data[SOURCE_DETAIL] = update.message.forward_from_message_id

    return await display_selection(update, context)


async def clear_source_detail(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_DETAIL] = None

    return await display_selection(update, context)


async def edit_source_description(update: Update, context: CallbackContext) -> int:
    await update.callback_query.edit_message_text(
        f"Beschreibe in 750 Zeichen was dieser Kanal macht.\n\nZum entfernen tippe einfach /empty\n\nZwischengespeichert ist aktuell: <code>{context.chat_data[SOURCE_DESCRIPTION]}</code>",

        reply_markup=back_keyboard)
    await update.callback_query.answer()

    return EDIT_DESCRIPTION


async def save_source_description(update: Update, context: CallbackContext) -> int | None:
    if len(update.message.text) > 750:
        await update.message.reply_text(
            "Die Beschreibung ist über 750 Zeichen lang, bitte sende mir etwas kürzeres.")
        return EDIT_DISPLAY

    context.chat_data[SOURCE_DESCRIPTION] = update.message.text

    return await display_selection(update, context)


async def clear_source_description(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_DESCRIPTION] = None

    return await display_selection(update, context)


async def edit_source_destination(update: Update, context: CallbackContext) -> int:
    context.chat_data[DESTINATIONS] = get_destinations()

    keyboard = list()

    for k, v in context.chat_data[DESTINATIONS].items():

        if k == context.chat_data[SOURCE_DESTINATION]:
            v = f"✅ {v}"

        keyboard.append([InlineKeyboardButton(v, callback_data=f"{SOURCE_DESTINATION}_{k}")])

    await update.callback_query.edit_message_text(
        "Wähle in welchem Kanal dieser Kanal posten soll. Mit /empty kannst du ihn leeren.\n\n"
        f"Zwischengespeichert ist aktuell: <code>{get_destination(context)}</code>",

        reply_markup=InlineKeyboardMarkup(

            keyboard +
            [back_button]

        ))
    await update.callback_query.answer()

    return EDIT_DESTINATION


async def save_source_destination(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_DESTINATION] = int(update.callback_query.data.split("_")[-1])

    return await edit_source_back(update, context)


async def clear_source_destination(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_DESTINATION] = None

    return await edit_source_back(update, context)


async def edit_source_api(update: Update, context: CallbackContext) -> int:
    context.chat_data[ACCOUNTS] = get_accounts()

    keyboard = []

    for k, v in context.chat_data[ACCOUNTS].items():
        v = v.name
        if k == context.chat_data[SOURCE_API]:
            v = f"✅ {v}"

        keyboard.append([InlineKeyboardButton(v, callback_data=f"{SOURCE_API}_{k}")])

    account_name = get_account(context).name if get_account(context) is not None else None
    await update.callback_query.edit_message_text(
        "Wähle den Account der Nachrichten aus diesem Kanal lesen soll. Hierzu muss der Account im entsprechenden Kanal Mitglied sein!  Mit /empty kannst du ihn leeren.\n\n"
        f"Zwischengespeichert ist aktuell: <code>{account_name}</code>",

        reply_markup=InlineKeyboardMarkup(

            keyboard +
            [back_button]

        ))
    await update.callback_query.answer()

    return EDIT_API


async def save_source_api(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_API] = int(update.callback_query.data.split("_")[-1])

    return await edit_source_back(update, context)


async def clear_source_api(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_API] = None

    return await edit_source_back(update, context)


async def edit_source_spread(update: Update, context: CallbackContext) -> int:
    context.chat_data[SOURCE_SPREAD] = not context.chat_data[SOURCE_SPREAD]

    await update.callback_query.edit_message_reply_markup(change_keyboard(context))
    await update.callback_query.answer()
    return SELECT_EDIT


async def edit_source_active(update: Update, context: CallbackContext) -> int:
    if context.chat_data[SOURCE_API] is not None:
        context.chat_data[SOURCE_ACTIVE] = not context.chat_data[SOURCE_ACTIVE]

        await update.callback_query.edit_message_reply_markup(change_keyboard(context))
    await update.callback_query.answer()
    return SELECT_EDIT


async def save_edit_source(update: Update, context: CallbackContext) -> int:
    source = Source(
        channel_id=context.chat_data[SOURCE_ID],
        channel_name=context.chat_data[SOURCE_TITLE],
        bias=context.chat_data[SOURCE_BIAS],
        destination=context.chat_data[SOURCE_DESTINATION],
        display_name=context.chat_data[SOURCE_DISPLAY],
        invite=context.chat_data[SOURCE_INVITE],
        username=context.chat_data[SOURCE_USERNAME],
        api_id=context.chat_data[SOURCE_API],
        description=context.chat_data[SOURCE_DESCRIPTION],
        rating=context.chat_data[SOURCE_RATING],
        detail_id=context.chat_data[SOURCE_DETAIL],
        is_spread=context.chat_data[SOURCE_SPREAD],
        is_active=context.chat_data[SOURCE_ACTIVE]
    )

    update_source(source)

    await update.message.reply_text(f"Änderungen für Quelle <code>{context.chat_data[SOURCE_ID]}</code> übernommen.\n\n"
                                    f"Falls du eine Quelle aktiviert oder deaktiviert hast, dann muss erst der komplette Bot neu gestartet werden, sodass die Quellen neu eingelesen werden.")
    return ConversationHandler.END


back_handler = CallbackQueryHandler(edit_source_back, "back")
edit_source_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_source", edit_source, filters=filters.Chat(ADMINS))],
    states={
        EDIT_SOURCE: [MessageHandler(filters.FORWARDED, edit_source_channel)],
        SELECT_EDIT: [
            CallbackQueryHandler(edit_source_display, SOURCE_DISPLAY),
            CallbackQueryHandler(edit_source_invite, SOURCE_INVITE),
            CallbackQueryHandler(edit_source_bias, SOURCE_BIAS),
            CallbackQueryHandler(edit_source_rating, SOURCE_RATING),
            CallbackQueryHandler(edit_source_detail, SOURCE_DETAIL),
            CallbackQueryHandler(edit_source_description, SOURCE_DESCRIPTION),
            CallbackQueryHandler(edit_source_api, SOURCE_API),
            CallbackQueryHandler(edit_source_destination, SOURCE_DESTINATION),
            CallbackQueryHandler(edit_source_spread, SOURCE_SPREAD),
            CallbackQueryHandler(edit_source_active, SOURCE_ACTIVE),
            CommandHandler("save", save_edit_source)
        ],

        EDIT_DISPLAY: [back_handler, CommandHandler("empty", clear_source_display),
                       MessageHandler(text_filter, save_source_display),
                       ],
        EDIT_INVITE: [back_handler, CommandHandler("empty", clear_source_invite),
                      MessageHandler(text_filter, save_source_invite),
                      ],
        EDIT_BIAS: [back_handler, CommandHandler("empty", clear_source_bias),
                    MessageHandler(text_filter, save_source_bias),
                    ],
        EDIT_RATING: [back_handler, CommandHandler("empty", clear_source_rating),
                      CallbackQueryHandler(save_source_rating, fr"^{SOURCE_RATING}_\d$")],
        EDIT_DETAIL: [back_handler, CommandHandler("empty", clear_source_detail),
                      MessageHandler(filters.FORWARDED, save_source_detail)],
        EDIT_DESCRIPTION: [back_handler, CommandHandler("empty", clear_source_description),
                           MessageHandler(text_filter, save_source_description),
                           ],
        EDIT_API: [back_handler, CommandHandler("empty", clear_source_api),
                   CallbackQueryHandler(save_source_api, fr"^{SOURCE_API}_\d+$")],
        EDIT_DESTINATION: [back_handler, CommandHandler("empty", clear_source_destination),
                           CallbackQueryHandler(save_source_destination, fr"^{SOURCE_DESTINATION}_-\d+$")],
    },
    fallbacks=cancel_handler,
)
