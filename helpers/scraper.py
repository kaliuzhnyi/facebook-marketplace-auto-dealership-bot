import os
import pickle
import random
import time

from selenium import webdriver
from selenium.common import NoSuchWindowException
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, WebDriverException
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

import logger
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
            if self.driver.current_url != self.url:
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

    def find_element(self,
                     selector: str | WebElement,
                     by: str = By.CSS_SELECTOR,
                     condition=EC.element_to_be_clickable,
                     exit_on_missing_element: bool = True,
                     wait_element_time: int | None = None) -> WebElement | None:
        """
        Locate an element using Selenium with a waiting condition.

        :param selector: Selector string (e.g. XPath, CSS)
        :param by: Type of selector (By.XPATH, By.CSS_SELECTOR, etc.)
        :param condition: Expected condition to wait for (default: element_to_be_clickable)
        :param wait_element_time: Time to wait for the element (if None, uses self.wait_element_time)
        :param exit_on_missing_element: If True, raises RuntimeError when the element is not found
        :return: WebElement if found, otherwise None (or raises if exit_on_missing_element=True)
        """

        if isinstance(selector, WebElement):
            return selector

        wait_element_time = wait_element_time or self.wait_element_time
        logger.system_logger.debug(f'Trying to find element: {by}="{selector}", timeout={wait_element_time}s')

        try:
            return WebDriverWait(self.driver, wait_element_time).until(condition((by, selector)))
        except TimeoutException:
            logger.system_logger.error(f'Timeout: Element not found: {by}="{selector}"', exc_info=True)
        except WebDriverException as e:
            logger.system_logger.error(f'WebDriver error: {e}', exc_info=True)
        except Exception as e:
            logger.system_logger.error(f'Unknown error: {e}', exc_info=True)

        if exit_on_missing_element:
            raise RuntimeError(f"Element not found: {by}='{selector}'")

        return None

    def find_element_and_click(self,
                               selector: str | WebElement,
                               by: str = By.CSS_SELECTOR,
                               condition=EC.element_to_be_clickable,
                               exit_on_missing_element: bool = True,
                               wait_element_time: int | None = None,
                               use_cursor: bool = True,
                               scroll_to: bool = True) -> WebElement | None:
        element = self.find_element(selector=selector,
                                    by=by,
                                    condition=condition,
                                    exit_on_missing_element=exit_on_missing_element,
                                    wait_element_time=wait_element_time)
        if not element:
            return None

        if scroll_to:
            self.scroll_to_element(selector=element)

        click_result = self.element_click(selector=element, use_cursor=use_cursor)
        if not click_result:
            return None

        return element

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

    def element_click(self,
                      selector: str | WebElement,
                      by: str = By.CSS_SELECTOR,
                      delay: bool = True,
                      exit_on_missing_element: bool = True,
                      use_cursor: bool = False) -> bool:
        """
        Attempts to click an element. Supports both direct click and ActionChains cursor click.

        :param selector: Selector string (e.g. XPath, CSS)
        :param by: Type of selector (By.XPATH, By.CSS_SELECTOR, etc.)
        :param delay: Whether to wait a random delay before clicking
        :param exit_on_missing_element: If True, raises if element is not found
        :param use_cursor: If True, performs click using ActionChains (simulates cursor)
        :return: True if click was successful, False otherwise
        """

        element = self.find_element(selector=selector,
                                    by=by,
                                    condition=EC.element_to_be_clickable,
                                    exit_on_missing_element=exit_on_missing_element)
        if not element:
            return False

        logger.system_logger.debug(f'Trying to click element: {by}="{selector}", use_cursor={use_cursor}')

        try:
            if use_cursor:
                actions = ActionChains(self.driver)
                actions.move_to_element(element)
                if delay:
                    actions.pause(self.get_action_random_delay())
                actions.click().perform()
                logger.system_logger.info(f'Clicked element using cursor: {by}="{selector}"')
            else:
                if delay:
                    self.wait_action_random_time()
                element.click()
                logger.system_logger.info(f'Clicked element: {by}="{selector}"')
            return True
        except ElementClickInterceptedException:
            logger.system_logger.warning(f'ElementClickInterceptedException: fallback to JS click: {by}="{selector}"')
            try:
                self.driver.execute_script("arguments[0].click();", element)
                logger.system_logger.info(f'Clicked element using JS fallback: {by}="{selector}"')
                return True
            except WebDriverException as e:
                logger.system_logger.error(f'JS click failed: {e}', exc_info=True)
        except WebDriverException as e:
            logger.system_logger.error(f'WebDriver error during click: {e}', exc_info=True)
        except Exception as e:
            logger.system_logger.error(f'Unexpected error during click: {e}', exc_info=True)

        return False

    # Wait random time before sending the keys to the element
    def element_send_keys(self,
                          text: str,
                          selector: str,
                          by: str = By.CSS_SELECTOR,
                          delay: bool = True,
                          exit_on_missing_element: bool = True) -> None:
        if delay:
            self.wait_action_random_time()

        element = self.find_element(selector=selector,
                                    exit_on_missing_element=exit_on_missing_element,
                                    by=by)
        if not element:
            return

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

    def element_delete_text(self, selector: str, by: str = By.CSS_SELECTOR, delay: bool = True,
                            exit_on_missing_element: bool = True):
        if delay:
            self.wait_action_random_time()

        element = self.find_element(selector=selector,
                                    by=by,
                                    exit_on_missing_element=exit_on_missing_element)

        # Select all of the text in the input
        element.send_keys(Keys.LEFT_SHIFT + Keys.HOME)
        # Remove the selected text with backspace
        element.send_keys(Keys.BACK_SPACE)

    def element_wait_to_be_invisible(self,
                                     selector: str,
                                     by: str = By.CSS_SELECTOR,
                                     condition=EC.invisibility_of_element_located) -> None:
        """
            Wait until the specified element becomes invisible.

            :param selector: Selector string (XPath, CSS, etc.)
            :param by: Type of selector (By.XPATH, By.CSS_SELECTOR, etc.)
            :param condition: Expected condition to wait for (default: invisibility_of_element_located)
            """
        logger.system_logger.debug(f"Waiting for element to be invisible: {by}='{selector}'")

        try:
            wait_until = condition((by, selector))
            WebDriverWait(self.driver, self.wait_element_time).until(wait_until)
            logger.system_logger.debug(f"Element is now invisible: {by}='{selector}'")
        except TimeoutException:
            logger.system_logger.warning(
                f"Timeout: Element still visible after {self.wait_element_time}s: {by}='{selector}'")
        except WebDriverException as e:
            logger.system_logger.error(f"WebDriver error while waiting invisibility: {e}", exc_info=True)
        except Exception as e:
            logger.system_logger.error(f"Unexpected error while waiting invisibility: {e}", exc_info=True)

    def scroll_to_element(self,
                          selector: str | WebElement,
                          by: str = By.CSS_SELECTOR,
                          exit_on_missing_element: bool = True) -> None:
        """
        Scrolls to an element, preferring ActionChains (user-like behavior),
        and falling back to JS scrollIntoView() if needed.

        :param selector: Selector string (XPath, CSS, etc.)
        :param by: Type of selector (By.XPATH, By.CSS_SELECTOR, etc.)
        :param exit_on_missing_element: If True, raises error or exits if element not found
        """

        element = self.find_element(selector=selector,
                                    by=by,
                                    exit_on_missing_element=exit_on_missing_element)
        if not element:
            return

        logger.system_logger.debug(f"Try scrolling to element: {by}='{selector}'")

        # Try ActionChains first (user-like scroll)
        try:
            logger.system_logger.debug("Trying ActionChains scroll_to_element...")
            ActionChains(self.driver).scroll_to_element(element).perform()
            return
        except Exception as e:
            logger.system_logger.warning(f"ActionChains scroll failed: {e}")

        # Fallback: JS scrollIntoView
        try:
            scroll_config = '{behavior: "auto", block: "start", inline: "nearest"}'
            logger.system_logger.debug(f'Falling back to JS scrollIntoView with {scroll_config}')
            self.driver.execute_script(f'arguments[0].scrollIntoView({scroll_config});', element)
        except Exception as e:
            logger.system_logger.error(f"Both scroll methods failed: {e}", exc_info=True)

    def scroll_to_element_by_xpath(self, xpath, exit_on_missing_element=True) -> None:
        return self.scroll_to_element(selector=xpath, by=By.XPATH, exit_on_missing_element=exit_on_missing_element)

    def send_key(self, key: str, delay: bool = True):
        if delay:
            self.wait_action_random_time()
        ActionChains(self.driver).send_keys(key).perform()


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

    def setup_driver_options(self) -> None:
        self.driver_options = ChromeOptions()
        self.driver_options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        self.driver_options.add_experimental_option('prefs',
                                                    {'profile.default_content_setting_values.notifications': 2})

    def setup_driver(self) -> None:
        chrome_driver = ChromeService(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_driver, options=self.driver_options)
        self.driver.maximize_window()

    def setup_tabs(self) -> None:
        self.tabs = {}

    def create_tab(self, tab_alias: str = None) -> None:

        data_window_handler = None
        try:
            if 'data:' in self.driver.current_url:
                data_window_handler = self.driver.current_window_handle
        except NoSuchWindowException:
            pass

        # Clear tabs and leave there only alive tabs
        self.tabs = {k: v for k, v in self.tabs.items() if v in self.driver.window_handles}

        if not tab_alias:
            tab_alias = f'tab_{len(self.tabs)}'

        if tab_alias in self.tabs.keys() and self.tabs[tab_alias] in self.driver.window_handles:
            self.switch_to_tab(self.tabs[tab_alias])
            return

        try:
            self.driver.switch_to.new_window('tab')
        except NoSuchWindowException:
            for k, v in self.tabs.items():
                if v in self.driver.window_handles:
                    self.switch_to_tab(k)
                    self.create_tab(tab_alias)
                    return

        self.tabs[tab_alias] = self.driver.window_handles[-1]

        if data_window_handler and data_window_handler in self.driver.window_handles:
            self.driver.switch_to.window(data_window_handler)
            self.driver.close()
            self.driver.switch_to.window(self.tabs[tab_alias])

    def switch_to_tab(self, tab_alias: str) -> None:
        self.driver.switch_to.window(self.tabs[tab_alias])

    def _get_first_alive_tab(self) -> str | None:
        for alias, handle in self.tabs.items():
            try:
                self.driver.switch_to.window(handle)
                self.driver.execute_script("return 1;")
                return alias
            except:
                continue
        return None
