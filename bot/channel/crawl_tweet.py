import asyncio
import logging
import re
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import CHANNEL_UA_RU
from bot.constant import FOOTER_UA_RU

PATTERN_TWITTER = re.compile(r"(https*://(?:twitter|x)\.com/\S+/status/\d+)")

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)


async def remove_element_by_xpath(xpath):
    try:
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].remove();", element)
    except NoSuchElementException:
        logging.warning(f"Element not found: {xpath}")


async def get_screenshot(url: str, screenshot_path: str):
    logging.info(f"Try getting {url}")
    try:
        driver.get(url)

        await remove_element_by_xpath('/html/body/div[1]/div/div/div[1]/div')
        await asyncio.sleep(10)
        await remove_element_by_xpath(
            '/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/section/div/div/div[1]/div/div/article/div/div/div[2]/div[2]/div/div/div[2]')

        driver.save_screenshot(screenshot_path)

        with Image.open(screenshot_path) as img:
            w, h = img.size
            img.crop((121, 39, w - 81, h)).save(screenshot_path)
    except:
        logging.error("Crawl failed")


async def handle_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(">>> handle twitter")
    if len(update.channel_post.text) > 600:
        return

    try:
        await update.channel_post.delete()
    except Exception as e:
        logging.error(f"Requires admin to delete message: {e}")

    url = re.findall(PATTERN_TWITTER, update.channel_post.text)[0]
    status_id = re.findall(r"status/(\d+)", url)[0]
    screenshot_path = f'img/{status_id}.png'

    await get_screenshot(url, screenshot_path)

    with open(screenshot_path, "rb") as photo:
        await context.bot.send_photo(chat_id=CHANNEL_UA_RU,
                                     photo=photo,
                                     caption=update.channel_post.text + FOOTER_UA_RU)

    Path(screenshot_path).unlink(missing_ok=True)
