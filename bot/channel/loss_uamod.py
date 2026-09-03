import datetime
import logging
from itertools import islice
from statistics import median
from typing import Dict, List, Optional

import httpx
from telegram import Update
from telegram.ext import ContextTypes

from bot.settings.config import CHANNEL_UA_RU
from bot.util.helper import export_svg

# Daily Russian equipment/personnel losses compiled from official Ukrainian
# Ministry of Defence reports (mod.gov.ua) - each entry's "sourceUri" links
# straight to the day's mod.gov.ua announcement. Replaces
# russian-casualties.in.ua, which started 403'ing every request from this
# host (Cloudflare bot-challenge on our IP, not something fixable in code).
DATA_SOURCE = 'https://raw.githubusercontent.com/lod-db/orc-losses/main/russian-losses.json'

# Our category keys -> field names in the orc-losses JSON.
FIELD_MAP = {
    'personnel': 'personnel',
    'tanks': 'tanks',
    'apv': 'afvs',
    'artillery': 'artillery',
    'mlrs': 'rocketSystems',
    'aaws': 'airDefense',
    'aircraft': 'fixedWingAircraft',
    'helicopters': 'rotaryWingAircraft',
    'uav': 'uavs',
    'vehicles': 'unarmoredVehicles',
    'se': 'specialEquipment',
    'missiles': 'missiles',
}
# 'boats' isn't in FIELD_MAP: it's ships+submarines summed, handled in _extract.

LOSS_DESCRIPTIONS = {
    'tanks': "Panzer",
    'apv': "Gepanzerte Fahrzeuge",
    'artillery': "Artillerie",
    'mlrs': "Mehrfachraketenwerfer",
    'aaws': "Flugabwehr",
    'aircraft': "Flugzeuge",
    'helicopters': "Hubschrauber",
    'uav': "Drohnen",
    'vehicles': "Lastkraftwagen",
    'boats': "Marine",
    'se': "Spezialausrüstung",
    'missiles': "Marschflugkörper",
    'personnel': "Personal (Tot/Verwundet)",
}

LOSS_STOCKPILE = {
    'tanks': 8168,
    'apv': 26993,
    'artillery': 18007,
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
    return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")


def divide(number: int, by: int) -> float:
    return round(number / by, 2)


def chunks(data, size):
    it = iter(data)
    for _ in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def format_number(number: int):
    return f"{number:,}".replace(",", "║").replace(".", ",").replace("║", ".")


def _extract(entry: dict) -> Dict[str, int]:
    """Map one orc-losses day entry to our category keys."""
    result = {cat: entry.get(field) or 0 for cat, field in FIELD_MAP.items()}
    result['boats'] = (entry.get('ships') or 0) + (entry.get('submarines') or 0)
    return result


def create_svg(total_losses: Dict[str, int], new_losses: Dict[str, int], day: str):
    field_size = 2
    all_width = 1400
    margin = 24

    heading_size = 42
    heading_space = margin * 2.5 + heading_size

    items = list(chunks(total_losses, field_size))
    row_count = len(items)
    width_cell = (all_width - (field_size + 1) * margin) / field_size
    height_cell = 160
    all_height = row_count * (margin + height_cell) + heading_space

    new_color = "#e8cc00"
    heading_color = "#ffffff"
    loss_color = "#ffffff"
    description_color = "#ffffff"
    background_color = "#000000"

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
          <stop offset="100%" style="stop-color:rgb(184, 73, 39);stop-opacity:1.00" />

    </linearGradient>
</defs>

<style>
    text {{
      font-family:Arial,sans-serif;
       fill:#ffffff;
     }}
</style>

<rect width="100%" height="100%"   fill='{background_color}'/>
        <text
            x="50%"
            y="{heading_size + margin}"
            text-anchor="middle"
            fill="{heading_color}"
            style="font-size:{heading_size}px;font-family:Impact;">Verluste Russlands laut Verteidigungsministerium Ukraine - {day}</text>
    """

    logging.info("------")

    for y, item in enumerate(items):
        logging.info(f"items :: {item}")

        for x, (k, v) in enumerate(item.items()):
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
            style="font-size:58px;font-family:Impact;"
            fill="{loss_color}">{format_number(v)}<tspan """

            if new_losses[k] != 0:
                svg += f"fill='{new_color}'> +{format_number(new_losses[k])}</tspan><tspan "

            svg += f"""dy="1.5em"
            text-anchor="start"
            fill="{description_color}"
            x="{x * width_cell + (x + 2) * margin}"
   style="font-size:42px;font-family:Arial;">{LOSS_DESCRIPTIONS[k]}</tspan>
        </text>"""

            if k in LOSS_STOCKPILE and LOSS_STOCKPILE[k] != 0:
                percentage = f"{v * 100 / LOSS_STOCKPILE[k]:.2f}".replace(".", ",")
                svg += f"""<text x="{(x + 1) * width_cell + x * margin}" y="{y * height_cell + (y + 2) * margin + heading_space}"
                 text-anchor="end" style="font-size:36px;font-family:Impact;" fill="#D3D3D3" dominant-baseline="text-top">{percentage}%</text>"""

    svg += """

    <g transform="translate(50%, 50%)">
       <text
            text-anchor="middle"
            transform="rotate(-45)"
            font-size="72"
            fill-opacity="0.1"
            fill="#a1ffff" >@Ukraine_Russland_Krieg_2022</text>
    </g>

</svg>"""

    export_svg(svg, "uamod_loss")


async def get_uamod_losses(context: ContextTypes.DEFAULT_TYPE):
    logging.info("get api")
    key = context.bot_data.get("last_loss", "")
    now = get_time()

    logging.info(f">>>> waiting... {datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S')} :: {key} :: {now}")

    if key == now:
        return

    logging.info("---- requesting ---- ")

    try:
        res = httpx.get(DATA_SOURCE, timeout=30.0)
        res.raise_for_status()
        entries: List[dict] = res.json()
        if not isinstance(entries, list) or not entries:
            logging.error(f"Unexpected orc-losses response shape: {res.text[:200]}")
            return
    except (httpx.HTTPError, ValueError) as e:
        logging.error(f"Failed to fetch or parse orc-losses data: {repr(e)}")
        return

    # Entries are newest-first; find today's and the one right before it.
    today_index: Optional[int] = next((i for i, e in enumerate(entries) if e.get('date') == now), None)
    if today_index is None:
        logging.warning(f"Entry for {now} not yet available in orc-losses data.")
        return

    total_losses = _extract(entries[today_index])
    prev_entry = entries[today_index + 1] if today_index + 1 < len(entries) else None
    prev_totals = _extract(prev_entry) if prev_entry else {cat: 0 for cat in total_losses}
    new_losses = {cat: total_losses[cat] - prev_totals[cat] for cat in total_losses}

    # Day-over-day deltas across the whole history, for the "Median" stat.
    median_losses: Dict[str, list] = {cat: [] for cat in total_losses}
    for i in range(len(entries) - 1):
        cur = _extract(entries[i])
        prev = _extract(entries[i + 1])
        for cat in total_losses:
            median_losses[cat].append(cur[cat] - prev[cat])

    print("---- found ---- ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))

    days = (datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days
    display_date = (datetime.datetime.now()).strftime("%d.%m.%Y")

    create_svg(total_losses, new_losses, display_date)

    text = f"🔥 <b>Russische Verluste bis {display_date} (Tag {days})</b>"
    for k, v in total_losses.items():
        if new_losses[k] != 0:
            daily = round(v / days, 1)
            text += f"\n\n<b>{LOSS_DESCRIPTIONS[k]} +{format_number(new_losses[k])}</b>\n• {format_number(daily)} pro Tag, Median {int(median(median_losses[k])) if median_losses[k] else 0}"
            if k in LOSS_STOCKPILE:
                storage = "Uniformiert" if k == "personnel" else "Lagerbestand"
                text += f"\n• {storage} noch {format_number(round((LOSS_STOCKPILE[k] - v) / daily))} Tage"

    last_id = context.bot_data.get("last_loss_id", 1)

    text += f"\n\nMit /loss gibt es in den Kommentaren weitere Statistiken." \
            f"\n\nℹ️ <a href='https://telegra.ph/russland-ukraine-statistik-methodik-quellen-02-18'>Datengrundlage und Methodik</a>" \
            f"\n\n📊 <a href='https://t.me/Ukraine_Russland_Krieg_2022/{last_id}'>vorige Statistik</a>"

    logging.info(text)

    with open("uamod_loss.png", "rb") as f:
        msg = await context.bot.send_photo(CHANNEL_UA_RU, photo=f, caption=text)

    context.bot_data["last_loss"] = now
    context.bot_data["last_loss_id"] = msg.id


async def setup_uamod_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("setup crawl")
    #  context.bot_data.pop("last_loss", "")
    #    context.bot_data.pop("last_loss_id", 18147)
    await get_uamod_losses(context)
    logging.info("help?")
    context.job_queue.run_repeating(get_uamod_losses, datetime.timedelta(hours=1.5))
    await update.message.reply_text("Scheduled Api Crawler.")
