"""
Main script for running the scraper.
"""
import logging
import logging.config
import sys

from sqlalchemy.orm import sessionmaker

from configuration import (
    BROWSER,
    DATA_READ_RESET_HOURS,
    DRIVER_OPTIONS,
    FILTERS,
    NUM_RESULTS,
    PATHS,
    START_URL,
)
from scraper.database import Scraper
from scraper.models import GPU, Base, Log, Sale
from scraper.product import EBayItem
from scraper.scraper import (
    create_database,
    get_accepted_substrings,
    get_engine,
    get_main_webdriver,
    populate_gpu_table_from_menu,
)
from scraper.webpage import BrandWebPage, MainWebPage, get_driver_options

# ------------------------------- Logging setup -------------------------------

# Setup logging
logging.basicConfig(
    filename="scraper.log",
    filemode="a",
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO,
)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

# ------------------------------ Database setup -------------------------------

logging.info("Setting up database")

database_path = PATHS["database"]
engine = get_engine(database_path, quite=True)
Session = sessionmaker(bind=engine)

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

session = Session()

# Make a new Log entry for the current run and get the log_id
new_log_id = Log.get_new_log(session)

accepted_substrings = get_accepted_substrings()
populate_gpu_table_from_menu(
    session,
    new_log_id,
    menu_items,
    accepted_substrings,
)
