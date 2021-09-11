import json

card_dicts = [
    {
        "search_term": "1050",
        "title": "NVIDIA GeForce GTX 1050 Ti",
        "gb_required": "4g|4G|4 g|4 G",
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1060",
        "title": "NVIDIA GeForce GTX 1060 3GB",
        "gb_required": "3g|3G|3 g|3 G",
        "gb_exclude": "6g|6G|6 g|6 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1060",
        "title": "NVIDIA GeForce GTX 1060 6GB",
        "gb_required": "6g|6G|6 g|6 G",
        "gb_exclude": "3g|3G|3 g|3 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1070",
        "title": "NVIDIA GeForce GTX 1070",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1070",
        "title": "NVIDIA GeForce GTX 1070 TI",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1080",
        "title": "NVIDIA GeForce GTX 1080",
        "gb_required": False,
        "gb_exclude": "11g|11G|11 g|11 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1080",
        "title": "NVIDIA GeForce GTX 1080 TI",
        "gb_required": False,
        "gb_exclude": "8g|8G|8 g|8 G",
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2060",
        "title": "NVIDIA GeForce RTX 2060",
        "gb_required": False,
        "gb_exclude": "8g|8G|8 g|8 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2060",
        "title": "NVIDIA GeForce RTX 2060 Super",
        "gb_required": False,
        "gb_exclude": "6g|6G|6 g|6 G",
        "new": False,
        "super": True,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2070",
        "title": "NVIDIA GeForce RTX 2070",
        "gb_required": False,
        "gb_exclude": "6g|6G|6 g|6 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2070",
        "title": "NVIDIA GeForce RTX 2070 Super",
        "gb_required": False,
        "gb_exclude": "6g|6G|6 g|6 G",
        "new": False,
        "super": True,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2080",
        "title": "NVIDIA GeForce RTX 2080",
        "gb_required": False,
        "gb_exclude": "11g|11G|11 g|11 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2080",
        "title": "NVIDIA GeForce RTX 2080 Super",
        "gb_required": False,
        "gb_exclude": "8g|8G|8 g|8 G",
        "new": False,
        "super": True,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "2080",
        "title": "NVIDIA GeForce RTX 2080 TI",
        "gb_required": False,
        "gb_exclude": "8g|8G|8 g|8 G",
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3060",
        "title": "NVIDIA GeForce RTX 3060",
        "gb_required": False,
        "gb_exclude": "8g|8G|8 g|8 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3060",
        "title": "NVIDIA GeForce RTX 3060 TI",
        "gb_required": False,
        "gb_exclude": "12g|12G|12 g|12 G",
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3070",
        "title": "NVIDIA GeForce RTX 3070",
        "gb_required": False,
        "gb_exclude": "12g|12G|12 g|12 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3070",
        "title": "NVIDIA GeForce RTX 3070 TI",
        "gb_required": False,
        "gb_exclude": "12g|12G|12 g|12 G",
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3080",
        "title": "NVIDIA GeForce RTX 3080",
        "gb_required": False,
        "gb_exclude": "12g|12G|12 g|12 G",
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3080",
        "title": "NVIDIA GeForce RTX 3080 TI",
        "gb_required": False,
        "gb_exclude": "10g|10G|10 g|10 G",
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "3090",
        "title": "NVIDIA GeForce RTX 3090",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "970",
        "title": "NVIDIA GeForce GTX 970",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "750",
        "title": "NVIDIA GeForce GTX 750",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "750",
        "title": "NVIDIA GeForce GTX 750 TI",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "980",
        "title": "NVIDIA GeForce GTX 980",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "980",
        "title": "NVIDIA GeForce GTX 980 TI",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "960",
        "title": "NVIDIA GeForce GTX 960",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1050",
        "title": "NVIDIA GeForce GTX 1050",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "760",
        "title": "NVIDIA GeForce GTX 760",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "770",
        "title": "NVIDIA GeForce GTX 770",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1660",
        "title": "NVIDIA GeForce GTX 1660",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1660",
        "title": "NVIDIA GeForce GTX 1660 Super",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": True,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "1660",
        "title": "NVIDIA GeForce GTX 1660 TI",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "_660",
        "title": "NVIDIA GeForce GTX 660",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": False,
        "mini": False,
        "founders": False,
    },
    {
        "search_term": "_660",
        "title": "NVIDIA GeForce GTX 660 TI",
        "gb_required": False,
        "gb_exclude": False,
        "new": False,
        "super": False,
        "ti": True,
        "mini": False,
        "founders": False,
    },
]


with open("./analysis/gpu_plots.json", "w") as outfile:
    json.dump(card_dicts, outfile, indent=4, sort_keys=False)
