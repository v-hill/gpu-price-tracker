"""
Main script for running the scraper.
"""
import logging
import logging.config
import sys
import time

from sqlalchemy.orm import sessionmaker

from configuration import PATHS, START_URL
from scraper.models import Log
from scraper.scraper import (
    create_database,
    delete_database,
    get_accepted_substrings,
    get_engine,
    get_main_webdriver,
    populate_gpu_table_from_menu,
    process_gpu,
)
from scraper.webpage import MainWebPage

# ------------------------------- Logging setup -------------------------------

# Setup logging
logging.basicConfig(
    filename="scraper.log",
    filemode="a",
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y/%m/%d %H:%M",
    level=logging.INFO,
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.info(" --- Started main.py --- ")

# ------------------------------ Database setup -------------------------------

logging.info("Setting up database")

database_path = PATHS["database"]
engine = get_engine(database_path, quite=True)
Session = sessionmaker(bind=engine)

# delete_database(database_path)
create_database(engine, database_path)

# ------------------------------- Webpage setup -------------------------------

logging.info("Setting up main webpage")

main_webdriver = get_main_webdriver()
webpage = MainWebPage(main_webdriver, START_URL)
webpage.auto_accept_cookies()

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models available in the menu
menu_items = webpage.get_brand_menu_items()

# --------------------- Collect info on available products --------------------

# Make a new Log entry for the current run and get the log_id
new_log_id = Log.get_new_log(Session)

accepted_substrings = get_accepted_substrings()
populate_gpu_table_from_menu(
    Session,
    new_log_id,
    menu_items,
    accepted_substrings,
)

completed = False
failures = 0
while not completed and failures <= 5:
    try:
        completed = process_gpu(Session, new_log_id, webpage, main_webdriver)
    except Exception as e:
        logging.exception("Error while collecting gpu data:\n%s" % e)
        failures += 1
        time.sleep(30)
