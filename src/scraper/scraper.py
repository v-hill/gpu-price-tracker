"""
Main scraper executable.
"""
import datetime
import logging
import logging.config
import os
import re
import shutil

import selenium.webdriver.chrome.options as chrome
import selenium.webdriver.firefox.options as firefox
import sqlalchemy
from selenium import webdriver

from configuration import (
    BROWSER,
    DATA_READ_RESET_HOURS,
    DRIVER_OPTIONS,
    FILTERS,
    NUM_RESULTS,
    PATHS,
    START_URL,
)
from scraper.models import GPU, Base, Log, Sale
from scraper.product import EBayItem
from scraper.utils import (
    check_always_accepted,
    check_num_results_bounds,
    get_or_create,
    remove_unicode,
)
from scraper.webpage import BrandWebPage


def get_driver_options():
    logging.info(f"    {BROWSER.capitalize()} browser selected")
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
        main_webdriver = webdriver.Chrome(
            PATHS["chromedriver"], options=browser_options
        )
    if BROWSER == "firefox":
        main_webdriver = webdriver.Firefox(
            executable_path=PATHS["geckodriver"], options=browser_options
        )
    return main_webdriver


def get_engine(database_filename, quite=True):
    if quite:
        engine = sqlalchemy.create_engine(f"sqlite:///{database_filename}")
    else:
        engine = sqlalchemy.create_engine(
            f"sqlite:///{database_filename}",
            echo=True,
            future=True,
        )
    return engine


def create_database(engine, database_filename):
    """
    Create sqlite database if no current database exists.
    """
    if os.path.exists(database_filename):
        logging.info(f"    Database already exists at: {database_filename}")
    else:
        logging.info(f"    Creating database at: {database_filename}")
        Base.metadata.create_all(engine)


def delete_database(database_filename):
    """
    Delete an existing sqlite database if the database exists.
    """
    logging.info(f"    Deleting database at: {database_filename}")
    if os.path.exists(database_filename):
        os.remove(database_filename)


def backup_database(database_filename):
    """
    Backup an existing database with a timestamp.
    """
    if os.path.exists(database_filename):
        new_database_filename = f"{datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}_{database_filename}"
        logging.info(f"    Backing up database to: {new_database_filename}")
        shutil.copy(database_filename, new_database_filename)


def get_accepted_substrings():
    accepted_substrings = FILTERS["accepted_substrings"]
    if not isinstance(accepted_substrings, list):
        raise Exception("'accepted_substrings' must be of type list")
    return accepted_substrings


def populate_gpu_table_from_menu(
    Session, new_log_id, menu_items, accepted_substrings
):
    # Add menu items to GPU table
    logging.info("Adding menu items to GPU table")
    with Session() as session:
        new_log = session.query(Log).filter(Log.log_id == new_log_id).first()
        for entry in menu_items:
            name = entry.text
            name = remove_unicode(name)
            if any(
                x in name.lower()
                for x in [f.lower() for f in accepted_substrings]
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
        gpus_added = (
            session.query(GPU).filter(GPU.log_id == new_log_id).count()
        )
        logging.info(f"    {gpus_added} GPUs found")


def make_sales_objects(brand_webpage, session, new_log_id, uncollected_gpu):
    # create sale objects
    logging.info("    Creating sale objects")
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
    logging.info(f"        {len(sales_objects)} new sale objects")
    logging.info(f"        {num_already_in_db} sale objects already in db")
    return sales_objects, num_already_in_db


def data_left_to_collect(Session, new_log_id):
    with Session() as session:
        # find any gpu in the current log which does not have data_collected
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        if gpu is None:
            logging.info("No GPUs in current log without data collected")
            return False
        logging.info(f"Collecting data for {gpu.name}")
        return True


def get_gpu_button_id(Session, new_log_id):
    with Session() as session:
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        return gpu.short_id()


def add_page_url_to_gpu(Session, webpage, new_log_id):
    with Session() as session:
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        gpu.url = webpage.driver.current_url
        session.commit()


def accepted_gpu(Session, num_results, new_log_id):
    # Check if data should be collected for this GPU
    with Session() as session:
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        collect_data = check_num_results_bounds(
            num_results, NUM_RESULTS
        ) or check_always_accepted(gpu.name, FILTERS)
    return collect_data


def navigate_to_gpu_page(webpage, gpu_button_id):
    logging.info("    Navigating to page of GPU")
    webpage.return_to_start_url()
    webpage.open_model_menu()
    webpage.open_all_filter_menu()
    webpage.select_option(button_id=gpu_button_id)
    webpage.apply_selection()


def collect_data(Session, new_log_id, brand_webpage):
    brand_webpage.get_pages()
    next_page_exists = True

    with Session() as session:
        log = session.query(Log).filter(Log.log_id == new_log_id).first()
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
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
                logging.debug(f"    {num_already_in_db} sales already in db")

        session.bulk_save_objects(sales_objects)
        session.commit()

        sales_added = (
            session.query(Sale).filter(Sale.log_id == new_log_id).count()
        )

        sales_scraped = (
            log.sales_scraped if log.sales_scraped is not None else 0
        )
        sales_scraped += len(sales_objects)
        log.sales_scraped = sales_scraped

        log.sales_added = sales_added
        log.end_time = datetime.datetime.now()

        gpu.data_collected = True
        gpu.last_collection = datetime.datetime.now()
        session.commit()
        logging.info("    Completed data collection")


def skip_collection(Session, new_log_id):
    with Session() as session:
        gpu = (
            session.query(GPU)
            .filter(GPU.log_id == new_log_id, GPU.data_collected == False)
            .first()
        )
        gpu.data_collected = True
        gpu.last_collection = datetime.datetime.now()
        session.commit()
        logging.info("    Skipping data collection")


def process_gpu(Session, new_log_id, webpage, main_webdriver):
    if not data_left_to_collect(Session, new_log_id):
        return True

    gpu_button_id = get_gpu_button_id(Session, new_log_id)
    navigate_to_gpu_page(webpage, gpu_button_id)
    add_page_url_to_gpu(Session, webpage, new_log_id)

    # Get number of results
    brand_webpage = BrandWebPage(main_webdriver, START_URL, NUM_RESULTS)
    num_results = brand_webpage.get_number_of_results()

    if accepted_gpu(Session, num_results, new_log_id):
        collect_data(Session, new_log_id, brand_webpage)
    else:
        skip_collection(Session, new_log_id)
    return False
