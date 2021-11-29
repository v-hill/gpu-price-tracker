START_URL = "https://www.ebay.co.uk/b/Computer-Graphics-Video-Cards/27386/bn_661667?LH_ItemCondition=3000&LH_PrefLoc=1&LH_Sold=1&rt=nc&_sop=13&_udlo=10"

PATHS = {
    "chromedriver": "C:/user/chromedriver.exe",
    "database": "gpu.db",
    "filepath": "C:/user/Data/",
    "geckodriver": "C:/user/geckodriver.exe",
}

BROWSER = "firefox"  # also available "chrome"

DRIVER_OPTIONS = {"disable_gpu": True}

NUM_RESULTS = {"max": 5000, "min": 20}

FILTERS = {
    "accepted_substrings": ["GTX", "RTX"],
    "always_accept": ["3060", "3070", "3080", "3090"],
}

DATA_READ_RESET_HOURS = 6
