import contextlib

from settings.config import UG_ADMINS, ADMINS, GROUP_UA_RU
from telegram import Update, BotCommandScopeChatAdministrators, BotCommandScopeChat
from telegram.error import BadRequest
from telegram.ext import CallbackContext


async def set_cmd(update: Update, context: CallbackContext):
    await context.bot.delete_my_commands()

    general_commands = [
        ("cmd", "Übersicht aller Befehle"),
        ("maps", "Karten Ukraine-Krieg"),
        ("loss", "Materialverluste in der Ukraine"),
        ("rules", "Regel der Gruppe"),
        ("whitelist", "Erlaubte Links"),
        ("donbas", "14.000 Zivilisten im Donbas"),
        ("stats", "Statistiken"),
        ("short", "Abkürzungen"),
        ("peace", "Russische Kriege"),
        ("bias", "Ist MN neutral?"),
        ("sold", "Söldner Vorrausetzungen"),
        ("genozid", "Kein Genozid der Ukrainer im Donbas"),
        ("sofa", "Waffensystem des Sofa-Kriegers"),
        ("bot", "für Trolle"),
        ("mimimi", "Wenn einer mal wieder heult"),
        ("duden", "Deutsch. Setzen. Sechs."),
        ("argu", "Argumentationspyramide"),
        ("disso", "Kognitive Dissonanz"),
        ("wissen", "Wissen ist Holschuld"),
        ("hominem", "Ad hominem"),
        ("deutsch", "Amtssprache"),
        ("vs", "Verfassungsschutz"),
        ("front", "An die Front!"),
    ]
    await context.bot.set_my_commands(general_commands)

    await context.bot.set_my_commands(general_commands + [
        ("warn", "Nutzer verwarnen"),
        ("unwarn", "Warnung abziehen"),
        ("ban", "Nutzer sperren"),
        ("report", "Tartaros Antispam melden"),
        ("bingo", "Spielfeld des Bullshit-Bingos"),
        ("reset_bingo", "Neue Bingo-Runde")
    ], scope=BotCommandScopeChatAdministrators(GROUP_UA_RU))

    ug_admin_commands = general_commands + [
        ("add_advertisement", "Werbung erstellen"),
    ]
    for chat_id in UG_ADMINS:
        with contextlib.suppress(BadRequest):
            await context.bot.set_my_commands(ug_admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))

    admin_commands = general_commands + [
        ("add_source", "Quelle hinzufügen"),
        ("edit_source", "Quelle bearbeiten"),
        ("add_pattern", "Zu entfernenden Footer hinzufügen"),
        ("warn", "Nutzer verwarnen"),
        ("unwarn", "Verwarnung zurückziehen"),
    ]
    for chat_id in ADMINS:
        with contextlib.suppress(BadRequest):
            await context.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=chat_id))

    await update.message.reply_text("Commands updated!")
