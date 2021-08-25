"""
Module for database related classes and functions.
"""
# Python library imports
import datetime
import json
from os import path
import bs4

# Repo code imports
from graphics_card import GraphicsCard


class Database():
    """
    Class for containing and processing all of the scraped data.
    """

    def __init__(self, conf: dict):
        self.products = []
        self.save_filepath = self.get_save_filepath(conf)
        self.make_database()

    def get_save_filepath(self, conf: dict):
        database_filename = conf['paths']['database']
        current_time = datetime.datetime.now()
        date_str = current_time.strftime("%Y_%m_%d_")
        database_filename = date_str + database_filename

        datbaase_path = conf['paths']['filepath']
        save_filepath = path.join(datbaase_path, database_filename)
        return save_filepath

    def make_database(self):
        """
        Create database if no current database exists.

        Parameters
        ----------
        name : str
            Name of database (must have .json extension)
            e.g. my_database.json

        """
        if path.exists(self.save_filepath):
            return True
        else:
            with open(self.save_filepath, 'w') as fout:
                json.dump([], fout, indent=4, sort_keys=False)
        return False

    def to_dict(self):
        """
        Create a dictionary representation of the Database for saving to json.

        Returns
        -------
        dict_out : dict
            Dictionary of Database instance.
        """
        dict_out = {}
        dict_out['collected'] = [prod.to_dict()
                                 for prod in self.products if prod.data_collected]
        dict_out['uncollected'] = [prod.to_dict()
                                   for prod in self.products if prod.data_collected == False]
        return dict_out

    def write_to_db(self):
        """
        Write data to database.

        Parameters
        ----------
        conf : dict
            configuration.toml
        """
        new_data = self.to_dict()

        # Load existing database
        with open(self.save_filepath) as f:
            existing_db = json.load(f)

        if existing_db == []:
            with open(self.save_filepath, 'w') as fout:
                json.dump(new_data, fout, indent=4, sort_keys=False)
                return 1

        # print(f'current database: {len(existing_db["collected"])} collected, '
        #       f'{len(existing_db["uncollected"])} uncollected')
        new_db_c = existing_db['collected']
        existing_db_c_names = [e['name'] for e in existing_db['collected']]
        for entry in new_data['collected']:
            if entry['name'] not in existing_db_c_names:
                new_db_c.append(entry)

        new_db_uc = []
        new_data_uc_names = [e['name'] for e in new_data['uncollected']]
        for entry in existing_db['uncollected']:
            if entry['name'] in new_data_uc_names:
                new_db_uc.append(entry)

        new_db = {'collected': new_db_c,
                  'uncollected': new_db_uc}

        # print(f'new database: {len(new_db["collected"])} collected, '
        #       f'{len(new_db["uncollected"])} uncollected')
        with open(self.save_filepath, 'w') as fout:
            json.dump(new_db, fout, indent=4, sort_keys=False)

    def check_exists(self, name: str):
        """
        Test whether an entry in the json database with a given name already exists.

        Parameters
        ----------
        name : str
            'name' tag of new GPU entry
        conf : dict
            configuration.toml

        Returns
        -------
        bool
            True if name already in database, else False.
        """
        # Load existing database
        with open(self.save_filepath) as f:
            existing_db = json.load(f)

        collected_names = [e['name'] for e in existing_db['collected']]
        if name in collected_names:
            return True
        return False

    def get_products(self, soup: bs4.BeautifulSoup):
        """
        Given the Chipset/GPU Model menu, populate the self.products list with
        the set of products in the menu.

        Parameters
        ----------
        soup : bs4.BeautifulSoup
            Soup of the page with the menu open.
        """
        menu = soup.find('div', {'class': 'x-overlay__wrapper--right'})
        options = menu.find_all('label',
                                {'class': 'x-refine__multi-select-label'})
        for entry in options:
            name = entry.text
            button_id = entry.find('input')['id']
            self.products.append(GraphicsCard(name, button_id))
        print(f'{len(self.products)} GPUs found')

    def filter_products(self, accepted_substrings: list):
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
