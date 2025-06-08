import logging
import re
from functools import wraps

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.helpers import mention_html

from bot. settings import config
from bot. util.helper import get_text2
from bot. util.regex import JOIN_ID

share_text = "\n🚨 Nyx News — Aggregierte Nachrichten aus aller Welt mit Quellenangabe und gekennzeichneter Voreingenommenheit der Quelle."


def log_errors(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        try:
            await func(update, context)
        except Exception as e:
            logging.error(e)

    return wrapper


def create_inline_keyboard(button_text, button_url=None, callback_data=None):
    return InlineKeyboardMarkup.from_button(
        InlineKeyboardButton(button_text, url=button_url, callback_data=callback_data)
    )


@log_errors
async def join_request_buttons(update: Update, context: CallbackContext):
    await context.bot.approve_chat_join_request(update.chat_join_request.chat.id, update.effective_user.id)
    await update.chat_join_request.from_user.send_photo(
        open("res/img/nn_info.jpg", "rb"),
        caption=f"Herzlich Willkommen, {update.chat_join_request.from_user.name} ✌🏼\n\n{get_text2(update.chat_join_request.from_user, 'how')}",
        reply_markup=create_inline_keyboard("Kanal teilen ⏩",
                                            button_url=f"https://t.me/share/url?url=https://t.me/nyx_news&text={share_text}")
    )


@log_errors
async def accept_join_request(update: Update, context: CallbackContext):
    chat_id = re.findall(JOIN_ID, update.callback_query.data)[0]
    await context.bot.approve_chat_join_request(chat_id, update.effective_user.id)
    await update.callback_query.edit_message_caption(
        f"{get_text2(update.callback_query.from_user, 'how')}\n\n<b>Herzlich Willkommen! Bitte teile Nyx News mit deinen Kontakten</b> 😊",
        reply_markup=create_inline_keyboard("Kanal teilen ⏩",
                                            button_url=f"https://t.me/share/url?url=https://t.me/nyx_news&text={share_text}")
    )
    await update.callback_query.answer()


@log_errors
async def join_request_ug(update: Update, context: CallbackContext):
    await context.bot.send_message(update.chat_join_request.from_user.id,
                                   f"Hey, {update.chat_join_request.from_user.name} ✌️\n\n"
                                   """⚖️ <u>Regeln dieses Forums</u>
   
   1. Inhalte sollen nachgewiesen sein, bspw. durch Bilder/Videos des Ortes. Eine exakte Geolokalisierung nicht nötig, nur wenigstens mit Ortsangabe.
   
   
   2.  Auch eine Verlinkung auf Originalquellen (vorzugsweise offizielle Stellen, Thinktanks) sollte stattfinden. Wünschenswert wäre die Sicherung eines Links mit archive.is oder archive.ph.
   
   
   3. Inhalte haben im Topic zu denen es am besten passt gepostet zu werden. Regions-Topics gehen vor.
   
   
   4. Wenn etwas nur in mehreren Regionen passiert und noch immer ein starker Bezug zu den Regionen vorherrscht, dann ist es nur in einer der Regions-Topics zu posten.
   
   
   5. Reposts gilt es zu vermeiden, sofern diese nicht weitere Informationen liefern oder einen Sachverhalt erklären.
   
   
   6. Bitte nur Inhalte mit engem Bezug zur Ukraine posten. Diese sollten einen größeren Mehrwert an Informationen bieten, mit denen die aktuelle Lage eingeschätzt werden kann.
   
   
   <u>Beispiele für relevante Inhalte</u>
   
   a) Ukraine/Russland nehmen eine größere Stellung ein oder verlieren diese.
   
   b) Ukraine/Russland verlieren/nutzen eine besonders große Menge an Material in einer Richtung binnen weniger Tage.
   
   c) Ukraine/Russland verlieren/nutzen nur in geringer Stückzahl verfügbares an Material.
   
   d) Ukraine/Russland bekommen neue Ausrüstung von ihren Partnern, bzw. die finale Entscheidung dazu fällt.
   
   e) Ein medial sehr präsenter Vorfall ereignet sich (etwa auf dem Niveau der abgeschossenen Il-76) und aufgrund der unklaren Situation sollten Belege zusammengetragen werden.
   
   
   Es geht nicht darum wie ein Newsticker zu fungieren, sondern Informationen zu einem Thema zu sammeln und sich darüber auszutauschen. Diese Gruppe soll nicht das Pendant zu @nyx_news oder @Ukraine_Russland_Krieg_2022 sein. Wer behauptet, der belegt auf Nachfrage.
   
   <b>Bitte fragt dich immer bevor du etwas sendest, ob es wirklich entscheidend und aus Sicht anderer Mitglieder relevant ist.</b>""",
                                   reply_markup=create_inline_keyboard("Gruppe beitreten ➡️",
                                                                       callback_data=f"ugreq_{update.chat_join_request.from_user.id}_{update.chat_join_request.from_user.name}")
                                   )


@log_errors
async def accept_rules_ug(update: Update, context: CallbackContext):
    user_id, name = update.callback_query.data.split("_")[1:]
    msg = update.callback_query.message
    await context.bot.send_message(config.UG_ADMIN,
                                   f"Beitrittsanfrage von {mention_html(user_id, name)}",
                                   reply_markup=InlineKeyboardMarkup([[
                                       InlineKeyboardButton("Zulassen ✅", callback_data=f"ugyes_{user_id}_{msg.id}"),
                                       InlineKeyboardButton("Ablehnen❌", callback_data=f"ugno_{user_id}_{msg.id}")
                                   ]]))
    await update.callback_query.edit_message_text(
        f"{msg.text}\n\n✅ <b>Anfrage gesendet. Die Admins überprüfen dein Profil.</b>", reply_markup=None)


@log_errors
async def decline_request_ug(update: Update, context: CallbackContext):
    user_id, msg_id = update.callback_query.data.split("_")[1:]
    await context.bot.decline_chat_join_request(config.UG_LZ, int(user_id))
    await context.bot.delete_message(int(user_id), int(msg_id))
    await update.callback_query.message.delete()


@log_errors
async def accept_request_ug(update: Update, context: CallbackContext):
    user_id, msg_id = update.callback_query.data.split("_")[1:]
    await context.bot.approve_chat_join_request(config.UG_LZ, int(user_id))
    await context.bot.delete_message(int(user_id), int(msg_id))
    await context.bot.send_photo(
        int(user_id),
        open("res/img/nn_info.jpg", "rb"),
        caption="Herzlich willkommen im Lagezentrum von @ukr_ger!\n\n🚨 Vielleicht gefällt dir auch <b>@newsmix_ukraine</b> — Aggregierte Nachrichten aus aller Welt mit Quellenangabe und gekennzeichneter Voreingenommenheit der Quelle.",
        reply_markup=create_inline_keyboard("Kanal beitreten ✅", button_url="https://t.me/newsmix_ukraine")
    )
    await update.callback_query.message.delete()
