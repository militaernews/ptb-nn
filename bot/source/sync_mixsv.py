"""Admin command that pulls sources/bloats edits made through mix-sv's web UI
into this bot's own database. mix-sv keeps its own independent copy of
sources/bloats (a separate Neon database) - this command diffs it against
what's actually live here, shows the admin what changed, and only writes
anything once they confirm.
"""
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, filters

from bot.data import db, mixsv_db
from bot.settings.config import ADMINS

CONFIRM_APPLY = "sync_mixsv_apply"
CONFIRM_CANCEL = "sync_mixsv_cancel"
PENDING_DIFFS = "sync_mixsv_diffs"

MAX_MESSAGE_LENGTH = 3500


def _normalize(value):
    """None and '' are the same "unset" value across the two databases."""
    return value if value not in (None, "") else None


def _compute_diffs():
    """Returns (diffs, new_channel_names) where diffs maps channel_id to
    {"title": str, "fields": {col: new_value}, "bloats": list[str] | None}.
    """
    mixsv_sources = mixsv_db.get_mixsv_sources()
    mixsv_bloats = mixsv_db.get_mixsv_bloats()
    own_sources = {s.channel_id: s for s in db.get_all_sources()}
    own_bloats = db.get_all_bloats()

    diffs = {}
    new_channels = []

    for mixsv_source in mixsv_sources:
        own = own_sources.get(mixsv_source.channel_id)
        if own is None:
            new_channels.append(f"{mixsv_source.channel_name} ({mixsv_source.channel_id})")
            continue

        changed_fields = {}
        for field in mixsv_db.SYNC_FIELDS:
            new_value = _normalize(getattr(mixsv_source, field))
            old_value = _normalize(getattr(own, field))
            if new_value != old_value:
                changed_fields[field] = getattr(mixsv_source, field)

        new_bloats = sorted(mixsv_bloats.get(mixsv_source.channel_id, []))
        old_bloats = sorted(own_bloats.get(mixsv_source.channel_id, []))
        bloats_changed = new_bloats != old_bloats

        if changed_fields or bloats_changed:
            diffs[mixsv_source.channel_id] = {
                "title": mixsv_source.channel_name,
                "fields": changed_fields,
                "bloats": new_bloats if bloats_changed else None,
            }

    return diffs, new_channels


def _format_diff_messages(diffs: dict, new_channels: list) -> list[str]:
    messages = []
    current = ""

    def flush():
        nonlocal current
        if current:
            messages.append(current)
            current = ""

    for channel_id, diff in diffs.items():
        lines = [f"<b>{diff['title']}</b> (<code>{channel_id}</code>)"]
        for field, value in diff["fields"].items():
            lines.append(f"  • {field}: <code>{value}</code>")
        if diff["bloats"] is not None:
            lines.append(f"  • bloats: {len(diff['bloats'])} pattern(s)")
        block = "\n".join(lines) + "\n\n"

        if len(current) + len(block) > MAX_MESSAGE_LENGTH:
            flush()
        current += block

    flush()

    if new_channels:
        block = "ℹ️ In mix-sv but not yet in this bot's database (not touched by this sync):\n"
        block += "\n".join(f"  • {name}" for name in new_channels)
        messages.append(block)

    return messages


async def sync_mixsv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not mixsv_db.is_configured():
        await update.message.reply_text(
            "MIX_SV_DATABASE_URL ist nicht konfiguriert - kein Sync möglich."
        )
        return

    await update.message.reply_text("Vergleiche mix-sv mit dieser Datenbank...")

    diffs, new_channels = _compute_diffs()

    if not diffs:
        text = "Keine Unterschiede gefunden."
        if new_channels:
            text += f"\n\n{len(new_channels)} Kanal/Kanäle sind nur in mix-sv bekannt (werden hier nicht angelegt)."
        await update.message.reply_text(text)
        return

    for message in _format_diff_messages(diffs, new_channels):
        await update.message.reply_text(message)

    context.chat_data[PENDING_DIFFS] = diffs

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"✅ {len(diffs)} Änderungen übernehmen", callback_data=CONFIRM_APPLY),
        InlineKeyboardButton("❌ Abbrechen", callback_data=CONFIRM_CANCEL),
    ]])
    await update.message.reply_text(
        f"{len(diffs)} Kanal/Kanäle unterscheiden sich. Änderungen aus mix-sv übernehmen?",
        reply_markup=keyboard,
    )


async def sync_mixsv_apply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    diffs = context.chat_data.get(PENDING_DIFFS)

    if not diffs:
        await query.answer("Keine ausstehenden Änderungen mehr.")
        await query.edit_message_text("Abgelaufen - bitte /sync_mixsv erneut ausführen.")
        return

    applied = 0
    for channel_id, diff in diffs.items():
        try:
            if diff["fields"]:
                db.update_source_fields(channel_id, diff["fields"])
            if diff["bloats"] is not None:
                db.replace_bloats(channel_id, diff["bloats"])
            applied += 1
        except Exception as e:
            logging.error(f"Failed to apply mix-sv sync for channel {channel_id}: {repr(e)}")

    context.chat_data.pop(PENDING_DIFFS, None)
    await query.answer()
    await query.edit_message_text(f"✅ {applied}/{len(diffs)} Kanäle aktualisiert.")


async def sync_mixsv_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    context.chat_data.pop(PENDING_DIFFS, None)
    await query.answer()
    await query.edit_message_text("Abgebrochen - keine Änderungen übernommen.")


sync_mixsv_handler = CommandHandler("sync_mixsv", sync_mixsv, filters=filters.Chat(ADMINS))
sync_mixsv_apply_handler = CallbackQueryHandler(sync_mixsv_apply, pattern=f"^{CONFIRM_APPLY}$")
sync_mixsv_cancel_handler = CallbackQueryHandler(sync_mixsv_cancel, pattern=f"^{CONFIRM_CANCEL}$")
