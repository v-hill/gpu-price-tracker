import datetime
import logging
import logging.config

import sqlalchemy
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base

from scraper.utils import convert_timedelta, generate_time_since_str

Base = declarative_base()


class Log(Base):
    """
    Log stores data for a run of the scraper.

    Parameter
    ----------
    log_id : int
        Index of the log.
    start_time: datetime
        Start time of scraper.
    end_time: datetime
        End time of scraper, whether completed or failed.
    sales_scraped: int
        Number of products scraped during the run.
    sales_added: int
        Number of products added to the database during the run.
    """

    __tablename__ = "log"
    log_id = Column(Integer, primary_key=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    sales_scraped = Column(Integer)
    sales_added = Column(Integer)

    def __repr__(self):
        return f"{self.log_id} {self.start_time.strftime('%Y/%m/%d %H:%M:%S')}"

    @classmethod
    def get_new_log(cls, session):
        """
        Get the most recent log from the Log table.
        Print the start_time of previous log and time since last run.
        If no prevous log, print no previous runs.
        Iterate log id by 1
        Create new log to use for this run of the scraper.
        """
        most_recent_log = (
            session.query(cls).order_by(sqlalchemy.desc(cls.log_id)).first()
        )
        if most_recent_log is not None:
            diff = datetime.datetime.now() - most_recent_log.start_time
            days, hours, minutes, seconds = convert_timedelta(diff)
            time_since_str = generate_time_since_str(
                days, hours, minutes, seconds
            )
            logging.info(
                "Previous Log entry: "
                f"{most_recent_log.start_time.strftime('%Y/%m/%d %H:%M:%S')}"
            )
            logging.info(time_since_str)

            new_log_id = most_recent_log.log_id + 1
            new_log = cls(
                log_id=new_log_id, start_time=datetime.datetime.now()
            )
        else:
            logging.info("No previous runs on Log")
            new_log = cls(log_id=1, start_time=datetime.datetime.now())
        session.add(new_log)
        session.commit()
        return new_log.log_id


class GPU(Base):
    __tablename__ = "gpu"
    gpu_id = Column(Integer, primary_key=True)
    log_id = Column(
        Integer, ForeignKey("log.log_id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String, unique=True, nullable=False)
    model = Column(String)
    url = Column(String)
    data_collected = Column(Boolean)
    button_id = Column(String)
    last_collection = Column(DateTime)

    def __repr__(self):
        return self.name

    def short_id(self):
        short_id = self.button_id.replace("c4-subPanel-Chipset%", "")
        assert short_id != self.button_id
        return short_id


class Sale(Base):
    __tablename__ = "sale"
    sale_id = Column(Integer, primary_key=True)
    log_id = Column(
        Integer, ForeignKey("log.log_id", ondelete="CASCADE"), nullable=False
    )
    gpu_id = Column(
        Integer, ForeignKey("gpu.gpu_id", ondelete="CASCADE"), nullable=False
    )
    title = Column(String)
    bids = Column(Integer)
    date = Column(DateTime)
    postage = Column(Float(precision=2))
    price = Column(Float(precision=2))
    total_price = Column(Float(precision=2))

    UniqueConstraint(
        "gpu", "title", "date", "bids", "price", "postage", name="gpu_unique"
    )
    CheckConstraint("postage >= 0", name="check_postage")
    CheckConstraint("price > 0", name="check_price")
    CheckConstraint("total_price > 0", name="check_totalprice")
    CheckConstraint("total_price >= price", name="check_price_gte_totalprice")

    def __str__(self):
        return f"£{self.total_price:7.2f} | {self.title}"
