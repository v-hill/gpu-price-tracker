"""Module for webpage related classes."""
import logging
import logging.config
import re
import time

from bs4 import BeautifulSoup

from scraper.src.product import EBayItem


class WebPage:
    """Base representation of an EBay webpage.

    Parameters
    ----------
    driver : webdriver.Webdriver
        Seleniumwebdriver used to communicate with the browser window.
    start_url : str
        The URL of the webpage
    """

    def __init__(self, driver, start_url: str):
        self.driver = driver
        self.start_url = start_url

    def return_to_start_url(self):
        """Return the browser to the starting URL of the webpage."""
        try:
            self.driver.get(self.start_url)
            time.sleep(3)
        except BaseException:
            raise Exception("Could not return to start url")

    def page_source_soup(self):
        """Return a BeautifulSoup soup representation of the current webpage."""
        return BeautifulSoup(self.driver.page_source, "html.parser")

    def close_webpage(self):
        self.driver.close()


# -----------------------------------------------------------------------------


class MainWebPage(WebPage):
    def __init__(self, driver, start_url: str):
        """Class to represent the webpage that is initially opened.

        Inhertied from base WebPage class. Represents the first page opened,
        with functions for accepting cookies, opening menus and selecting a
        particular product.

        Parameters
        ----------
        driver : selenium.webdriver....WebDriver
            The selenium webdriver.

        """
        WebPage.__init__(self, driver, start_url)
        self.return_to_start_url()

    def auto_accept_cookies(self):
        soup = self.page_source_soup()
        # get button id
        try:
            accept_button_id = ""
            for button in soup.find_all("button"):
                if "accept" in str(button.text).lower():
                    accept_button_id = button["id"]
                    logging.info("    Accept cookies button found")
                    break
        except BaseException:
            logging.exception("No cookies accept button found in page")

        # click on button
        if accept_button_id != "":
            assert accept_button_id == "gdpr-banner-accept"
            try:
                gdpr_button = self.driver.find_element_by_id(accept_button_id)
                gdpr_button.click()
                logging.info("    Cookies successfully accepted")
                time.sleep(2)
            except:
                logging.exception(
                    "    Unable to click on accept cookies button"
                )

    def open_model_menu(self):
        soup = self.page_source_soup()
        try:
            button_css = ""
            for button in soup.find_all("button"):
                if "GPU Model" in button.text:
                    # print(button.prettify()) # For debug
                    aria_controls_text = button["aria-controls"]
                    button_css = f'[aria-controls="{aria_controls_text}"]'
                    break
        except BaseException:
            logging.exception("No GPU model menu button found in page")
        if button_css != "":
            menu_button = self.driver.find_element_by_css_selector(button_css)
            menu_button.click()
            time.sleep(1)

    def open_all_filter_menu(self):
        soup = self.page_source_soup()
        try:
            button_css = ""
            for button in soup.find_all("button"):
                if "see all" in button.text:
                    aria_label_text = button["aria-label"]
                    if "gpu model" in aria_label_text.lower():
                        # print(button.prettify()) # For debug
                        button_css = f'[aria-label="{aria_label_text}"]'
        except BaseException:
            logging.exception("See all menu button not found")
        if button_css != "":
            see_all_button = self.driver.find_element_by_css_selector(
                button_css
            )
            see_all_button.click()
            time.sleep(2)
        else:
            logging.exception("No see all menu button found in page")

    def get_brand_menu_items(self):
        """Get the available GPU products in te brand menu.

        Given the Chipset/GPU Model menu, create a list of entries for the gpu
        table for the set of available products in the menu.
        """
        menu = self.page_source_soup().find(
            "div", {"class": "x-overlay__wrapper--right"}
        )
        options = menu.find_all(
            "div",
            {
                "class": (
                    "x-refine__multi-select x-overlay-sub-panel__aspect-option"
                )
            },
        )
        if len(options) == 0:
            logging.exception("No options found in Chipset/GPU model menu")
        else:
            logging.info(
                f"    {len(options)} options found in Chipset/GPU model menu"
            )
        return options

    def select_option(self, button_id: str):
        """Select an option from the menu given a GraphicsCard object.

        Keeps trying to select option until successful for 10 seconds.

        Parameters
        ----------
        product : GraphicsCard
            The product to select
        """
        start_time = time.time()
        while (time.time() - start_time) <= 10:
            try:
                option_button = self.driver.find_element_by_css_selector(
                    f'[id*="{button_id}"]'
                )
                option_button.click()
                time.sleep(1)
                return 1
            except BaseException:
                time.sleep(1)
        if True:
            raise Exception("Unable to select option from the brands menu")

    def apply_selection(self):
        """Press the apply button.

        Press the apply button to navigate to the page with the applied
        filters.
        """
        button_css = '[aria-label="Apply"]'
        apply_button = self.driver.find_element_by_css_selector(button_css)
        apply_button.click()
        time.sleep(3)


# -----------------------------------------------------------------------------


class Pagination:
    """Class for representing an a page option in the pagination bar."""

    def __init__(self, page_num: int, label: str, href: str):
        self.page_num = page_num
        self.label = label
        self.href = href
        self.data_collected = False

    def __repr__(self):
        return f"page num: {self.page_num}, label: {self.label}"


# -----------------------------------------------------------------------------


class BrandWebPage(WebPage):
    def __init__(self, driver, start_url: str):
        WebPage.__init__(self, driver, start_url)
        self.pages = []
        self.current_page = None
        self.next_page = None
        self.num_results = 0

    def check_number_of_results(self):
        """Find the number of results on a page.

        Raise an error if the number of results is suspicously high, or if the
        number of results could not be found.

        Raises
        ------
        Exception
            If the number of results is above the number of results maximum
            then an exception is thrown. This catches instances where the
            driver fails to navigate to the correct GPU page.
        """
        max_results = 10000
        soup = self.page_source_soup()
        num_results = soup.find_all(
            "h2", {"class": "srp-controls__count-heading"}
        )

        if len(num_results) == 0:
            exception = "Could not find number of results"
            logging.exception(exception)
            raise Exception(exception)

        num_results_str = str(num_results[0].text).replace(",", "")
        num_results = int(re.findall(r"\d+", num_results_str)[0])
        logging.info(f"    {num_results} results found")
        if num_results >= max_results:
            exception = (
                f"Number of results found ({num_results}) exceeds maximum"
                f" allowed value of {max_results}"
            )
            logging.exception(exception)
            raise Exception(exception)
        return num_results

    def get_pages(self):
        """Populate list of Pagination objects."""
        soup = self.page_source_soup()
        self.pages = []
        pagination = soup.find("div", {"class": "b-pagination"})
        try:
            options = pagination.find_all(
                "a", {"class": re.compile("pagination__item")}
            )
        except BaseException:
            options = []
            # print('Warning: No pagination found')

        # if self.num_results < 48 and len(options) <= 1:
        #     print('Warning: Not enough pages '
        #           f'found for {self.num_results} items')
        for option in options:
            href = ""
            page_num = int(option.text)
            if "aria-current" in option.attrs:
                label = "current"  # Text label
            else:
                label = option["type"]
            try:
                href = option["href"]
            except BaseException:
                pass
            self.pages.append(Pagination(page_num, label, href))

    def get_next_page(self):
        self.get_pages()
        for page in self.pages:
            if page.label == "current":
                self.current_page = page
                break

        self.next_page = None
        for page in self.pages:
            if page.page_num == (self.current_page.page_num + 1):
                self.next_page = page
                break
        # print(f'current: {self.current_page}\n   '
        #       f'next: {self.next_page}') # For debug

    def nav_to_next_page(self):
        self.get_next_page()
        if self.next_page is not None:
            try:
                self.driver.get(self.next_page.href)
                time.sleep(0.5)
                return True
            except BaseException:
                raise Exception("Could not navigate to next page")
        return False

    def make_items(self):
        soup = self.page_source_soup()
        items_container = soup.find(
            "ul", {"class": re.compile("srp-results srp-grid")}
        )
        item_tags = items_container.find_all(
            "div", {"class": "s-item__wrapper clearfix"}
        )
        if len(item_tags) == 0:
            raise Exception("No items found on page")

        return [EBayItem(tag) for tag in item_tags]
