"""
Main scraper executable.
"""
import logging
import logging.config

from selenium import webdriver

from database import Database
from configuration import (
    BROWSER,
    DATE_LIMIT,
    FILTERS,
    NUM_RESULTS,
    PATHS,
    START_URL,
)
from utils import check_always_accepted, too_old
from webpage import BrandWebPage, MainWebPage, get_driver_options

# ----------------------------------- Main ------------------------------------

# Setup logging
logging.basicConfig(
    filename="scraper.log",
    encoding="utf-8",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.DEBUG,
)

# Create database if one doesn't exist
db = Database(PATHS)

browser_options = get_driver_options()  # Setup driver options
if BROWSER == "chrome":
    main_driver = webdriver.Chrome(PATHS["chromedriver"], options=browser_options)
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
db.get_products(webpage.page_source_soup())
db.filter_products(FILTERS["accepted_substrings"])
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
            print(f"Data already in database for: {gpu_model.name}")
            continue
        webpage.return_to_start_url()

        # Navigate to GPU page
        webpage.open_model_menu()
        webpage.open_all_filter_menu()
        webpage.select_option(gpu_model)
        webpage.apply_selection()
        print(f"Collecting data for: {gpu_model.name}")

        # Get number of results
        brand_webpage = BrandWebPage(main_driver, START_URL, NUM_RESULTS)
        num_results, sucess = brand_webpage.get_number_of_results()
        gpu_model.num_sold = num_results

        data = []
        if sucess or check_always_accepted(gpu_model.name, FILTERS):
            brand_webpage.get_pages()
            next_page_exists = True
            data.extend(brand_webpage.collect_page_data())
            while next_page_exists and not too_old(DATE_LIMIT, data):
                # Naviagte to the next page and collect item data
                next_page_exists = brand_webpage.nav_to_next_page()
                data.extend(brand_webpage.collect_page_data())
        gpu_model.add_data(data)
    db.write_to_db()  # Write new data to database
