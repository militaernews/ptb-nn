import datetime
import logging
import os
import re
from itertools import islice
from typing import Dict

from pandas import read_csv
from telegram import Update
from telegram.ext import ContextTypes

from bot. settings.config import CHANNEL_UA_RU
from bot. settings.constant import FOOTER_UA_RU
from bot. util.helper import export_svg

from bot. settings.config import RES_PATH

DATA_SOURCE = r'https://docs.google.com/spreadsheets/d/1bngHbR0YPS7XH1oSA1VxoL4R34z60SJcR3NxguZM9GI/gviz/tq?tqx=out:csv&sheet=Totals'

CATEGORIES = {
    "TANK": "Kampfpanzer",
    "IFV": "Schützenpanzer",
    "APC": "Transportpanzer",
    "AFV": "Geschützte Fahrzeuge",
    "Artillery": "Rohrartillerie",
    "MLRS": "Raketenartillerie",
    "CSS": "Logistik- &amp; Zugfahrzeuge",
    "ARV": "Pionierfahrzeuge",
    "C2": "Kommandoposten",
    "Radar": "Radare",
    "EW": "EloKa",
    "FLAK": "Flugabwehrkanonen",
    "SAM": "Boden-Luft-Startgeräte",
    "Plane": "Flugzeuge",
    "Helicopter": "Hubschrauber",
    "UAV": "Kampfdrohnen",
    "Marine": "Schiffe, Boote &amp; U-Boote",
}

COLUMNS = {
    'Aircraft': 'Plane',
    'Anti-Aircraft_Guns': "FLAK",
    'Artillery_Support_Vehicles_And_Equipment': "CSS",
    'Command_Posts_And_Communications_Stations': "C2",
    'Helicopters': "Helicopter",
    'Multiple_Rocket_Launchers': "MLRS",
    'Naval_Ships': "Marine",
    'Naval_Ships_and_Submarines': "Marine",
    'Self-Propelled_Anti-Aircraft_Guns': "FLAK",
    'Self-Propelled_Artillery': "Artillery",
    'Surface-To-Air_Missile_Systems': "SAM",
    'Tanks': 'TANK',
    'Towed_Artillery': "Artillery",
    'Trucks,_Vehicles_and_Jeeps': "CSS",
    'Unmanned_Combat_Aerial_Vehicles': "UAV",
    "Radars_And_Communications_Equipment": "Radar",
    'Radars': "Radar",
    'Self-Propelled_Anti-Tank_Missile_Systems': "APC",
    'Engineering_Vehicles_And_Equipment': "ARV",
    'Armoured_Fighting_Vehicles': "IFV",
    'Infantry_Fighting_Vehicles': "IFV",
    'Armoured_Personnel_Carriers': "APC",
    'Infantry_Mobility_Vehicles': "APC",
    'Jammers_And_Deception_Systems': "EW",
    'Mine-Resistant_Ambush_Protected': "AFV",
}

STOCKPILE_RU = {
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


def get_time(delta: int = 1) -> str:
    return (datetime.datetime.now() - datetime.timedelta(days=delta)).strftime("%Y.%m.%d")


def divide(number: int, by: int) -> float:
    return round(number / by, 2)


def chunks(data, size):
    return ({k: data[k] for k in islice(iter(data), i, i + size)} for i in range(0, len(data), size))


def format_number(number):
    return f"{number:,}".replace(",", " ").replace(".", ",").replace(" ", ".")


def create_entry(x: int, y: int, total: int, new: int, description: str) -> str:
    print(f"loss: {new} - {total}")
    if new == 0:
        new_loss = ""
    elif new > 0:
        new_loss = f'<tspan style="fill:#ffd42a;">+{format_number(new)}</tspan>'
    else:  # correcting a too high value
        new_loss = f'<tspan style="fill:#34b7eb">{format_number(new)}</tspan>'

    return f""" 

    <text style="font-size:40px;font-family:Impact;" x="{x}" y="{y}">
{format_number(total)}{new_loss}<tspan dy="22px" x="{x}" style="font-size:20px;font-family:Arial;" >{description}</tspan></text>  """


def create_svg(total_losses: Dict[str, Dict[str, int]], new_losses: Dict[str, Dict[str, int]], day: str):
    field_size = 4
    all_width = 1280
    min_x = -all_width / 2
    coat_size = 300
    margin = 64
    margin_y = 8

    heading_size = 110
    heading_space = margin + heading_size

    items = list(chunks(total_losses, field_size))
    row_count = len(items * 2)
    width_cell = (all_width - (field_size + 1) * margin) / field_size
    height_cell = 90
    all_height = (row_count - 1) * margin_y + (row_count * height_cell) + 2 * margin  # + heading_space

    new_color = "#e8cc00"
    heading_color = "#ffffff"
    loss_color = "#ffffff"
    description_color = "#ffffff"
    background_color = "#be6400"

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='{min_x} 0 {all_width} {all_height}'
       version='1.1'      
       xmlns='http://www.w3.org/2000/svg'
>
 
<defs>

<linearGradient gradientTransform="rotate(-100, 0.5, 0.5)" x1="50%" y1="0%" x2="50%" y2="100%" id="gradient">
    <stop stop-color="hsl(0, 100%, 20%)" stop-opacity="1" offset="0%"/>
    <stop stop-color="hsl(180, 100%, 20%)" stop-opacity="1" offset="100%"/>
</linearGradient>

<filter id="shadow" x="0" y="0" width="1" height="1" filterUnits="objectBoundingBox" primitiveUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feGaussianBlur stdDeviation="70"/>
</filter>

</defs>

<style>
    text {{
      font-family:Arial,sans-serif;
       fill:#ffffff;
     }}
</style>
 
<rect fill="#000" height="100%" width="100%" x="{min_x}" y="0"  />
<rect  fill="url(#gradient)"  height="100%" width="100%" x="{min_x}" y="0" filter="url(#shadow)"  rx="8"  />

<image x="{-all_width / 4 - coat_size / 2}" y="{all_height / 2 - coat_size / 2}" width="{coat_size}" height="{coat_size}"  opacity="0.12" href="{RES_PATH}/img/ru_coat.svg"/>

<image x="{all_width / 4 - coat_size / 2}" y="{all_height / 2 - coat_size / 2}" width="{coat_size}" height="{coat_size}"  opacity="0.12" href="{RES_PATH}/img/ua_coat.svg" />

<text x="0" y="{(48 + 24) + margin}px" style="font-size:48px;text-anchor:middle;font-family:Impact;" >{day} <tspan style="fill:#ffd42a;">// Tag {(datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days}</tspan><tspan dy="1em"  x="0"  style="font-size:24px;font-family:'freesans-2',sans-serif;" >Wöchentliche geolokalisierte Materialverluste</tspan>
</text>
    """

    logging.info("------")

    half = len(CATEGORIES) // 2 + 1
    keys = [[*CATEGORIES][:half], [False] + [*CATEGORIES][half:]]

    positions = [(min_x, "RU"), (0, "UA")]

    for x_offset, country in positions:

        for col, outer_losses in enumerate(keys):
            for row, loss in enumerate(outer_losses):
                if loss is False:
                    continue
                svg += create_entry(
                    int(col * (width_cell + margin) + x_offset + margin),
                    int(heading_space + row * (height_cell + margin_y)),
                    total_losses[loss][country],
                    new_losses[loss][country],
                    CATEGORIES[loss]
                )
        keys.reverse()

    svg += "</svg>"

    print(svg)

    export_svg(svg, "osint_loss")


def loss_text(display_date: str, days: int, total_losses: dict, new_losses: dict, median_losses: dict,
              last_id: int) -> str:
    text = f"🔥 <b>Wöchentliche geolokalisierte Materialverluste beider Seiten bis {display_date} (Tag {days})</b>"

    text += f"\n\nMit /loss gibt es in den Kommentaren weitere Statistiken." \
            f"\n\nℹ️ <a href='https://telegra.ph/russland-ukraine-statistik-methodik-quellen-02-18'>Datengrundlage und Methodik</a>" \
            f"\n\n📊 <a href='https://t.me/Ukraine_Russland_Krieg_2022/{last_id}'>vorige Statistik</a>{FOOTER_UA_RU}"

    return text


from typing import Dict


def extract_losses(now):
    logging.info("---- requesting ---- ")
    df = read_csv(DATA_SOURCE)
    res = df[df['Date'].str.contains(now)]
    # print(res)

    san = {"RU": {}, "UA": {}}
    for col, data in res.items():
        if col.startswith(("Date", "Unnamed", "Change", "Ratio", "UNHCR")) or col.endswith(
                ("Total", "Heavy_Mortars", "Anti-Tank_Guided_Missiles", "Logistics_Trains", "Unmanned_Aerial_Vehicles",
                 "Man-Portable_Air_Defence_Systems")):
            # print(col,"---",int(data.values[0]))

            continue

        if col.startswith("Russia"):
            san["RU"][re.sub("Russia_", "", col)] = int(data.values[0])
        elif col.startswith("Ukraine"):
            san["UA"][re.sub("Ukraine_", "", col)] = int(data.values[0])

    res = {}
    for k, stats in san.items():
        for cat, v in stats.items():
            if cat not in COLUMNS:
                continue
            print(k, cat, v, COLUMNS[cat])

            if COLUMNS[cat] in res and k in res[COLUMNS[cat]]:
                res[COLUMNS[cat]][k] += v
            elif COLUMNS[cat] in res and k not in res[COLUMNS[cat]]:
                res[COLUMNS[cat]][k] = v


            else:
                res[COLUMNS[cat]] = {k: v}

    return res


def diff_dicts(dict1: Dict[str, Dict[str, int]], dict2: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    result = {}
    for outer_key in dict1.keys() & dict2.keys():
        result[outer_key] = {}
        for inner_key in dict1[outer_key].keys() & dict2[outer_key].keys():
            result[outer_key][inner_key] = dict2[outer_key][inner_key] - dict1[outer_key][inner_key]
    return result


async def get_osint_losses(context: ContextTypes.DEFAULT_TYPE):
    logging.info("get api")
    now = get_time()

    totals_today = extract_losses(now)

    #  print(dumps(totals_today, ensure_ascii=False, sort_keys=True, indent=2, default=str))

    diff_loss = diff_dicts(extract_losses(get_time(8)), totals_today)

    # print(dumps(diff_loss, ensure_ascii=False, sort_keys=True, indent=2, default=str))

    print("---- found ---- ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))

    days = (datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days
    display_date = datetime.datetime.now().strftime("%d.%m.%Y")

    create_svg(totals_today, diff_loss, display_date)

    last_id = context.bot_data.get("last_loss_id_2", 71462)
    text = loss_text(display_date, days, totals_today, diff_loss, {}, last_id)

    with open("osint_loss.png", "rb") as f:
        msg = await context.bot.send_photo(CHANNEL_UA_RU, photo=f, caption=text)

    context.bot_data["last_loss_2"] = now
    context.bot_data["last_loss_id_2"] = msg.id


async def setup_osint_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("setup osint")
    #  context.bot_data.pop("last_loss", "")
    #    context.bot_data.pop("last_loss_id_2", 18147)
    await get_osint_losses(context)
    context.job_queue.run_repeating(get_osint_losses, datetime.timedelta(days=7))
    await update.message.reply_text("Scheduled Osint.")
