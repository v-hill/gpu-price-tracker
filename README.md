# gpu-price-tracker
Selenium based web scraper for collecting data on sold GPUs from EBay.

## Useage

The main scraper is exectued by running the 'scraper.py' file. This outputs a .json file containing the sold GPU data.

### For Chrome:

You must download the correct version of chromedriver for your browser. To find out which version of Chrome you have visit WhatVersion.net using the following link:

https://www.whatversion.net/chrome/

Once you know which version of Chrome you're running download the appropriate driver from the following site:

https://chromedriver.chromium.org/downloads

### For Firefox:

You must download the Mozilla geckodriver for the Firefox browser.

The latest geckodriver release can be downloaded from the following site:

https://github.com/mozilla/geckodriver/releases

## Configuration
### PATHS (dict)


Set the location of your chromedriver or geckodriver path in the configuration.toml file. The entry to edit is:

```
  [paths]
  chromedriver = "C:/{your path here}/chromedriver.exe"
  geckodriver = "C:/{your path here}/geckodriver.exe"
```

The name of the database is set by the following entry:
```
[paths]
database = "gpu.db"
```
The database is created in the root of the project directory.

### BROWSER (str)

Then set the web broswer for Selenium to use.
Currently supports Firefox and Chrome.

```
BROWSER = "firefox"  # also available "chrome"
```

### DRIVER_OPTIONS (dict)

This is space to add additional configuration, such as disabling gpu acceleration in the browser.

```
DRIVER_OPTIONS = {"disable_gpu": True}
```

### NUM_RESULTS (dict)

The 'max' value sets the maximum number of results on a page, without raising an exception.
Typically there are around ~17,000 results on the start url. After navigating to a particular GPU this number is significantly lower, no more than a few hundred results.
If the scraper navigates to a page and there are ~17,000 results, an error has occured and the correct buttons have not been pressed. To account for changes in the number of results, the default max limit is set at 5000.


The 'min' value specifies the lowest number of results to still be added to the database. If the number of results for a GPU is below the minimum, no data is collected.

```
NUM_RESULTS = {"max": 5000, "min": 20}
```
