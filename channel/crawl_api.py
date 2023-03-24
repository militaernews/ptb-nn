import datetime
import json
import logging
from itertools import islice
from typing import Dict

import cairosvg
import httpx
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext

import config

LOSS_DESCRIPTIONS = {
    'tanks': "Panzer",
    'apv': "Gepanzerte Fahrzeuge",
    'artillery': "Artilleriesysteme",
    'mlrs': "Mehrfachraketenwerfer",
    'aaws': "Luftverteidigungssysteme",
    'aircraft': "Flugzeuge",
    'helicopters': "Hubschrauber",
    'uav': "Drohnen",
    'vehicles': "Lastkraftwagen",
    'boats': "Schiffe",
    'se': "Spezialausrüstung",
    'missiles': "Marschflugkörper",
    'personnel': "Getötetes Personal",
    "presidents": "Präsidenten"
}

LOSS_STOCKPILE = {
    'tanks': 8168,
    'apv': 26993,
    'artillery': 10991,
    'mlrs': 4300,
    'aaws': 3422,
    'aircraft': 1551,
    'helicopters': 1098,
    'uav': 5028,
    'vehicles': 98567,
    'boats': 773,
    'se': 1400,
    'personnel': 1500000,
}


def get_time() -> str:
    return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y.%m.%d")


def divide(number: int, by: int) -> float:
    return round(number / by, 2)


def chunks(data, size):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def format_number(number: int):
    return f"{number:,}".replace(",", "║").replace(".", ",").replace("║", ".")


def create_svg(total_losses: Dict[str, int], new_losses: Dict[str, int], day: str):
    field_size = 2
    all_width = 1342
    margin = 24

    heading_size = 46
    heading_space = margin * 2.5 + heading_size

    items = list(chunks(total_losses, field_size))
    row_count = len(items)
    width_cell = (all_width - (field_size + 1) * margin) / field_size
    height_cell = 160
    all_height = row_count * (margin + height_cell) + heading_space

    new_color = "#e8cc00"
    heading_color = "white"
    loss_color = "white"
    description_color = "white"
    background_color = "black"

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='0 0 {all_width} {all_height}'
       version='1.1'
       xmlns='http://www.w3.org/2000/svg'
       xmlns:svg='http://www.w3.org/2000/svg'>
       <defs>
   <linearGradient id="lgrad" x1="0%" y1="50%" x2="100%" y2="50%" >
    
                   
     <stop offset="0%" style="stop-color:rgb(5,45,31);stop-opacity:1.00" />
          <stop offset="100%" style="stop-color:rgb(23,46,41);stop-opacity:1.00" />

    </linearGradient>
  </defs>
        <text
            x="50%"
            y="{heading_size + margin}"
            text-anchor="middle"
            font-size="{heading_size}"
            fill="{heading_color}"
            font-family="Bahnschrift">Russische Verluste in der Ukraine - {day}</text>
    """

    print("------")

    for y, item in enumerate(items):
        logging.info(f"items :: {item}")

        for x, (k, v) in enumerate(item.items()):
            #    print(y, x, "--", k, v)
            # fill="#002a24" stroke="#2c5a2b" # stroke="gray" stroke-width="{stroke_width}"
            svg += f"""
        <rect
            width='{width_cell}'
            height='{height_cell}'
            x='{x * width_cell + (x + 1) * margin}'
            y="{(y * height_cell) + y * margin + heading_space}"
            paint-order="fill"
            rx="16"
            fill="url(#lgrad)"
          />

        <text
            x="{x * width_cell + (x + 2) * margin}"
            y="{(y * height_cell) + (y + 2.2) * margin + heading_space}"
            text-anchor="start"
            dominant-baseline="central"
            font-size="58px"
            font-family="Bahnschrift"
            fill="{loss_color}">{format_number(v)}<tspan """

            if k != "presidents" and new_losses[k] != 0:
                svg += f"fill='{new_color}'> +{format_number(new_losses[k])}</tspan><tspan "

            svg += f"""dy="1.5em"
            text-anchor="start"
            fill="{description_color}"
            x="{x * width_cell + (x + 2) * margin}"
            font-size="42px">{LOSS_DESCRIPTIONS[k]}</tspan>
        </text>"""

            if k in LOSS_STOCKPILE and LOSS_STOCKPILE[k] != 0:
                svg += f"""<text x="{(x + 1) * width_cell + x * margin}" y="{(y * height_cell) + (y + 1) * margin + heading_space}"
                 text-anchor="end" font-size="36px" font-family="Bahnschrift" fill="lightgrey" dominant-baseline="top">{str(divide(v * 100, LOSS_STOCKPILE[k])).replace(".", ",")}%</text>"""

    svg += f"""
    
    <g transform="translate(50%, 50%)">
       <text
            text-anchor="middle"
            transform="rotate(-45)"
            font-size="{heading_size * 1.6}"
            fill-opacity="0.1"
            fill="#a1ffff" >@Ukraine_Russland_Krieg_2022</text>
    </g>
    
</svg>"""

    print(svg)

    cairosvg.svg2png(bytestring=svg, write_to='loss.png', background_color=background_color)


create_svg({
    'personnel': 161520, 'tanks': 3492, 'apv': 6799, 'artillery': 2528,
    'mlrs': 502, 'aaws': 262,
    'aircraft': 304, 'helicopters': 289,
    'vehicles': 5377, 'boats': 18, 'se': 257, 'uav': 2132,
    'missiles': 907, 'presidents': 0
}, {
    'personnel': 980, 'tanks': 8, 'apv': 10, 'artillery': 9,
    'mlrs': 7, 'aaws': 2,
    'aircraft': 0, 'helicopters': 0,
    'vehicles': 10, 'boats': 0, 'se': 1, 'uav': 12,
    'missiles': 0, 'presidents': 0
}, "15.03.2023")


async def get_api(context: CallbackContext):
    print("get api")
    key = context.bot_data.get("last_loss", "")
    now = get_time()
    print("crawl: ", key, now)

    logging.info(f">>>> waiting... {datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S')} :: {key} :: {now}")

    if key != now:
        logging.info("---- requesting ---- ")

        res = httpx.get('https://russian-casualties.in.ua/api/v1/data/json/daily')
        data = json.load(res)["data"]
        #  print(data)

        try:
            new_losses = data[now]
            new_losses.pop("captive")

        except KeyError as e:
            print("Could not get entry with key: ", e)
            return

        total_losses = {
            'personnel': 0,
            'tanks': 0,
            'apv': 0,
            'artillery': 0,
            'mlrs': 0,
            'aaws': 0,
            'aircraft': 0,
            'helicopters': 0,
            'vehicles': 0,
            'boats': 0,
            'se': 0,
            'uav': 0,
            'missiles': 0,
            'presidents': 0
        }

        for day, item in data.items():
            #  print(day)

            for k, v in item.items():
                #   print(k, v)

                if k != "captive":
                    total_losses[k] = total_losses[k] + v

        print("---- found ---- ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))

        days = (datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days
        display_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

        create_svg(total_losses, new_losses, display_date)

        text = f"🔥 <b>Russische Verluste bis zum {display_date} (Tag {days})</b>"
        for k, v in total_losses.items():
            if k != "presidents" and new_losses[k] != 0:
                daily = round(v / days, 1)
                text += f"\n\n<b>{LOSS_DESCRIPTIONS[k]} +{format_number(new_losses[k])}</b>\n• {format_number(daily)} pro Tag"
                if k in LOSS_STOCKPILE:
                    text += f"\n• Lagerbestand noch {format_number(round((LOSS_STOCKPILE[k] - v) / daily))} Tage"

        last_id = context.bot_data.get("last_loss_id", 1)

        text += f"\n\nMit /loss gibt es in den Kommentaren weitere Statistiken.\n\nℹ️ <a href='https://telegra.ph/russland-ukraine-statistik-methodik-quellen-02-18'>Datengrundlage und Methodik</a>\n\n📊 <a href='https://t.me/invasion_ukraine/{last_id}'>vorige Statistik</a>{config.FOOTER}"

        logging.info(text)

        with open("loss.png", "rb") as f:
            msg = await context.bot.send_photo(config.CHANNEL, photo=f, caption=text)

        context.bot_data["last_loss"] = now
        context.bot_data["last_loss_id"] = msg.id


async def setup_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("setup crawl")
    #  context.bot_data.pop("last_loss", "")
    #    context.bot_data.pop("last_loss_id", 18147)
    await get_api(context)
    print("help?")
    context.job_queue.run_repeating(get_api, datetime.timedelta(hours=2))
    await update.message.reply_text("Scheduled Api Crawler.")
