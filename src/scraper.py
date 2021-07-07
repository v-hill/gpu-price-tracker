"""
Main scraper executable.
"""

# Python library imports
import toml
import selenium.webdriver.firefox.options as firefox
import selenium.webdriver.chrome.options as chrome
from selenium import webdriver

# Repo code imports
from database import Database, make_database
from webpage import MainWebPage, BrandWebPage
from utils import too_old, check_always_accepted

# --------------------------- Function definitions ----------------------------


def collect_page_data(b_webpage, verbose=False):
    """
    Collect the data for every item on the webpage.

    Parameters
    ----------
    b_webpage : BrandWebPage
        Webpage class.
    verbose : bool, optional
        Prints data on every item. The default is False.

    Returns
    -------
    items : list
        List of EBayItem objects.
    """
    item_tags = b_webpage.make_items()
    if len(item_tags) == 0:
        raise Exception("No items found on page")
    items = []
    for item in item_tags:
        item.get_details()
        item.get_attribute_dict()
        item.get_title()
        item.parse_date()
        item.sort_price_details()
        item.get_total_cost()
        items.append(item)
        if verbose:
            for key, val in item.item_attributes.items():
                print(f'{key:<12}: {val}')
            print('-' * 60)
    return items

# ----------------------------------- Main ------------------------------------


# Load configuration toml
with open('configuration.toml', 'r') as f:
    conf = toml.load(f, _dict=dict)

# Create database if one doesn't exist
db_exists = make_database(conf['paths']['database'])

# Setup driver options
if conf['browser']['chrome'] == 'True':
    browser_options = chrome.Options()
if conf['browser']['firefox'] == 'True':
    browser_options = firefox.Options()

browser_options.add_argument('--disable-blink-features=AutomationControlled')
if bool(conf['driver_options']['disable_gpu']):
    browser_options.add_argument('--disable-gpu')  # Disable GPU

# Start webdriver
print(conf['paths']['geckodriver'])
if conf['browser']['chrome'] == 'True':
    main_driver = webdriver.Chrome(
        conf['paths']['chromedriver'],
        options=browser_options)
if conf['browser']['firefox'] == 'True':
    main_driver = webdriver.Firefox(
        executable_path=conf['paths']['geckodriver'],
        options=browser_options)


webpage = MainWebPage(main_driver, conf)  # Create main webpage class
webpage.auto_accept_cookies()

# Open main filter menu
webpage.open_model_menu()
webpage.open_all_filter_menu()

# Get GPU models
db = Database()
db.get_products(webpage.page_source_soup())
db.filter_products(conf['filters']['accepted_substrings'])
db.write_to_db(conf)  # Write new data to database

# Main loop over all products
iterator = iter(db.products)
done_looping = False
while not done_looping:
    try:
        gpu_model = next(iterator)
    except StopIteration:
        done_looping = True
    else:
        if db.check_exists(gpu_model.name, conf):
            print(f'Data already in database for: {gpu_model.name}')
            continue
        webpage.return_to_start_url()

        # Navigate to GPU page
        webpage.open_model_menu()
        webpage.open_all_filter_menu()
        webpage.select_option(gpu_model)
        webpage.apply_selection()
        print(f'Collecting data for: {gpu_model.name}')

        # Get number of results
        brand_webpage = BrandWebPage(main_driver, conf)
        num_results, sucess = brand_webpage.get_number_of_results()
        gpu_model.num_sold = num_results

        data = []
        if sucess or check_always_accepted(gpu_model.name, conf):
            brand_webpage.get_pages()
            next_page_exists = True
            data.extend(collect_page_data(brand_webpage))
            while next_page_exists and not too_old(conf, data):
                # Naviagte to the next page and collect item data
                next_page_exists = brand_webpage.nav_to_next_page()
                data.extend(collect_page_data(brand_webpage))
        gpu_model.add_data(data)
    db.write_to_db(conf)  # Write new data to database
