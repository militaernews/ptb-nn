import asyncio
import datetime
import subprocess
import logging
import re
from itertools import islice
from json import dumps, load
from statistics import median
from typing import Dict, TypedDict

import cairosvg
import httpx
from pandas import read_csv
#from resvg_python import svg_to_bytes
from telegram import Update
from telegram.ext import ContextTypes

import config
#import constant
#from util.helper import export_svg

DATA_SOURCE = r'https://docs.google.com/spreadsheets/d/1bngHbR0YPS7XH1oSA1VxoL4R34z60SJcR3NxguZM9GI/gviz/tq?tqx=out:csv&sheet=Totals'

CATEGORIES ={
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
    "EW": "Elektronische Kampfführung",
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


def get_time() -> str:
    return (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y.%m.%d")


def divide(number: int, by: int) -> float:
    return round(number / by, 2)


def chunks(data, size):
    return ({k: data[k] for k in islice(iter(data), i, i + size)} for i in range(0, len(data), size))


def format_number(number):
    return f"{number:,}".replace(",", " ").replace(".", ",").replace(" ", ".")

def export_svg(svg: str, filename: str):
    logging.info(svg)

    input_filename = filename.replace(".png", ".svg")

    with open(input_filename, "w", encoding='utf-8')as f:
        f.write(svg)

    command = fr'../tools/resvg "{input_filename}" loss4.png --skip-system-fonts --background "#000000" --dpi 300 --font-family "Arial" --use-fonts-dir "../res/fonts"'
    result = subprocess.run(command, stdout=subprocess.PIPE)

    print("---\n\n\n\n\nRESVG: ", result.returncode, result)
    print(result.returncode)

def create_watermark():
    return """
    <g  x="50%" y="50%">
       <text
            text-anchor="middle"
            transform="rotate(-45)"
           
            font-size="75px"
            fill-opacity="0.1"
            fill="#a1ffff" >@Ukraine_Russland_Krieg_2022</text>
    </g>
    </svg>"""


def create_entry(x: int, y: int, total: int, new: int, description: str) -> str:
    return f""" 

    <text style="font-size:40px;font-family:Impact;fill:#ffffff;" x="{x}" y="{y}">
{format_number(total)}<tspan style="fill:#ffd42a">+{format_number(new)}</tspan><tspan dy="22px" x="{x}" style="font-size:20px;font-family:Arial;" >{description}</tspan></text>  """

def create_svg(total_losses: Dict[str, Dict[str,int]], new_losses: Dict[str, Dict[str,int]], day: str):
    field_size = 2
    all_width = 1300
    coat_size = 300
    margin = 24

    heading_size = 26
    heading_space = margin * 2.5 + heading_size

    items = list(chunks(total_losses, field_size))
    row_count = len(items)
    width_cell = (all_width - (field_size + 1) * margin) / field_size
    height_cell = 90
    all_height = (row_count-1) * (margin + height_cell) # + heading_space

    new_color = "#e8cc00"
    heading_color = "#ffffff"
    loss_color = "#ffffff"
    description_color = "#ffffff"
    background_color = "#be6400"

    svg = f"""<?xml version='1.0' encoding='UTF-8' standalone='no'?>
    <svg
       width='{all_width}'
       height='{all_height}'
       viewBox='0 0 {all_width} {all_height}'
       version='1.1'      
       xmlns='http://www.w3.org/2000/svg'
       xmlns:svg='http://www.w3.org/2000/svg'>
 
<defs>

<linearGradient gradientTransform="rotate(-100, 0.5, 0.5)" x1="50%" y1="0%" x2="50%" y2="100%" id="gradient">
    <stop stop-color="hsl(0, 100%, 20%)" stop-opacity="1" offset="0%"/>
    <stop stop-color="hsl(180, 100%, 20%)" stop-opacity="1" offset="100%"/>
</linearGradient>

<filter id="shadow" x="0" y="0" width="1" height="1" filterUnits="objectBoundingBox" primitiveUnits="userSpaceOnUse" color-interpolation-filters="sRGB">
  <feGaussianBlur stdDeviation="70"/>
</filter>

</defs>
 
     <rect fill="#000" height="100%" width="100%" x="0" y="0"  />
 <rect  fill="url(#gradient)"  height="100%" width="100%" x="0" y="0" filter="url(#shadow)"  rx="8"  />
 
<image x="{all_width/4-coat_size/2}" y="{all_height/2 -coat_size/2}" width="{coat_size}" height="{coat_size}"  opacity="0.15" href="./ru_coat.svg"/>

<image x="{all_width/4 *3-coat_size/2}" y="{all_height/2-coat_size/2}" width="{coat_size}" height="{coat_size}"  opacity="0.15" href="./ua_coat.svg" />

            <text  style="font-size:48px;font-family:Impact;text-anchor:middle;fill:#ffffff;"
       x="{all_width/2}"  y="90">{day} <tspan style="fill:#ffd42a;">// Tag {(datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days}</tspan><tspan
dy="1em"  x="{all_width/2}"  style="font-size:36px;font-family:Arial;fill:#ffffff;">Geolokalisierte Materialverluste</tspan></text>
    """

    logging.info("------")

    half = len(CATEGORIES) // 2 + 1
    keys = [[*CATEGORIES][:half], [False] + [*CATEGORIES][half:]]

    positions = [(60, "RU"), (660, "UA")]

    for x_offset, country in positions:
        for col, outer_losses in enumerate(keys):
            for row, loss in enumerate(outer_losses):
                if loss is False:
                    continue
                svg += create_entry(
                    x_offset + col * 300,
                    110 + row * height_cell,
                    total_losses[loss][country],
                    new_losses[loss][country],
                    CATEGORIES[loss]
                )
        keys.reverse()


    svg += create_watermark()

   # print(svg)

    export_svg(svg, "loss.png")


def loss_text(display_date: str, days: int, total_losses: dict, new_losses: dict, median_losses: dict,
              last_id: int) -> str:
    text = f"🔥 <b>Geolokalisierte Materialverluste beider Seiten bis {display_date} (Tag {days})</b>"

    text += f"\n\nMit /loss gibt es in den Kommentaren weitere Statistiken." \
            f"\n\nℹ️ <a href='https://telegra.ph/russland-ukraine-statistik-methodik-quellen-02-18'>Datengrundlage und Methodik</a>" \
            f"\n\n📊 <a href='https://t.me/Ukraine_Russland_Krieg_2022/{last_id}'>vorige Statistik</a>{'ff'}"

    return text





from typing import Dict

def diff_dicts(dict1: Dict[str, Dict[str, int]], dict2: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
    result = {}
    for outer_key in dict1.keys() & dict2.keys():
        result[outer_key] = {}
        for inner_key in dict1[outer_key].keys() & dict2[outer_key].keys():
            result[outer_key][inner_key] = dict2[outer_key][inner_key] - dict1[outer_key][inner_key]
    return result

def extract_losses(now):
    logging.info("---- requesting ---- ")
    df =read_csv(DATA_SOURCE)
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

    return san

async def get_api(context: ContextTypes.DEFAULT_TYPE):
    logging.info("get api")
    if context is not None:
        key = context.bot_data.get("last_loss", "")
    else:
        key  = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y.%m.%d")
    now = get_time()
    logging.info(f">>>> waiting... {datetime.datetime.now().strftime('%d.%m.%Y, %H:%M:%S')} :: {key} :: {now}")

    if key == now:
        return



    raw = extract_losses(now)

  #  print(raw)

    totals = {}

    for k, stats in raw.items():
        for cat, v in stats.items():
            if cat not in COLUMNS:
                continue
            print(k, cat, v, COLUMNS[cat])

            if COLUMNS[cat] in totals and k in totals[COLUMNS[cat]]:
                totals[COLUMNS[cat]][k] += v
            elif COLUMNS[cat] in totals and k not in totals[COLUMNS[cat]]:
                totals[COLUMNS[cat]][k] = v


            else:
                totals[COLUMNS[cat]] = {k: v}

 #   print(dumps(totals, ensure_ascii=False, sort_keys=True, indent=2, default=str))

    with open("losses.json", "r", encoding="utf-8") as f:
        old_loss = load(f)

    diff_loss = diff_dicts(old_loss,totals)

 #   print(dumps(diff_loss, ensure_ascii=False, sort_keys=True, indent=2, default=str))

    with open("losses.json", "w", encoding="utf-8") as f:
        f.write(dumps(totals, ensure_ascii=False, sort_keys=True, indent=2, default=str))


    print("---- found ---- ", datetime.datetime.now().strftime("%d.%m.%Y, %H:%M:%S"))

    days = (datetime.datetime.now().date() - datetime.date(2022, 2, 25)).days
    display_date = datetime.datetime.now().strftime("%d.%m.%Y")

    create_svg(totals, diff_loss,  display_date)

    last_id = context.bot_data.get("last_loss_id", 1)
    text = loss_text(display_date, days, totals, diff_loss, {}, last_id)

    with open("loss.png", "rb") as f:
        msg = await context.bot.send_photo(config.CHANNEL_UA_RU, photo=f, caption=text)

    context.bot_data["last_loss"] = now
    context.bot_data["last_loss_id"] = msg.id


async def setup_crawl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("setup crawl")
    #  context.bot_data.pop("last_loss", "")
    #    context.bot_data.pop("last_loss_id", 18147)
    await get_api(context)
    context.job_queue.run_repeating(get_api, datetime.timedelta(hours=1.5))
    await update.message.reply_text("Scheduled Api Crawler.")

asyncio.run( get_api(None))
