import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import yt_dlp
from telegram import Update, Message
from telegram.ext import CallbackContext

YT_PATTERN = re.compile(
    r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|shorts\/|v\/)?)([\w\-]+)(?:\S+)?")

PPE = ProcessPoolExecutor()


# class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
#  def run(self, info):
#     self.to_screen('Doing stuff')
#    return [], info


async def my_hook(d, msg: Message, update: Update):
    print(d)
    if d['status'] == 'downloading':
        print('Downloading video!')

        await msg.edit_text(f"Downloading video '{d['title']}'\n\n{d['_percent_str']}%, {d['_eta_str']}")
    if d['status'] == 'finished':
        print('Downloaded!')

        print(d['destination'])
        await update.message.reply_video(f"{d['destination']}",
                                         caption=f"<b>{d['title']} - {d['uploader']}</b>\n\n{d['url']}",
                                         supports_streaming=True)

        await msg.delete()

        Path(d['destination']).unlink(missing_ok=True)


async def get_youtube_video(update: Update, context: CallbackContext):
    print(f"video ----------- {YT_PATTERN.findall(update.message.text)}")
    video_url = YT_PATTERN.findall(update.message.text)[0]
    print(video_url)
    filename = video_url[4] + ".mp4"

    #

    print("--")

    msg = await update.message.reply_text("Downloading video... please wait.")
    # await context.bot.send_chat_action(update.effective_chat.id,"Downloading video...")

    ydl_opts = {
        'outtmpl': 'vid/%(id)s.%(ext)s',
        #  "progress_hooks": [lambda d: asyncio.get_running_loop().run_in_executor(PPE, my_hook, d, msg, update)],
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        #   ydl.add_post_processor(MyCustomPP(), when='pre_process')
        ydl.download([''.join(video_url)])
