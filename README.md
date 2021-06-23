# gpu-price-tracker
Selenium based web scraper for collecting data on sold GPUs from EBay.

## Useage

You must download the correct version of chromedriver for your browser. To find out which version of chrome you have visit WhatVersion.net using the following link:

https://www.whatversion.net/chrome/

Once you know which version of chrome you're running download the appropriate driver from the following site:

https://chromedriver.chromium.org/downloads

Finally, set the location of your chromedriver path in the configuration.toml file. The entry to edit is:

```
  [paths]
  chromedriver = "C:/{your path here}/"
```

Make any other changes you wish to the program configuration.

The main scraper is exectued by running the 'scraper.py' file. This outputs a .json file containing the sold GPU data.

## Dependencies

This code replies on the following python packages, with minimum version listed where necessary:

```
python: >= 3.6, 
beautifulsoup4 >= 4.9.1
copy
datetime
json
os
pandas >= 1.0.5
re
selenium >= 3.141.0
time
toml >= 0.10.1
```



