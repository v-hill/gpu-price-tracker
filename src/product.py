"""
Module for EBayItem class.
"""

# Python library imports
import copy
import re

import bs4
import pandas as pd

from utils import remove_unicode


class EBayItem:
    def __init__(self, soup_tag: bs4.element.Tag):
        self.soup_tag = soup_tag
        self.item_details = None
        self.item_attributes = {}

    def __repr__(self):
        repr_string = ''
        for key, val in self.item_attributes.items():
            repr_string += f'{key:<12}: {val} \n'
        return repr_string

    def to_dict(self):
        """
        Create a dictionary representation of the EBayItem for saving to json.

        Returns
        -------
        attrs_dict : dict
            Dictionary of EBayItem instance.
        """
        attrs_dict = copy.deepcopy(self.item_attributes)
        date_str = attrs_dict['date'].strftime("%Y-%m-%d %H:%M:%S")
        attrs_dict['date'] = date_str
        return attrs_dict

    def get_details(self):
        """
        Populate the self.item_details with a dictionay of atrributes.
        """
        detail_class_str = "^s-item__detail s-item__detail"
        self.item_details = self.soup_tag.find_all(
            "div", {"class": re.compile(detail_class_str)})
        self.item_details.extend(self.soup_tag.find_all(
            "span", {"class": re.compile(detail_class_str)}))

    def get_attribute_dict(self):
        """
        Populate the self.item_attributes dictionary with the following
        attributes:
          - price
          - postage
          - bids
        """
        self.item_attributes['bids'] = 0
        for detail in self.item_details:
            detail_span = detail.find_all("span")
            for span in detail_span:
                key = str(span['class'][-1])
                if key == 's-item__price':
                    self.item_attributes['price'] = str(span.text)
                if key == 's-item__logisticsCost':
                    self.item_attributes['postage'] = str(span.text)
                if key == 's-item__deliveryOptions':
                    self.item_attributes['postage'] = str(span.text)
                if key == 's-item__bidCount':
                    bids = int(re.findall(r'\d+', str(span.text))[0])
                    self.item_attributes['bids'] = bids
        if not 'postage' in self.item_attributes:
            self.item_attributes['postage'] = 0

    def get_title(self):
        """
        Populate the self.item_attributes dictionary with the following
        attributes:
          - title
        """
        title_class_str = "s-item__title s-item__title--has-tags"
        try:
            title = self.soup_tag.find("h3",
                                       {"class": re.compile(title_class_str)})
            title = str(title.text)
            title = remove_unicode(title)
            self.item_attributes['title'] = title
        except BaseException:
            print("no title found")
            self.item_attributes['title'] = None

    def parse_date(self):
        """
        Populate the self.item_attributes dictionary with the following
        attributes:
          - date
        """
        date_time = self.soup_tag.find(
            "div", {"class": re.compile('s-item__title-tag')})
        date_time = date_time.text.replace('Sold  ', '')
        date = pd.to_datetime(date_time)
        date += pd.to_timedelta(12, unit='h')
        date_datetime = date.to_pydatetime()
        self.item_attributes['date'] = date_datetime

    def sort_price_details(self):
        """
        Converts price and postage info into floating point values.
        """
        attr_dict = copy.deepcopy(self.item_attributes)
        for key in attr_dict:
            test_val = str(attr_dict[key]).replace(',', '')
            if any(map(test_val.lower().__contains__, ["free", "collect"])):
                price_num = float(0)
                self.item_attributes[key] = price_num

            elif "£" in test_val:
                test_val = remove_unicode(test_val)
                price_list = re.findall(r'\d*\.?\d+', test_val)
                if len(price_list) != 1:
                    raise Exception("price list contains more than one "
                                    "element")
                price_num = float(price_list[0])
                self.item_attributes[key] = price_num

    def get_total_cost(self):
        try:
            total = (self.item_attributes['price'] +
                     self.item_attributes['postage'])
        except BaseException:
            print('ah ha')
        total = round(total, 2)
        self.item_attributes['total price'] = total
