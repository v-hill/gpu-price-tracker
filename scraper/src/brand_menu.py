import logging
import logging.config

from scraper.models import BrandMenu
from scraper.src.utils import remove_unicode


def update_brand_menu_table(menu_items, log):
    new_menu_entries = []
    for entry in menu_items:
        text = entry.text
        text = remove_unicode(text)
        text = text.strip()
        menu_entry = BrandMenu.objects.filter(text__exact=text).first()
        if menu_entry is None:
            new_menu_entry = BrandMenu(
                log=log,
                text=text,
                button_id=entry.find("input")["id"],
            )
            new_menu_entries.append(new_menu_entry)
        else:
            if menu_entry.button_id != entry.find("input")["id"]:
                menu_entry.log = log
                menu_entry.button_id = entry.find("input")["id"]
                menu_entry.save()
                logging.info(f"    Button with text {text} updated button id")

    BrandMenu.objects.bulk_create(new_menu_entries)
