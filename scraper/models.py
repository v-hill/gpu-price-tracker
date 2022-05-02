"""Database model definitions for the scraper data storage."""
import datetime
import logging
import logging.config

from django.db import models
from django.utils.timezone import make_aware

from scraper.src.utils import convert_timedelta, generate_time_since_str


class Log(models.Model):
    """
    Log stores data for a run of the scraper.

    Parameter
    ----------
    start_time: datetime
        Start time of scraper.
    end_time: datetime
        End time of scraper, whether completed or failed.
    sales_scraped: int
        Number of products scraped during the run.
    sales_added: int
        Number of products added to the database during the run.
    """

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    sales_scraped = models.IntegerField(
        help_text="Number of products scraped during the run."
    )
    sales_added = models.IntegerField(
        help_text="Number of products added to the database during the run."
    )

    @property
    def run_time(self):
        return self.end_time - self.start_time

    def __str__(self) -> str:
        return f"{self.id} | {self.start_time.strftime('%Y/%m/%d')}"

    @classmethod
    def get_new_log(cls, reset_hours):
        """Get or create a new runtime log.

        Steps:
         - Get the most recent log from the Log table.
         - Print the start_time of previous log and time since last run.
         - If no prevous log, print no previous runs.
         - Create new log to use for this run of the scraper.
        """
        most_recent_log = cls.objects.all().order_by("-start_time").first()
        current_datetime = make_aware(datetime.datetime.now())

        if most_recent_log is not None:
            diff = cls.find_time_since_last_log(
                most_recent_log, current_datetime
            )
            if diff.total_seconds() <= (60 * 60 * reset_hours):
                return most_recent_log
            else:
                new_id = most_recent_log.id + 1
        else:
            logging.info("No previous runs on Log")
            new_id = 1

        new_log = cls(
            id=new_id,
            start_time=current_datetime,
            end_time=current_datetime,
            sales_scraped=0,
            sales_added=0,
        )
        new_log.save()
        return new_log

    @classmethod
    def find_time_since_last_log(cls, most_recent_log, current_datetime):
        diff = current_datetime - most_recent_log.start_time
        days, hours, minutes, seconds = convert_timedelta(diff)
        time_since_str = generate_time_since_str(days, hours, minutes, seconds)
        logging.info(
            "Previous Log entry: "
            f"{most_recent_log.start_time.strftime('%Y/%m/%d %H:%M:%S')}"
        )
        logging.info(time_since_str)
        return diff


class BrandMenu(models.Model):
    first_log = models.ForeignKey(
        Log, on_delete=models.CASCADE, related_name="first_log"
    )
    latest_log = models.ForeignKey(
        Log, on_delete=models.CASCADE, related_name="latest_log"
    )
    text = models.CharField(max_length=80)
    button_id = models.CharField(max_length=80)

    def __str__(self) -> str:
        return self.text

    def short_id(self):
        """Remove the prefix from the button ID."""
        short_id = self.button_id.replace("c4-subPanel-Chipset%", "")
        assert short_id != self.button_id, "Length of button ID is unchanged"
        return short_id

    @classmethod
    def short_id_from_name(cls, gpu_name):
        button = cls.objects.filter(text__exact=gpu_name).first()
        return button.short_id()

    class Meta:
        """Metadata options."""

        unique_together = ("text",)


class EbayGraphicsCard(models.Model):
    log = models.ForeignKey(Log, on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    collect_data = models.BooleanField(default=True)
    data_collected = models.BooleanField()
    last_collection = models.DateTimeField()
    total_collected = models.IntegerField(blank=True, null=True)

    class Meta:
        """Metadata options."""

        unique_together = ("name",)

    def __str__(self) -> str:
        return self.name


class URL(models.Model):
    url = models.CharField(max_length=200)
    log = models.ForeignKey(Log, on_delete=models.CASCADE)
    gpu = models.ForeignKey(EbayGraphicsCard, on_delete=models.CASCADE)

    class Meta:
        """Metadata options."""

        unique_together = (
            "url",
            "log",
            "gpu",
        )


class Sale(models.Model):
    log = models.ForeignKey(Log, on_delete=models.CASCADE)
    gpu = models.ForeignKey(EbayGraphicsCard, on_delete=models.CASCADE)
    title = models.CharField(max_length=80)
    bids = models.IntegerField()
    date = models.DateTimeField()
    postage = models.FloatField()
    price = models.FloatField()
    total_price = models.FloatField()

    class Meta:
        """Metadata options."""

        unique_together = (
            "gpu",
            "title",
            "date",
            "bids",
            "price",
            "postage",
        )

    def __str__(self):
        return f"£{self.total_price:7.2f} | {self.title}"
