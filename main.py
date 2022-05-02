"""Main script for running the scraper."""


def django_setup():
    import os
    from pathlib import Path

    base_directory = Path(__file__).resolve().parent
    os.chdir(base_directory)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")

    import django

    django.setup()


django_setup()

import logging
import logging.config
import time

from django.conf import settings

import scraper.src.logging
from scraper.models import Log
from scraper.src.brand_menu import update_brand_menu_table
from scraper.src.scraper import (
    add_new_gpus,
    backup_database,
    calculate_total_collected_per_gpu,
    process_gpu,
    reset_data_collected_flag,
)
from scraper.src.webdriver import get_main_webdriver
from scraper.src.webpage import MainWebPage

PATHS = {
    "chromedriver": (
        "U:/Work/Programming/WebDrivers/Chrome_90_chromedriver.exe"
    ),
    "geckodriver": "U:/Work/Programming/WebDrivers/geckodriver.exe",
}

START_URL = (
    "https://www.ebay.co.uk/b/Computer-Graphics-Video-Cards"
    "/27386/bn_661667?LH_ItemCondition=3000"
    "&LH_PrefLoc=1"
    "&LH_Sold=1"
    "&rt=nc"
    "&_sop=13"
    "&_udlo=10"
)

DATA_READ_RESET_HOURS = 6

# ------------------------------ Database backup ------------------------------

logging.info(" --- Started main.py --- ")
backup_database(settings.DATABASES["default"]["NAME"])

# --------------------------------- Log setup ---------------------------------

# Make a new Log entry for the current run and get the log
log = Log.get_new_log(DATA_READ_RESET_HOURS)

# ------------------------------- Webpage setup -------------------------------

main_webdriver = get_main_webdriver("firefox", PATHS)
webpage = MainWebPage(main_webdriver, START_URL)
webpage.auto_accept_cookies()

# ------------------- Collect info on available GPU models --------------------

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models available in the menu
menu_items = webpage.get_brand_menu_items()
update_brand_menu_table(menu_items, log)

# -------------------

# Add new menu items to GPU table
logging.info("Adding select menu items to EbayGraphicsCard")
accepted_substrings = ["GTX", "RTX"]

add_new_gpus(accepted_substrings, log)
reset_data_collected_flag(DATA_READ_RESET_HOURS, log)

# -------------------

completed = False
failures = 0
while not completed and failures <= 5:
    try:
        completed = process_gpu(log, webpage, main_webdriver, START_URL)
    except Exception as e:
        logging.exception("Error while collecting gpu data:\n%s" % e)
        failures += 1
        time.sleep(30)

calculate_total_collected_per_gpu()
