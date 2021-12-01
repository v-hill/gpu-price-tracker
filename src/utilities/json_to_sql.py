"""
Script for converting the legacy json "database" into the new sqlite database
format.
"""
import json
import os
from datetime import datetime

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from src.configuration import PATHS
from src.models import GPU, Log, Sale
from src.utils import get_or_create

engine = sqlalchemy.create_engine(f"sqlite:///{PATHS['database']}")
Session = sessionmaker(bind=engine)


def load_db(path):
    with open(path) as f:
        db = json.load(f)
    return db


def import_json_data(raw_data_filepath):
    filepaths = os.listdir(raw_data_filepath)
    filepaths = [f for f in filepaths if ".json" in f]
    filepaths = [f for f in filepaths if "combined" not in f]

    # Iterate over all json files and import them into the sqlite database
    for file1 in filepaths:
        print(file1)
        new_data = load_db(os.path.join(raw_data_filepath, file1))

        # make log object per each json file

        log_times = [
            datetime.strptime(gpu["collection_time"], "%Y-%m-%d %H:%M:%S")
            for gpu in new_data["collected"]
        ]
        log_start_time = min(log_times)
        log_end_time = max(log_times)

        products_scraped = sum(
            [len(gpu["data"]) for gpu in new_data["collected"]]
        )

        log_kwargs = {
            "start_time": log_start_time,
            "end_time": log_end_time,
            "sales_scraped": products_scraped,
        }

        with Session() as session:
            log_obj, exists = get_or_create(session, Log, **log_kwargs)
            if not exists:
                session.add(log_obj)
                session.commit()
                print("created log", log_obj.log_id)
            else:
                print("log exists", log_obj.log_id)
            new_log_id = log_obj.log_id

        if exists:
            # records for this file already in database
            continue

        else:
            for gpu in new_data["collected"]:
                gpu_kwargs = {"name": gpu["name"]}
                with Session() as session:
                    gpu_obj, exists = get_or_create(session, GPU, **gpu_kwargs)

                # In the case that this gpu has not been added to the database,
                # add all new data. No need to check if existing data for this
                # gpu exists.
                if not exists:
                    with Session() as session:
                        gpu_kwargs = {
                            "name": gpu["name"],
                            "log_id": new_log_id,
                        }

                        gpu_obj, _ = get_or_create(session, GPU, **gpu_kwargs)
                        print(gpu_obj)
                        gpu_obj.last_collection = log_end_time
                        session.add(gpu_obj)
                        session.commit()

                        sale_items_list = []
                        for item in gpu["data"]:
                            item["total_price"] = item.pop("total price")
                            item["date"] = datetime.strptime(
                                item["date"], "%Y-%m-%d %H:%M:%S"
                            )
                            item["log_id"] = new_log_id
                            item["gpu_id"] = gpu_obj.gpu_id
                            sale_obj, exists = get_or_create(
                                session, Sale, **item
                            )
                            if not exists:
                                sale_items_list.append(sale_obj)
                        session.bulk_save_objects(sale_items_list)

                        log = (
                            session.query(Log)
                            .filter(Log.log_id == new_log_id)
                            .first()
                        )
                        if log.sales_added is not None:
                            log.sales_added += len(sale_items_list)
                        else:
                            log.sales_added = len(sale_items_list)
                        print(len(sale_items_list), " sales added")
                        session.commit()

                elif exists:
                    with Session() as session:
                        existing_gpu_obj = (
                            session.query(GPU)
                            .filter(GPU.name == gpu["name"])
                            .first()
                        )
                        log = (
                            session.query(Log)
                            .filter(Log.log_id == new_log_id)
                            .first()
                        )

                        print(
                            f"gpu object exists in table: {existing_gpu_obj}"
                        )

                        # get only new records
                        sale_objs_list = []
                        sale_cols = [
                            "bids",
                            "postage",
                            "total price",
                            "title",
                            "date",
                            "price",
                        ]
                        for item in gpu["data"]:
                            sale_kwargs = {k: item[k] for k in sale_cols}
                            sale_kwargs["date"] = datetime.strptime(
                                sale_kwargs["date"], "%Y-%m-%d %H:%M:%S"
                            )
                            sale_kwargs["total_price"] = sale_kwargs.pop(
                                "total price"
                            )

                            sale_obj, exists = get_or_create(
                                session, Sale, **sale_kwargs
                            )

                            if not exists:
                                sale_obj.log_id = new_log_id
                                sale_obj.gpu_id = existing_gpu_obj.gpu_id
                                sale_objs_list.append(sale_obj)

                        print(
                            f"      {len(sale_objs_list)} /"
                            f" {len(gpu['data'])} added "
                        )
                        session.bulk_save_objects(sale_objs_list)

                        if log.sales_added is not None:
                            log.sales_added += len(sale_objs_list)
                        else:
                            log.sales_added = len(sale_objs_list)
                        session.commit()
