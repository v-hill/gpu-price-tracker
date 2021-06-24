"""
Module for graphics card class.
"""

# Python library imports
from datetime import datetime


class GraphicsCard():
    """
    Class for representing a graphics card. The set of graphics cards is
    found from the available options in the full filter menu.
    """

    def __init__(self, name, button_id):
        self.name = name
        self.id = button_id
        self.data_collected = False
        self.data = []
        self.collection_time = 0
        self.num_sold = 0

    def __repr__(self):
        return f'name: {self.name}'

    def short_id(self):
        return self.id.replace('c4-subPanel-Chipset%', '')

    def add_data(self, data):
        """
        Add scraper EBayItem data.

        Parameters
        ----------
        data : list
            List of EBayItem objects
        """
        print(f'    {len(data)} results added to database')
        self.data_collected = True
        self.data = data
        now = datetime.now()
        self.collection_time = now.strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """
        Create a dictionary representation of the GraphicsCard for saving to
        json.

        Returns
        -------
        dict_out : dict
            Dictionary of GraphicsCard instance.
        """
        dict_out = {'name': self.name,
                    'data_collected': self.data_collected,
                    'collection_time': self.collection_time,
                    'num_sold': self.num_sold}
        dict_out['data'] = [item.to_dict() for item in self.data]
        return dict_out
