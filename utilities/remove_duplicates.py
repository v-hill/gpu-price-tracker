"""
Script to remove duplicate entries from the json database file.
"""

# Python library imports
import json
import os

data_directory = "C:....."
filepaths = os.listdir(data_directory)

filepaths = [f for f in filepaths if '.json' in f]

file_idx = -1    # Set the index of the json database to sort
file = filepaths[file_idx]

# Load existing database
with open(data_directory + file) as f:
    existing_db = json.load(f)

collected_db = existing_db['collected']

new_db = {'collected': [],
          'uncollected': []}

for gpu in collected_db:
    items_removed = 0
    new_data = []
    for item in gpu['data']:
        in_new_data = False
        for entry in new_data:
            shared_items = {
                k: entry[k] for k in entry if k in item and entry[k] == item[k]}
            if len(shared_items) == len(entry):
                in_new_data = True
        if in_new_data:
            items_removed += 1
        else:
            new_data.append(item)

    if items_removed > 0:
        print(f'{items_removed} items removed from {gpu["name"]}')
        gpu['data'] = new_data
    new_db['collected'].append(gpu)

with open(data_directory + file, 'w') as fout:
    json.dump(new_db, fout, indent=4, sort_keys=False)
