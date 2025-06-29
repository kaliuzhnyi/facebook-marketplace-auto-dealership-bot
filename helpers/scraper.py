import os
import pickle
import random
import time

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class Scraper:
    # This time is used when we are waiting for element to get loaded in the html
    wait_element_time = 30

    # In this folder we will save cookies from logged in users
    cookies_folder = 'cookies' + os.path.sep

    def __init__(self, url: str | None = None, driver=None):
        self.url = url
        self.tabs = {}

        if not driver:
            self.setup_driver_options()
            self.setup_driver()
        else:
            self.driver = driver

        if url:
            self.driver.get(url)

    # Add these options in order to make chrome driver appear as a human instead of detecting it as a bot
    # Also change the 'cdc_' string in the chromedriver.exe with Notepad++ for example with 'abc_' to prevent detecting it as a bot
    def setup_driver_options(self):
        self.driver_options = Options()

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
        chrome_driver = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_driver, options=self.driver_options)
        self.driver.maximize_window()

    # Automatically close driver on destruction of the object
    def __del__(self):
        self.driver.close()

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

    # Add login functionality and load cookies if there are any with 'cookies_file_name'
    def add_login_functionality(self,
                                login_url: str,
                                after_login_url:str,
                                is_logged_in_selector: str,
                                cookies_file_name: str):
        self.login_url = login_url
        self.after_login_url = after_login_url
        self.is_logged_in_selector = is_logged_in_selector
        self.cookies_file_name = cookies_file_name + '.pkl'
        self.cookies_file_path = self.cookies_folder + self.cookies_file_name

        # Check if there is a cookie file saved
        if self.is_cookie_file():
            # Load cookies
            self.load_cookies()
            self.go_to_page(self.after_login_url)

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
        self.go_to_page(self.after_login_url)

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

        if self.url:
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

    # Check if user is logged in based on a html element that is visible only for logged in users
    def is_logged_in(self, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        return self.find_element(selector=self.is_logged_in_selector,
                                 exit_on_missing_element=False,
                                 wait_element_time=wait_element_time)

    # Wait random amount of seconds before taking some action so the server won't be able to tell if you are a bot
    def wait_random_time(self):
        random_sleep_seconds = round(random.uniform(0.20, 1.20), 2)

        time.sleep(random_sleep_seconds)

    # Goes to a given page and waits random time before that to prevent detection as a bot
    def go_to_page(self, page):
        # Wait random time before refreshing the page to prevent the detection as a bot
        self.wait_random_time()

        # Refresh the site url with the loaded cookies so the user will be logged in
        self.driver.get(page)

    def find_element(self, selector, by=By.CSS_SELECTOR, exit_on_missing_element=True, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        # Initialize the condition to wait
        wait_until = EC.element_to_be_clickable((by, selector))

        try:
            # Wait for element to load
            element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
        except:
            if exit_on_missing_element:
                print('ERROR: Timed out waiting for the element with css selector "' + selector + '" to load')
                # End the program execution because we cannot find the element
                exit()
            else:
                return False

        return element

    def find_element_by_xpath(self, xpath, exit_on_missing_element=True, wait_element_time=None):
        if wait_element_time is None:
            wait_element_time = self.wait_element_time

        # Initialize the condition to wait
        wait_until = EC.element_to_be_clickable((By.XPATH, xpath))

        try:
            # Wait for element to load
            element = WebDriverWait(self.driver, wait_element_time).until(wait_until)
        except:
            if exit_on_missing_element:
                # End the program execution because we cannot find the element
                print('ERROR: Timed out waiting for the element with xpath "' + xpath + '" to load')
                exit()
            else:
                return False

        return element

    # Wait random time before clicking on the element
    def element_click(self, selector, by=By.CSS_SELECTOR, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_random_time()

        element = self.find_element(selector=selector,
                                    by=by,
                                    exit_on_missing_element=exit_on_missing_element)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    # Wait random time before clicking on the element
    def element_click_by_xpath(self, xpath, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_random_time()

        element = self.find_element_by_xpath(xpath, exit_on_missing_element)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    # Wait random time before sending the keys to the element
    def element_send_keys(self, selector, text, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_random_time()

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
            self.wait_random_time()

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

        self.wait_random_time()

        try:
            input_file.send_keys(files)
        except InvalidArgumentException:
            print('ERROR: Exiting from the program! Please check if these file paths are correct:\n' + files)
            exit()

    # Wait random time before clearing the element
    def element_clear(self, selector, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_random_time()

        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element)

        element.clear()

    def element_delete_text(self, selector, delay=True, exit_on_missing_element=True):
        if delay:
            self.wait_random_time()

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
