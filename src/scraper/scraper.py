"""
Main scraper executable.
"""
import datetime
import logging
import logging.config
import os
import re
import sys
import time
from os import path

import selenium.webdriver.chrome.options as chrome
import selenium.webdriver.firefox.options as firefox
import sqlalchemy
from selenium import webdriver
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
from scraper.utils import (
    check_always_accepted,
    check_num_results_bounds,
    get_or_create,
    remove_unicode,
)
from scraper.webpage import BrandWebPage, MainWebPage, get_driver_options


def get_driver_options():
    logging.info(f"{BROWSER} browser selected")
    if BROWSER == "chrome":
        browser_options = chrome.Options()
    if BROWSER == "firefox":
        browser_options = firefox.Options()
    else:
        raise Exception(f"Browser {BROWSER} is not 'chrome' or 'firefox'")
    browser_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    if bool(DRIVER_OPTIONS["disable_gpu"]):
        browser_options.add_argument("--disable-gpu")  # Disable GPU
    return browser_options


def get_main_webdriver():
    browser_options = get_driver_options()  # Setup driver options
    if BROWSER == "chrome":
        main_driver = webdriver.Chrome(
            PATHS["chromedriver"], options=browser_options
        )
    if BROWSER == "firefox":
        main_driver = webdriver.Firefox(
            executable_path=PATHS["geckodriver"], options=browser_options
        )
    return main_driver


def get_engine(database_path, quite=True):
    if quite:
        engine = sqlalchemy.create_engine(f"sqlite:///{database_path}")
    else:
        engine = sqlalchemy.create_engine(
            f"sqlite:///{database_path}",
            echo=True,
            future=True,
        )
    return engine


def create_database(engine, database_path):
    """
    Create sqlite database if no current database exists.
    """
    if path.exists(database_path):
        logging.info(f"Database already exists at: {database_path}")
    else:
        logging.info(f"Creating database at: {database_path}")
        Base.metadata.create_all(engine)


def delete_database(database_path):
    """
    Delete an existing sqlite database if the database exists.
    """
    if os.path.exists(database_path):
        os.remove(database_path)


def get_accepted_substrings():
    accepted_substrings = FILTERS["accepted_substrings"]
    if not isinstance(accepted_substrings, list):
        raise Exception("'accepted_substrings' must be of type list")
    return accepted_substrings


def populate_gpu_table_from_menu(
    session, new_log_id, menu_items, accepted_substrings
):
    # Add menu items to GPU table
    new_log = session.query(Log).filter(Log.log_id == new_log_id).first()
    for entry in menu_items:
        name = entry.text
        name = remove_unicode(name)
        if any(
            x in name.lower() for x in [f.lower() for f in accepted_substrings]
        ):
            new_gpu, _ = get_or_create(session, GPU, name=name)
            new_gpu.log_id = new_log_id
            new_gpu.button_id = entry.find("input")["id"]

            new_gpu.data_collected = True
            if new_gpu.last_collection is not None:
                diff = datetime.datetime.now() - new_gpu.last_collection
                diff_hours = diff.seconds / 3600
                if diff_hours >= DATA_READ_RESET_HOURS:
                    new_gpu.data_collected = False
            else:
                new_gpu.data_collected = False

            session.add(new_gpu)
    new_log.end_time = datetime.datetime.now()
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
        if not exists:
            new_sale.log_id = new_log_id
            new_sale.gpu_id = uncollected_gpu.gpu_id
        sales_objects.append(new_sale)
        if exists:
            num_already_in_db += 1
    return sales_objects, num_already_in_db


def collect_gpu_data(Session, new_log_id, webpage, main_driver):
    with Session() as session:
        new_log = session.query(Log).filter(Log.log_id == new_log_id).first()
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        if gpu is None:
            return True

        logging.info(gpu.name)

        # Navigate to GPU page
        webpage.return_to_start_url()
        webpage.open_model_menu()
        webpage.open_all_filter_menu()
        webpage.select_option(button_id=gpu.short_id())
        webpage.apply_selection()
        gpu.url = webpage.driver.current_url

        # Get number of results
        brand_webpage = BrandWebPage(main_driver, START_URL, NUM_RESULTS)
        num_results = brand_webpage.get_number_of_results()

        # Check if data should be collected for this GPU
        collect_data = check_num_results_bounds(
            num_results, NUM_RESULTS
        ) or check_always_accepted(gpu.name, FILTERS)

        if collect_data:
            brand_webpage.get_pages()
            next_page_exists = True

            sales_objects, num_already_in_db = make_sales_objects(
                brand_webpage,
                session,
                new_log_id,
                gpu,
            )

            while next_page_exists and num_already_in_db <= 5:
                # Naviagte to the next page and collect item data
                next_page_exists = brand_webpage.nav_to_next_page()
                if next_page_exists:
                    new_sales_objects, existing_items = make_sales_objects(
                        brand_webpage,
                        session,
                        new_log_id,
                        gpu,
                    )
                    sales_objects += new_sales_objects
                    num_already_in_db += existing_items
                    logging.debug(
                        f"    {num_already_in_db} sales already in db"
                    )

            session.bulk_save_objects(sales_objects)
            session.commit()

            sales_added = (
                session.query(Sale).filter(Sale.log_id == new_log_id).count()
            )
            logging.info(f"    {sales_added} sales added to db")

            sales_scraped = (
                new_log.sales_scraped
                if new_log.sales_scraped is not None
                else 0
            )
            sales_scraped += len(sales_objects)
            new_log.sales_scraped = sales_scraped

            new_log.sales_added = sales_added
            new_log.end_time = datetime.datetime.now()

        gpu.data_collected = True
        gpu.last_collection = datetime.datetime.now()
        session.commit()
        logging.info("    completed data collection")
    return False


# completed = False
# failures = 0
# while not completed and failures <= 5:
#     try:
#         completed = collect_gpu_data(Session, new_log_id, webpage, main_driver)
#     except Exception as e:
#         logging.exception("Error while collecting gpu data:\n%s" % e)
#         failures += 1
#         time.sleep(30)
