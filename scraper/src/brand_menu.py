"""Functions relaed to the eBay brand menu.

The brand menu is the menu the opens up when the user clicks on the
'Chipset/GPU Model' filter when searching for an item.
"""
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
                first_log=log,
                latest_log=log,
                text=text,
                button_id=entry.find("input")["id"],
            )
            new_menu_entries.append(new_menu_entry)
        else:
            if menu_entry.button_id != entry.find("input")["id"]:
                menu_entry.button_id = entry.find("input")["id"]
                logging.info(
                    f"    Button with text '{text}' updated button id"
                )
            menu_entry.latest_log = log
            menu_entry.save()

    BrandMenu.objects.bulk_create(new_menu_entries)
