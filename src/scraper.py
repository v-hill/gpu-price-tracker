"""
Main scraper executable.
"""
# Standard library imports
import logging

# Python library imports
import selenium.webdriver.chrome.options as chrome
import selenium.webdriver.firefox.options as firefox
import toml
from selenium import webdriver

# Repo code imports
from database import Database
from utils import check_always_accepted, too_old
from webpage import BrandWebPage, MainWebPage, get_driver_options

# ----------------------------------- Main ------------------------------------

# Load configuration toml
with open("src/configuration.toml", "r") as f:
    conf = toml.load(f, _dict=dict)

# Setup logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename="scraper.log",
    encoding="utf-8",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.DEBUG,
)

# Create database if one doesn't exist
db = Database(conf)

browser_options = get_driver_options()  # Setup driver options
if conf["browser"]["chrome"] == "True":
    main_driver = webdriver.Chrome(
        conf["paths"]["chromedriver"], options=browser_options
    )
if conf["browser"]["firefox"] == "True":
    main_driver = webdriver.Firefox(
        executable_path=conf["paths"]["geckodriver"], options=browser_options
    )

webpage = MainWebPage(main_driver, conf)  # Create main webpage class
webpage.auto_accept_cookies()

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models
db.get_products(webpage.page_source_soup())
db.filter_products(conf["filters"]["accepted_substrings"])
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
        brand_webpage = BrandWebPage(main_driver, conf)
        num_results, sucess = brand_webpage.get_number_of_results()
        gpu_model.num_sold = num_results

        data = []
        if sucess or check_always_accepted(gpu_model.name, conf):
            brand_webpage.get_pages()
            next_page_exists = True
            data.extend(brand_webpage.collect_page_data())
            while next_page_exists and not too_old(conf, data):
                # Naviagte to the next page and collect item data
                next_page_exists = brand_webpage.nav_to_next_page()
                data.extend(brand_webpage.collect_page_data())
        gpu_model.add_data(data)
    db.write_to_db()  # Write new data to database
