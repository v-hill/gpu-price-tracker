"""
Main scraper executable.
"""
import datetime
import logging
import logging.config
import re
import sys

import sqlalchemy
from selenium import webdriver
from sqlalchemy.orm import sessionmaker

from configuration import (
    BROWSER,
    FILTERS,
    NUM_RESULTS,
    PATHS,
    START_URL,
)
from database import Scraper
from models import GPU, Log, Sale
from product import EBayItem
from utils import (
    check_always_accepted,
    check_num_results_bounds,
    get_or_create,
    remove_unicode,
)
from webpage import BrandWebPage, MainWebPage, get_driver_options

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
logging.info("----  Started scraper.py script  ----")

# --------------------------------- Log setup ---------------------------------

engine = sqlalchemy.create_engine(
    f"sqlite:///{PATHS['database']}",
    echo=True,
    future=True,
)
engine = sqlalchemy.create_engine(f"sqlite:///{PATHS['database']}")

# instantiate an instance of the Database class
scraper = Scraper(engine=engine, database_path=PATHS["database"])

# Make a new Log entry for the current run and get the log_id
Session = sessionmaker(bind=engine)
new_log_id = Log.get_new_log(Session)

# ------------------------------- Browser setup -------------------------------

browser_options = get_driver_options()  # Setup driver options
if BROWSER == "chrome":
    main_driver = webdriver.Chrome(
        PATHS["chromedriver"], options=browser_options
    )
if BROWSER == "firefox":
    main_driver = webdriver.Firefox(
        executable_path=PATHS["geckodriver"], options=browser_options
    )

# ---------------------------- Main Webpage setup -----------------------------

webpage = MainWebPage(
    main_driver,
    START_URL,
)  # Create main webpage class
webpage.auto_accept_cookies()

# --------------------- Collect info on available products --------------------

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models available in the menu
menu_items = webpage.get_brand_menu_items()

accepted_substrings = FILTERS["accepted_substrings"]
if not isinstance(accepted_substrings, list):
    raise Exception("'accepted_substrings' must be of type list")

# Add menu items to GPU table
with Session() as session:
    new_log = session.query(Log).filter(Log.log_id == new_log_id).first()
    for entry in menu_items:
        name = entry.text
        name = remove_unicode(name)
        if any(
            x in name.lower() for x in [f.lower() for f in accepted_substrings]
        ):
            new_gpu, _ = get_or_create(session, GPU, name=name)
            new_gpu.log_id = new_log_id
            new_gpu.data_collected = False
            new_gpu.button_id = entry.find("input")["id"]
            session.add(new_gpu)
    new_log.end_time = start_time = datetime.datetime.now()
    session.commit()
    gpus_added = session.query(GPU).filter(GPU.log_id == new_log_id).count()
    logging.info(f"{gpus_added} GPUs found")

# --------------------------------- Main loop ---------------------------------


def make_sales_objects(brand_webpage, session, new_log_id, uncollected_gpu):
    # create sale objects
    sales_objects = []
    soup = brand_webpage.page_source_soup()
    items_container = soup.find(
        "ul", {"class": re.compile("srp-results srp-grid")}
    )
    item_tags = items_container.find_all(
        "div", {"class": "s-item__wrapper clearfix"}
    )
    if len(item_tags) == 0:
        raise Exception("No items found on page")

    num_already_in_db = 0
    for tag in item_tags:
        new_item = EBayItem(tag)
        new_item.clean_item()
        item_kwargs = new_item.get_kwargs()
        new_sale, exists = get_or_create(session, Sale, **item_kwargs)
        new_sale.log_id = new_log_id
        new_sale.gpu_id = uncollected_gpu.gpu_id
        sales_objects.append(new_sale)
        if exists:
            num_already_in_db += 1
    return sales_objects, num_already_in_db


with Session() as session:
    new_log = session.query(Log).filter(Log.log_id == new_log_id).first()
    uncollected_gpu = (
        session.query(GPU)
        .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
        .first()
    )
    if uncollected_gpu is not None:
        print("can continue")

    logging.info(f"GPU: {uncollected_gpu.name}")

    # Navigate to GPU page
    webpage.return_to_start_url()
    webpage.open_model_menu()
    webpage.open_all_filter_menu()
    webpage.select_option(button_id=uncollected_gpu.short_id())
    webpage.apply_selection()

    # Get number of results
    brand_webpage = BrandWebPage(main_driver, START_URL, NUM_RESULTS)
    num_results = brand_webpage.get_number_of_results()

    # Check if data should be collected for this GPU
    collect_data = check_num_results_bounds(
        num_results, NUM_RESULTS
    ) or check_always_accepted(uncollected_gpu.name, FILTERS)

    if collect_data:
        logging.info(f"    collecting data")
        brand_webpage.get_pages()
        next_page_exists = True

        sales_objects, num_already_in_db = make_sales_objects(
            brand_webpage,
            session,
            new_log_id,
            uncollected_gpu,
        )

        while next_page_exists and num_already_in_db <= 5:
            # Naviagte to the next page and collect item data
            next_page_exists = brand_webpage.nav_to_next_page()
            if next_page_exists:
                new_sales_objects, existing_items = make_sales_objects(
                    brand_webpage,
                    session,
                    new_log_id,
                    uncollected_gpu,
                )
                sales_objects += new_sales_objects
                num_already_in_db += existing_items
                print(num_already_in_db)

        session.bulk_save_objects(sales_objects)
        logging.info(f"    {len(sales_objects)} sales added to db")
        new_log.end_time = start_time = datetime.datetime.now()
        uncollected_gpu.data_collected = True
        session.commit()


"""
If more than 6 hours since last run, set data_collected to false for all GPU

Add num scraped, num found to gpu tables

"""