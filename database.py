"""
Module for database related classes and functions.
"""

# Python library imports
from os import path
import json

# Repo code imports
from graphics_card import GraphicsCard


def make_database(name):
    """
    Create database if no current database exists.

    Parameters
    ----------
    name : str
        Name of database (must have .json extension)
        e.g. my_database.json

    """
    if path.exists(name):
        return True
    else:
        with open(name, 'w') as fout:
            json.dump([], fout, indent=4, sort_keys=False)
    return False


class Database():
    """
    Class for containing and processing all of the scraped data.
    """

    def __init__(self):
        self.products = []

    def to_dict(self):
        dict_out = {}
        dict_out['collected'] = [prod.to_dict()
                                 for prod in self.products if prod.data_collected]
        dict_out['uncollected'] = [prod.to_dict()
                                   for prod in self.products if prod.data_collected == False]
        return dict_out

    def write_to_db(self, conf):
        """
        Write data to database.

        Parameters
        ----------
        conf : dict
            configuration.toml
        """
        new_data = self.to_dict()

        # Load existing database
        with open(conf['paths']['database']) as f:
            existing_db = json.load(f)

        if existing_db == []:
            with open(conf['paths']['database'], 'w') as fout:
                json.dump(new_data, fout, indent=4, sort_keys=False)
                return 1

        new_data_c = new_data['collected']
        new_data_uc = new_data['uncollected']
        existing_db_c = existing_db['collected']
        existing_db_uc = existing_db['uncollected']

        new_db_c = existing_db_c + new_data_c
        new_db_uc = []

        new_data_uc_names = [e['name'] for e in new_data_uc]
        for entry in existing_db_uc:
            if entry['name'] in new_data_uc_names:
                new_db_uc.append(entry)

        new_db = {'collected': new_db_c,
                  'uncollected': new_db_uc}

        with open(conf['paths']['database'], 'w') as fout:
            json.dump(new_db, fout, indent=4, sort_keys=False)

    def check_exists(self, name, conf):
        # Load existing database
        with open(conf['paths']['database']) as f:
            existing_db = json.load(f)

        collected_names = [e['name'] for e in existing_db['collected']]
        if name in collected_names:
            return True
        return False

    def get_products(self, soup):
        menu = soup.find('div', {'class': 'x-overlay__wrapper--right'})
        options = menu.find_all('label',
                                {'class': 'x-refine__multi-select-label'})
        for entry in options:
            name = entry.text
            button_id = entry.find('input')['id']
            self.products.append(GraphicsCard(name, button_id))
        print(f'{len(self.products)} GPUs found')

    def filter_products(self, accepted_substrings):
        """
        Filter out unwanted GPUs by selecting only products whose name contains
        one of the substrings listed in the 'accepted_substrings' attribute of
        the configuration.toml file.

        Parameters
        ----------
        accepted_substrings : list
            List of accepted substrings to filter.
        """
        if not isinstance(accepted_substrings, list):
            raise Exception("'accepted_substrings' must be of type list")
        filters = accepted_substrings
        new_products = []
        for p in self.products:
            if any(x in p.name.lower() for x in [f.lower() for f in filters]):
                new_products.append(p)
        self.products = new_products
        print(f'{len(self.products)} GPUs to scrape')
