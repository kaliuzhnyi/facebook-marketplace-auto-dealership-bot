import os
import pickle
import random
import time

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import CONFIG


class Scraper:
    # This time is used when we are waiting for element to get loaded in the html
    wait_element_time = 30

    action_wait_random_time_min = CONFIG['scraper']['action_random_delay']['min']
    action_wait_random_time_max = CONFIG['scraper']['action_random_delay']['max']

    listing_random_delay_min = CONFIG['scraper']['listing_random_delay']['min']
    listing_random_delay_max = CONFIG['scraper']['listing_random_delay']['max']

    # In this folder we will save cookies from logged-in users
    cookies_folder = 'cookies' + os.path.sep

    def __init__(self, url: str, driver: WebDriver | None = None):
        self.url = url

        if not driver:
            self.setup_driver_options()
            self.setup_driver()
        else:
            self.driver = driver

        self.go_to_page(url)

    # Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
    # Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
    def setup_driver_options(self):
        self.driver_options = ChromeOptions()

        arguments = [
            '--disable-blink-features=AutomationControlled'
        ]

        experimental_options = {
            'excludeSwitches': ['enable-automation', 'enable-logging'],
            'prefs': {'profile.default_content_setting_values.notifications': 2}
        }

        for argument in arguments:
            self.driver_options.add_argument(argument)

        for key, value in experimental_options.items():
            self.driver_options.add_experimental_option(key, value)

    # Setup chrome driver with predefined options
    def setup_driver(self):
        chrome_driver = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_driver, options=self.driver_options)
        self.driver.maximize_window()

    # Automatically close driver on destruction of the object
    def __del__(self):
        self.driver.close()

    # Add login functionality and load cookies if there are any with 'cookies_file_name'
    def add_login_functionality(self,
                                login_url: str,
                                is_logged_in_selector: str,
                                cookies_file_name: str):
        self.login_url = login_url
        self.is_logged_in_selector = is_logged_in_selector
        self.cookies_file_name = cookies_file_name + '.pkl'
        self.cookies_file_path = self.cookies_folder + self.cookies_file_name

        # Check if there is a cookie file saved
        if self.is_cookie_file():
            # Load cookies
            self.load_cookies()
            self.go_to_page(self.url)

            # Check if user is logged in after adding the cookies
            is_logged_in = self.is_logged_in(5)
            if is_logged_in:
                return

        self.driver.get(self.login_url)
        # Wait for the user to log in with maximum amount of time 5 minutes
        print(
            'Please login manually in the browser and after that you will be automatically logged in with cookies. Note that if you do not log in for five minutes, the program will turn off.')
        is_logged_in = self.is_logged_in(300)

        # User is not logged in so exit from the program
        if not is_logged_in:
            exit()

        # User is logged in so save the cookies
        self.save_cookies()
        self.go_to_page(self.url)

    # Check if cookie file exists
    def is_cookie_file(self):
        return os.path.exists(self.cookies_file_path)

    # Load cookies from file
    def load_cookies(self):
        # Load cookies from the file
        cookies_file = open(self.cookies_file_path, 'rb')
        cookies = pickle.load(cookies_file)

        for cookie in cookies:
            self.driver.add_cookie(cookie)

        cookies_file.close()

        self.go_to_page(self.url)

    # Save cookies to file
    def save_cookies(self):
        # Do not save cookies if there is no cookies_file name
        if not hasattr(self, 'cookies_file_path'):
            return

        # Create folder for cookies if there is no folder in the project
        if not os.path.exists(self.cookies_folder):
            os.mkdir(self.cookies_folder)

        # Open or create cookies file
        cookies_file = open(self.cookies_file_path, 'wb')

        # Get current cookies from the driver
        cookies = self.driver.get_cookies()

        # Save cookies in the cookie file as a byte stream
        pickle.dump(cookies, cookies_file)

        cookies_file.close()

    # Check if user is logged in based on a html element that is visible only for logged-in users
    def is_logged_in(self, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        return self.find_element(selector=self.is_logged_in_selector,
                                 exit_on_missing_element=False,
                                 wait_element_time=wait_element_time)

    # Wait random amount of seconds before taking some action so the server won't be able to tell if you are a bot
    def wait_action_random_time(self) -> None:
        self.wait_random_time(self.action_wait_random_time_min, self.action_wait_random_time_max)

    def wait_listing_random_time(self) -> None:
        self.wait_random_time(self.listing_random_delay_min, self.listing_random_delay_max)

    @classmethod
    def wait_random_time(cls, min_delay: int, max_delay: int) -> None:
        random_sleep_seconds = cls.get_random_delay(min_delay, max_delay)
        time.sleep(random_sleep_seconds)

    def get_action_random_delay(self):
        return self.get_random_delay(self.action_wait_random_time_min, self.action_wait_random_time_max)

    @classmethod
    def get_random_delay(cls, min_delay: int, max_delay: int) -> int:
        return int(round(random.uniform(min_delay, max_delay), 2))

    # Goes to a given page and waits random time before that to prevent detection as a bot
    def go_to_page(self, page: str):
        # Wait random time before refreshing the page to prevent the detection as a bot
        self.wait_action_random_time()

        # Refresh the site url with the loaded cookies so the user will be logged in
        self.driver.get(page)

    def find_element(self, selector: str, by: str = By.CSS_SELECTOR, exit_on_missing_element: bool = True,
                     wait_element_time: int | None = None) -> WebElement | None:
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        # Initialize the condition to wait
        wait_until = EC.element_to_be_clickable((by, selector))

        try:
            # Wait for element to load
            element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
        except:
            if exit_on_missing_element:
                print(f'ERROR: Timed out waiting for the element with {by} "{selector}" to load')
                # End the program execution because we cannot find the element
                exit()
            else:
                return None

        return element

    def find_element_by_xpath(self, xpath: str, exit_on_missing_element: bool = True,
                              wait_element_time: int | None = None) -> WebElement | None:
        return self.find_element(selector=xpath, by=By.XPATH, exit_on_missing_element=exit_on_missing_element,
                                 wait_element_time=wait_element_time)

    def find_elements_with_scrolling(self, selector: str, by: str, wait_elements_time: int | None = 10) -> list[
        WebElement]:
        if wait_elements_time is None:
            wait_elements_time = self.wait_element_time

        wait = WebDriverWait(self.driver, wait_elements_time)
        scroll_element = self.driver.find_element(By.TAG_NAME, 'body')

        while True:
            elements = self.driver.find_elements(by=by, value=selector)
            current_elements_count = len(elements)

            scroll_element.send_keys(Keys.END)

            try:
                wait.until(lambda d: len(d.find_elements(by=by, value=selector)) > current_elements_count)
            except:
                break

        return elements

    # Wait random time before clicking on the element
    def element_click(self, selector,
                      by=By.CSS_SELECTOR,
                      delay=True,
                      exit_on_missing_element=True,
                      use_cursor=False):

        element = self.find_element(selector=selector, by=by, exit_on_missing_element=exit_on_missing_element)

        try:
            if use_cursor:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).pause(self.get_action_random_delay()).click().perform()
            else:
                if delay:
                    self.wait_action_random_time()
                element.click()
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    # Wait random time before clicking on the element
    def element_click_by_xpath(self, xpath, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element_by_xpath(xpath, exit_on_missing_element)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    # Wait random time before sending the keys to the element
    def element_send_keys(self, selector, text, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

        element.send_keys(text)

    # Wait random time before sending the keys to the element
    def element_send_keys_by_xpath(self, xpath, text, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element_by_xpath(xpath, exit_on_missing_element)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

        element.send_keys(text)

    def input_file_add_files(self, selector, files):
        # Initialize the condition to wait
        wait_until = EC.presence_of_element_located((By.CSS_SELECTOR, selector))

        try:
            # Wait for input_file to load
            input_file = WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
        except:
            print('ERROR: Timed out waiting for the input_file with selector "' + selector + '" to load')
            # End the program execution because we cannot find the input_file
            exit()

        self.wait_action_random_time()

        try:
            input_file.send_keys(files)
        except InvalidArgumentException:
            print('ERROR: Exiting from the program! Please check if these file paths are correct:\n' + files)
            exit()

    # Wait random time before clearing the element
    def element_clear(self, selector: str, delay: bool = True, exit_on_missing_element: bool = True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element)

        element.clear()

    def element_delete_text(self, selector: str, delay: bool = True, exit_on_missing_element: bool = True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element)

        # Select all of the text in the input
        element.send_keys(Keys.LEFT_SHIFT + Keys.HOME)
        # Remove the selected text with backspace
        element.send_keys(Keys.BACK_SPACE)

    def element_wait_to_be_invisible(self, selector):
        wait_until = EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))

        try:
            WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
        except:
            print('Warning when waiting the element with selector "' + selector + '" to be invisible')

    def element_wait_to_be_invisible_by_xpath(self, xpath):
        wait_until = EC.invisibility_of_element_located((By.XPATH, xpath))

        try:
            WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
        except:
            print('Warning when waiting the element with xpath "' + xpath + '" to be invisible')

    def scroll_to_element(self, selector, exit_on_missing_element=True):
        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element)

        self.driver.execute_script('arguments[0].scrollIntoView(true);', element)

    def scroll_to_element_by_xpath(self, xpath, exit_on_missing_element=True):
        element = self.find_element_by_xpath(xpath, exit_on_missing_element)

        self.driver.execute_script('arguments[0].scrollIntoView(true);', element)


class ScraperDriverManager:

    def __init__(self,
                 driver_options: ChromeOptions | None = None,
                 driver: webdriver.Chrome | None = None,
                 tabs: dict[str, str] | None = None):
        self.driver_options = driver_options
        self.driver = driver
        self.tabs = tabs

        if not self.driver_options:
            self.setup_driver_options()

        if not self.driver:
            self.setup_driver()

        if not self.tabs:
            self.setup_tabs()

    def setup_driver_options(self):
        self.driver_options = ChromeOptions()
        self.driver_options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        self.driver_options.add_experimental_option('prefs',
                                                    {'profile.default_content_setting_values.notifications': 2})

    def setup_driver(self):
        chrome_driver = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_driver, options=self.driver_options)
        self.driver.maximize_window()

    def setup_tabs(self):
        self.tabs = {}

    def create_tab(self, tab_alias: str = None, and_switch: bool = False):
        if not tab_alias:
            tab_alias = f'tab_{len(self.tabs)}'
        self.driver.execute_script("window.open('about:blank', '_blank');")

        if not len(self.tabs):
            if 'data:,' in self.driver.current_url:
                self.driver.close()

        self.tabs[tab_alias] = self.driver.window_handles[-1]

        if and_switch:
            self.switch_to_tab(tab_alias)

    def switch_to_tab(self, tab_alias: str):
        self.driver.switch_to.window(self.tabs[tab_alias])
