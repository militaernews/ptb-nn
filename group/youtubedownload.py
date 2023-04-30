import re
from pathlib import Path

from pytube import YouTube
from telegram import Update
from telegram.ext import CallbackContext

YT_PATTERN = re.compile(
    r"((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|shorts\/|v\/)?)([\w\-]+)(?:\S+)?")


async def get_youtube_video(update: Update, context: CallbackContext):
    print(f"video ----------- {YT_PATTERN.findall(update.message.text)}")
    video_url = YT_PATTERN.findall(update.message.text)[0]
    print(video_url)
    filename = video_url[4] + ".mp4"

    #

    print("--")

    video_path = YouTube(f"https://www.youtube.com/embed/{video_url[4]}?feature=oembed",
                         use_oauth=True,
                         allow_oauth_cache=True,
                         )\
        .streams\
        .filter(progressive=True, file_extension='mp4')\
        .order_by('resolution')\
        .desc()\
        .first()

    print(video_path)

    msg = await update.message.reply_text("Downloading video... please wait.")

    file_path = video_path.download(output_path="vid", filename=filename)

    await update.message.reply_video(file_path,
                                     caption=f"<b>{video_path.title}</b>\n\n{''.join(video_url)}",
                                     supports_streaming=True)

    await msg.delete()

    Path(file_path).unlink(missing_ok=True)
