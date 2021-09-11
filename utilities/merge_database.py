"""
Script to combine multiple database files.
"""

# Python library imports
import json
import os
from datetime import datetime
import toml
from numpy import ceil

strftime = datetime.strftime
strptime = datetime.strptime

# Load configuration toml
with open('src/configuration.toml', 'r') as f:
    conf = toml.load(f, _dict=dict)


def load_db(path):
    with open(path) as f:
        db = json.load(f)
    return db


def get_latest_time(gpu1, gpu2):
    """
    Return the most recent data collection time out of two GPU dictionaries.

    Parameters
    ----------
    gpu1 : dict
        First GPU dict.
    gpu2 : dict
        Second GPU dict.

    Returns
    -------
    str
        The most recent data collection time in string format.
    """
    time1 = strptime(gpu1['collection_time'], '%Y-%m-%d %H:%M:%S')
    time2 = strptime(gpu2['collection_time'], '%Y-%m-%d %H:%M:%S')
    if time1 >= time2:
        return time1.strftime('%Y-%m-%d %H:%M:%S')
    return time2.strftime('%Y-%m-%d %H:%M:%S')


def make_new_entry(db_1, gpu2):
    gpu1 = [g for g in db_1['collected']
            if g['name'] == gpu2['name']][0]
    new_entry = {'name': gpu1['name'],
                 'data_collected': True,
                 'collection_time': gpu1['collection_time'],
                 'num_sold': 0,
                 'data': gpu1['data']}
    new_entry['collection_time'] = get_latest_time(gpu1, gpu2)
    return new_entry


def get_new_gpu_names(data_1, data_2):
    # Add new GPU names
    gpu_list1 = [gpu['name'] for gpu in data_1['collected']]
    gpu_list2 = [gpu['name'] for gpu in data_2['collected']]
    gpu_diff = [gpu for gpu in gpu_list2 if gpu not in gpu_list1]
    gpu_shared = [gpu for gpu in gpu_list2 if gpu in gpu_list1]
    return gpu_diff


def already_in_db(item_new, new_entry):
    for item_old in new_entry['data']:
        if item_old == item_new:
            return True
    return False


def get_db_index(db_new, name):
    i = 0
    for item in db_new['collected']:
        if item['name'] == name:
            return i
        i += 1
    return False


data_directory = conf['paths']['filepath']
db_new_name = 'combined_gpu_db.json'

filepaths = os.listdir(data_directory)
filepaths = [f for f in filepaths if '.json' in f]
filepaths = [f for f in filepaths if 'combined' not in f]

# Create new empty database
db_new = {'collected': [],
          'uncollected': []}
with open(data_directory + db_new_name, 'w', encoding='utf-8') as fout:
    json.dump(db_new, fout, indent=4, sort_keys=False)

# Iterate over all other json databases and combined into the
# combined_gpu_db.json file
for file1 in filepaths:
    print(file1)
    # Load existing combined database
    new_data = load_db(data_directory + file1)  # Load database to merge
    gpu_diff = get_new_gpu_names(db_new, new_data)

    for gpu in new_data['collected']:
        if len(gpu["data"]) == 0:
            continue
        if gpu['name'] in gpu_diff:
            print(f'New card added: {gpu["name"]}')
            db_new['collected'].append(gpu)
        else:
            idx = get_db_index(db_new, gpu['name'])
            print(f'Merging data for: {gpu["name"]}')
            # print(f'    {len(gpu["data"])} new cards')
            # print(
            # f'    {len(db_new["collected"][idx]["data"])} cards in database')

            new_entry = make_new_entry(db_new, gpu)
            items_removed = 0
            for item_new in gpu['data']:
                if already_in_db(item_new, new_entry):
                    items_removed += 1
                    continue
                new_entry['data'].append(item_new)
            new_entry['num_sold'] = len(new_entry['data'])
            db_new['collected'][idx] = new_entry
            print(f'    {1-(items_removed/len(gpu["data"])):0.1%} '
                  'of cards added')
    print(f'Number of GPUs in database {len(db_new["collected"])}')
    print('-' * 79)

with open(data_directory + db_new_name, 'w', encoding='utf-8') as fout:
    json.dump(db_new, fout, indent=4, sort_keys=False)
