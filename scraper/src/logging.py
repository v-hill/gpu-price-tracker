"""
Logging setup.
"""
import logging
import logging.config
import sys

CONSOLE_LOGGING = True

logging.basicConfig(
    filename="scraper.log",
    filemode="a",
    format="%(asctime)s | %(levelname)8s | %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO,
)

if CONSOLE_LOGGING:
    # define a Handler which writes INFO messages or higher to sys.stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s |  %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    console.setFormatter(formatter)
    # add the handler to the the current logger
    logging.getLogger().addHandler(console)
