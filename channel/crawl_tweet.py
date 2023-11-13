import asyncio
import logging
import re
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update
from telegram.ext import ContextTypes

from config import CHANNEL_UA_RU
from constant import FOOTER_UA_RU

PATTERN_TWITTER = re.compile(r"(https*://(?:twitter|x)\.com/\S+/status/\d+)")

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)


async def get_screenshot(url: str, screenshot_path: str):
    logging.info(f"Try getting {url}")
    driver.get(url)

    try:
        banner = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div')
        driver.execute_script("arguments[0].remove();", banner)
    except:
        pass
    await asyncio.sleep(10)

    try:
        three_dots = driver.find_element(By.XPATH,
                                         '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/section/div/div/div[1]/div/div/article/div/div/div[2]/div[2]/div/div/div[2]')
        driver.execute_script("arguments[0].remove();", three_dots)
    except:
        pass

    driver.save_screenshot(screenshot_path)

    img = Image.open(screenshot_path)
    w, h = img.size
    img.crop((121, 39, w - 81, h)).save(screenshot_path)


async def handle_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("twitter")
    if len(update.channel_post.text) > 600:
        return

    try:
        await update.channel_post.delete()
    except:
        logging.error("Requires admin to delete message")

    url = re.findall(PATTERN_TWITTER, update.channel_post.text)[0]
    status_id = re.findall(r"status/(\d+)", url)[0]
    screenshot_path = f'img/{status_id}.png'

    await get_screenshot(url, screenshot_path)

    await context.bot.send_photo(chat_id=CHANNEL_UA_RU,
                                 photo=open(screenshot_path, "rb"),
                                 caption=update.channel_post.text + FOOTER_UA_RU)

    Path(screenshot_path).unlink(missing_ok=True)
