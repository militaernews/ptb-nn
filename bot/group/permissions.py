import logging

from telegram import Update
from telegram.ext import Application, ChatMemberHandler, ContextTypes

REQUIRED_GROUP_PERMISSIONS = ("delete_messages", "restrict_members", "invite_users")

logger = logging.getLogger(__name__)


async def handle_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When the bot is added to (or promoted/demoted in) a group, tell the group
    which admin rights it needs for moderation (warn/ban) and approving join requests.
    """
    result = update.my_chat_member
    if result.chat.type not in ("group", "supergroup"):
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    if old_status == new_status:
        return

    if new_status == "administrator":
        member = result.new_chat_member
        missing = [p for p in REQUIRED_GROUP_PERMISSIONS if not getattr(member, f"can_{p}", False)]
        if not missing:
            return
        text = (
            "⚠️ Danke, dass ich Admin bin, aber mir fehlen noch:\n"
            + "\n".join(f"• can_{p}" for p in missing)
            + "\n\nBitte diese Rechte ergänzen, damit ich verwarnen, bannen und Beitrittsanfragen bearbeiten kann."
        )
    elif new_status == "member":
        text = (
            "👋 Danke für's Hinzufügen! Damit ich Regelverstöße ahnden und Beitrittsanfragen "
            f"bearbeiten kann, mache mich bitte zum Admin mit den Rechten "
            f"{', '.join(f'can_{p}' for p in REQUIRED_GROUP_PERMISSIONS)}."
        )
    else:
        return

    try:
        await context.bot.send_message(result.chat.id, text)
    except Exception as e:
        logger.warning(f"Could not post permission notice in {result.chat.id}: {e}")


def register_permissions(app: Application):
    app.add_handler(ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
