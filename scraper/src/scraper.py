"""
Main script for running the scraper.
"""


import datetime
import logging
import logging.config
import os
import re
import shutil

from django.utils.timezone import make_aware

from scraper.models import URL, BrandMenu, EbayGraphicsCard, Log, Sale
from scraper.src.product import EBayItem
from scraper.src.webpage import BrandWebPage


def backup_database(database_path):
    """
    Backup an existing database with a timestamp.
    """
    if os.path.exists(database_path):
        old_name = database_path.stem
        new_name = f"{datetime.datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}_{old_name}{database_path.suffix}"
        new_database_path = database_path.parent / new_name
        logging.info(f"    Backing up database to: {new_database_path}")
        shutil.copy(database_path, new_database_path)


def add_new_gpus(accepted_substrings, log):
    brand_menu_qs = BrandMenu.objects.all()
    new_gpu_entries = []
    for entry in brand_menu_qs:
        name_contains_substring = any(
            x in entry.text.lower()
            for x in [f.lower() for f in accepted_substrings]
        )
        if name_contains_substring:
            gpu_entry = EbayGraphicsCard.objects.filter(
                name__exact=entry.text
            ).first()
            if gpu_entry is None:
                new_gpu_entry = EbayGraphicsCard(
                    log=log,
                    name=entry.text,
                    collect_data=True,
                    data_collected=True,
                    last_collection=make_aware(
                        datetime.datetime(2000, 1, 1, 1, 1)
                    ),
                )
                new_gpu_entries.append(new_gpu_entry)
    EbayGraphicsCard.objects.bulk_create(new_gpu_entries)


def reset_data_collected_flag(reset_hours, log):
    current_datetime = make_aware(datetime.datetime.now())
    for gpu_entry in EbayGraphicsCard.objects.all():
        if gpu_entry.collect_data:
            diff = current_datetime - gpu_entry.last_collection
            if diff.seconds >= (60 * 60 * reset_hours):
                gpu_entry.data_collected = False
                gpu_entry.log = log
                gpu_entry.save()


def data_left_to_collect():
    # find any gpu in the current log which does not have data_collected
    gpu = EbayGraphicsCard.objects.filter(
        data_collected=False, collect_data=True
    ).first()
    if gpu is None:
        logging.info("No GPUs in current log without data collected")
        return False
    return True


def navigate_to_gpu_page(webpage, gpu_button_id):
    logging.info("    Navigating to page of GPU")
    webpage.return_to_start_url()
    webpage.open_model_menu()
    webpage.open_all_filter_menu()
    webpage.select_option(button_id=gpu_button_id)
    webpage.apply_selection()


def create_url_obj(url, log, gpu):
    url = URL.objects.get_or_create(url=url, log=log, gpu=gpu)


def make_sales_objects(
    brand_webpage,
    log,
    gpu,
):
    # create sale objects
    logging.info("    Creating sale objects")
    soup = brand_webpage.page_source_soup()
    items_container = soup.find(
        "ul", {"class": re.compile("srp-results srp-grid")}
    )
    item_tags = items_container.find_all(
        "div", {"class": "s-item__wrapper clearfix"}
    )
    if len(item_tags) == 0:
        raise Exception("No items found on page")

    try:
        num_already_in_db, num_added_to_db = bulk_insertion(
            log, gpu, item_tags
        )
    except:
        num_already_in_db, num_added_to_db = individual_insertion(
            log, gpu, item_tags
        )

    logging.info(f"        {num_added_to_db} new sale objects added")
    logging.info(f"        {num_already_in_db} sale objects already in db")
    return num_added_to_db, num_already_in_db


def bulk_insertion(log, gpu, item_tags):
    num_already_in_db = 0
    num_added_to_db = 0
    new_sale_items = []
    for tag in item_tags:
        new_item = EBayItem(tag)
        new_item.clean_item()
        item_kwargs = new_item.get_kwargs()
        item_kwargs["date"] = make_aware(item_kwargs["date"])

        new_sale = Sale.objects.filter(**item_kwargs).first()

        if new_sale is None:
            new_sale = Sale(**item_kwargs)
            new_sale.log = log
            new_sale.gpu = gpu
            new_sale_items.append(new_sale)
            num_added_to_db += 1
        else:
            num_already_in_db += 1
    Sale.objects.bulk_create(new_sale_items)
    return num_already_in_db, num_added_to_db


def individual_insertion(log, gpu, item_tags):
    logging.info("        performing individual insertion")
    num_already_in_db = 0
    num_added_to_db = 0
    for tag in item_tags:
        new_item = EBayItem(tag)
        new_item.clean_item()
        item_kwargs = new_item.get_kwargs()
        item_kwargs["date"] = make_aware(item_kwargs["date"])

        new_sale = Sale.objects.filter(**item_kwargs).first()
        if new_sale is None:
            new_sale = Sale(**item_kwargs)
            new_sale.log = log
            new_sale.gpu = gpu
            new_sale.save()
            num_added_to_db += 1
        else:
            num_already_in_db += 1
    return num_already_in_db, num_added_to_db


def collect_data(log, gpu, brand_webpage):
    brand_webpage.get_pages()  # Find page number buttons
    next_page_exists = True  # assume next page exists

    num_added_to_db, num_already_in_db = make_sales_objects(
        brand_webpage,
        log,
        gpu,
    )

    while next_page_exists and num_already_in_db <= 45:
        # Naviagte to the next page and collect item data
        next_page_exists = brand_webpage.nav_to_next_page()
        if next_page_exists:
            new_num_added_to_db, new_num_already_in_db = make_sales_objects(
                brand_webpage,
                log,
                gpu,
            )
            num_added_to_db += new_num_added_to_db
            num_already_in_db += new_num_already_in_db
            logging.debug(f"    {num_already_in_db} sales already in db")

    sales_scraped = log.sales_scraped if log.sales_scraped is not None else 0
    sales_scraped += num_added_to_db + num_already_in_db
    log.sales_scraped = sales_scraped

    current_datetime = make_aware(datetime.datetime.now())
    log.sales_added = Sale.objects.filter(log=log).count()
    log.end_time = current_datetime
    log.save()

    gpu.data_collected = True
    gpu.last_collection = current_datetime
    gpu.save()
    logging.info("    Completed data collection")


def process_gpu(log, webpage, main_webdriver, start_url):
    if not data_left_to_collect():
        return True

    gpu = EbayGraphicsCard.objects.filter(
        data_collected=False, collect_data=True
    ).first()
    logging.info(f"Collecting data for {gpu.name}")

    gpu_button_id = BrandMenu.short_id_from_name(gpu.name)

    navigate_to_gpu_page(webpage, gpu_button_id)
    create_url_obj(webpage.driver.current_url, log, gpu)

    # Now the we're on the page for a particular gpu, create a BrandWebPage instance
    brand_webpage = BrandWebPage(main_webdriver, start_url)
    brand_webpage.check_number_of_results()

    collect_data(log, gpu, brand_webpage)


def calculate_total_collected_per_gpu():
    logging.info("Calculating total_collected value for each gpu")
    qs = EbayGraphicsCard.objects.all()
    for card in qs:
        count = Sale.objects.filter(gpu__id=card.id).count()
        card.total_collected = count
        card.save()


def calculate_sales_added_per_log():
    logging.info("Calculating sales_added value for each log")
    qs = Log.objects.all()
    for log in qs:
        count = Sale.objects.filter(log__id=log.id).count()
        log.sales_added = count
        log.save()
        print(log.id, count)
