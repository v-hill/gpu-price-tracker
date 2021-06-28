"""
Module for EBayItem class.
"""

# Python library imports
import re
import copy
import pandas as pd


class EBayItem:
    def __init__(self, soup_tag):
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
        self.item_attributes['bids'] = 0
        for detail in self.item_details:
            detail_span = detail.find_all("span")
            for span in detail_span:
                key = str(span['class'][-1])
                if key == 's-item__price':
                    self.item_attributes['price'] = str(span.text)
                if key == 's-item__logisticsCost':
                    self.item_attributes['postage'] = str(span.text)
                if key == 's-item__bidCount':
                    bids = int(re.findall(r'\d+', str(span.text))[0])
                    self.item_attributes['bids'] = bids

    def get_title(self):
        title_class_str = "s-item__title s-item__title--has-tags"
        try:
            title = self.soup_tag.find("h3",
                                       {"class": re.compile(title_class_str)})
            title = str(title.text)
            self.item_attributes['title'] = title
        except BaseException:
            print("no title found")
            self.item_attributes['title'] = None

    def parse_date(self):
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
            try:
                if "£" in test_val:
                    price_num = re.findall(r'\d*\.?\d+', test_val)[0]
                    price_num = float(price_num)
                    if price_num <= 5:
                        raise Exception("Price info incorrectly parsed")
                    self.item_attributes[key] = price_num
                if "Free postage" in test_val:
                    price_num = float(0)
                    self.item_attributes[key] = price_num
            except BaseException:
                pass

    def get_total_cost(self):
        try:
            total = (self.item_attributes['price'] +
                     self.item_attributes['postage'])
            total = round(total, 2)
            self.item_attributes['total price'] = total
        except BaseException:
            self.item_attributes['total price'] = None
