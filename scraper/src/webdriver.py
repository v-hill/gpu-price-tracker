"""Setup for selenium webdriver."""
import logging
import logging.config
import time

import selenium.webdriver.chrome.options as chrome
import selenium.webdriver.firefox.options as firefox
from selenium import webdriver

DRIVER_OPTIONS = {"disable_gpu": True}


def get_driver_options(browser):
    logging.info(f"    {browser.capitalize()} browser selected")
    if browser not in ["chrome", "firefox"]:
        raise Exception(f"Browser {browser} is not 'chrome' or 'firefox'")

    if browser == "chrome":
        browser_options = chrome.Options()
    elif browser == "firefox":
        browser_options = firefox.Options()

    browser_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    if bool(DRIVER_OPTIONS["disable_gpu"]):
        browser_options.add_argument("--disable-gpu")  # Disable GPU
    return browser_options


def get_main_webdriver(browser, paths):
    browser_options = get_driver_options(browser)  # Setup driver options
    if browser == "chrome":
        main_webdriver = webdriver.Chrome(
            paths["chromedriver"], options=browser_options
        )
    if browser == "firefox":
        main_webdriver = webdriver.Firefox(
            executable_path=paths["geckodriver"], options=browser_options
        )
        time.sleep(5)
    return main_webdriver
