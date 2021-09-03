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

## TOML configuration:

### [paths] key


Set the location of your chromedriver or geckodriver path in the configuration.toml file. The entry to edit is:

```
  [paths]
  chromedriver = "C:/{your path here}/"
  geckodriver = "C:/{your path here}/"
```

The name of the database is set by the following entry:
```
[paths]
database = "gpu_db.json"
```

The filepath key sets the folder which the database gets saved to.
```
[paths]
filepath = "C://...../Data/"
```

The date on which the scraper is run is automatically appended to the database name (e.g. 2021_01_01_gpu_db.json). 

### [browser] key

Then set the approripate broswer flag in the configuration file to True. For example, when using Firefox, the config should be as follows:

```
  [browser]
  chrome = "False"
  firefox = "True"
```

### [driver_options] key

This is space to add additional configuration, such as disabling gpu acceleration in the browser.

'''
[driver_options]
disable_gpu = "True"
'''


## Dependencies

This code replies on the following python packages, with minimum version listed where necessary:

```
python: >= 3.6, 
beautifulsoup4 >= 4.9.1
pandas >= 1.0.5
selenium >= 3.141.0
toml >= 0.10.1
```



