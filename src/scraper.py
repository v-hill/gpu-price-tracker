"""
Main scraper executable.
"""
import logging
import logging.config
import re
import sys

from selenium import webdriver

from configuration import (
    BROWSER,
    DATE_LIMIT,
    FILTERS,
    NUM_RESULTS,
    PATHS,
    START_URL,
)
from database import Scraper
from utils import check_always_accepted, check_num_results_bounds, too_old
from webpage import BrandWebPage, MainWebPage, get_driver_options

# ----------------------------------- Main ------------------------------------

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

# Create database if one doesn't exist
db = Scraper(PATHS)

browser_options = get_driver_options()  # Setup driver options
if BROWSER == "chrome":
    main_driver = webdriver.Chrome(
        PATHS["chromedriver"], options=browser_options
    )
if BROWSER == "firefox":
    main_driver = webdriver.Firefox(
        executable_path=PATHS["geckodriver"], options=browser_options
    )

webpage = MainWebPage(
    main_driver,
    START_URL,
)  # Create main webpage class
webpage.auto_accept_cookies()

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models
db.get_brand_menu_items(webpage.page_source_soup())
db.get_filtered_products(FILTERS["accepted_substrings"])
db.write_to_db()  # Write new data to database

# Main loop over all products
iterator = iter(db.products)
done_looping = False
while not done_looping:
    try:
        gpu_model = next(iterator)
    except StopIteration:
        done_looping = True
    else:
        if db.check_exists(gpu_model.name):
            logging.info(f"Data already in database for: {gpu_model.name}")
            continue
        webpage.return_to_start_url()

        # Navigate to GPU page
        webpage.open_model_menu()
        webpage.open_all_filter_menu()
        webpage.select_option(gpu_model)
        webpage.apply_selection()
        logging.info(f"Collecting data for: {gpu_model.name}")

        # Get number of results
        brand_webpage = BrandWebPage(main_driver, START_URL, NUM_RESULTS)
        num_results, sucess = brand_webpage.get_number_of_results()
        gpu_model.num_sold = num_results

        if check_num_results_bounds(
            num_results, NUM_RESULTS
        ) or check_always_accepted(gpu_model.name, FILTERS):
            brand_webpage.get_pages()
            next_page_exists = True

            soup = brand_webpage.page_source_soup()
            items_container = soup.find(
                "ul", {"class": re.compile("srp-results srp-grid")}
            )
            item_tags = items_container.find_all(
                "div", {"class": "s-item__wrapper clearfix"}
            )
            if len(item_tags) == 0:
                raise Exception("No items found on page")

            while next_page_exists and not too_old(DATE_LIMIT, data):
                # Naviagte to the next page and collect item data
                next_page_exists = brand_webpage.nav_to_next_page()
                data.extend(brand_webpage.collect_page_data())
        gpu_model.add_data(data)
    db.write_to_db()  # Write new data to database
