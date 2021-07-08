"""
Script to combine multiple database files.
"""

# Python library imports
import json
import os
from datetime import datetime

strftime = datetime.strftime
strptime = datetime.strptime


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


data_directory = "U:/Work/6_Programming/Ebay_Scaper/New_data/"
filepaths = os.listdir(data_directory)
filepaths = [f for f in filepaths if '.json' in f]
filepaths = [f for f in filepaths if 'combined' not in f]

# Create new empty database
new_db = {'collected': [],
          'uncollected': []}
new_db_name = 'combined_gpu_db.json'
with open(data_directory + new_db_name, 'w', encoding='utf-8') as fout:
    json.dump(new_db, fout, indent=4, sort_keys=False)

# Iterate over all other json databases and combined into the
# combined_gpu_db.json file
for file1 in filepaths[:4]:
    print(file1)
    # Load existing combined database
    with open(data_directory + new_db_name) as f:
        db_1 = json.load(f)

    # Load database to merge
    with open(data_directory + file1) as f:
        db_2 = json.load(f)

    # Add new GPU names
    gpu_list1 = [gpu['name'] for gpu in db_1['collected']]
    gpu_list2 = [gpu['name'] for gpu in db_2['collected']]
    gpu_diff = [gpu for gpu in gpu_list2 if gpu not in gpu_list1]
    gpu_shared = [gpu for gpu in gpu_list2 if gpu in gpu_list1]

    new_db = {'collected': [],
              'uncollected': []}

    for gpu2 in db_2['collected']:
        if gpu2['name'] in gpu_diff:
            print(f'New card added: {gpu2["name"]}')
            new_db['collected'].append(gpu2)
        elif gpu2['name'] in gpu_shared:
            print(f'Merging data for: {gpu2["name"]}')
            gpu1 = [g for g in db_1['collected']
                    if g['name'] == gpu2['name']][0]
            new_entry = {'name': gpu1['name'],
                         'data_collected': True,
                         'collection_time': gpu1['collection_time'],
                         'num_sold': 0,
                         'data': gpu1['data']}

            new_entry['collection_time'] = get_latest_time(gpu1, gpu2)
            new_entry['num_sold'] += gpu2['num_sold']

            items_removed = 0
            for item in gpu2['data']:
                in_new_data = False
                for entry in new_entry['data']:
                    shared_items = {
                        k: entry[k] for k in entry if k in item and entry[k] == item[k]}
                    if len(shared_items) == len(entry):
                        in_new_data = True
                if in_new_data:
                    items_removed += 1
                else:
                    new_entry['data'].append(item)
            new_entry['num_sold'] = len(new_entry['data'])
            new_db['collected'].append(new_entry)
            print(f'    {items_removed} of {len(gpu2["data"])}'
                  ' items shared')
    print('-' * 79)
    with open(data_directory + new_db_name, 'w', encoding='utf-8') as fout:
        json.dump(new_db, fout, indent=4, sort_keys=False)
