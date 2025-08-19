import re
import unicodedata
from collections import deque
from datetime import datetime

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from config import CONFIG
from helpers.model import Listing, PublishedListing, FuelType
from helpers.scraper import Scraper
from logger import system_logger

PAGES = {
    'selling': 'https://facebook.com/marketplace/you/selling',
    'create_new_listing': 'https://www.facebook.com/marketplace/create',
    'create_new_listing_vehicle': 'https://www.facebook.com/marketplace/create/vehicle'
}


class XPATH:

    @classmethod
    def selling_listing_container_clickable_element(cls, listing_title: str) -> str:
        cls.translate_expr('@aria-label', ' ')
        return f'//div/div/div/div[2]/div/div[{cls.translate_eq_expr(normalize_title_for_compare(listing_title), "@aria-label", " ")}]'

    @classmethod
    def selling_listing_container(cls, listing_title: str) -> str:
        return f'//div[.{cls.selling_listing_container_clickable_element(listing_title)[1:]}]'

    @classmethod
    def selling_search_input(cls):
        return f'//input[{cls.translate_eq_expr("search your listings", "@placeholder")}]'

    @classmethod
    def translate_expr(cls, str1: str, str2: str = '', str3: str = ''):
        return f'translate({str1}, "ABCDEFGHIJKLMNOPQRSTUVWXYZАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ{str2}", "abcdefghijklmnopqrstuvwxyzабвгґдеєжзиіїйклмнопрстуфхцчшщъыьэюя{str3}")'

    @classmethod
    def translate_eq_expr(cls, value: str, str1: str, str2: str = '', str3: str = ''):
        return f'{cls.translate_expr(str1, str2, str3)} = "{value.lower()}"'

    @classmethod
    def translate_cont_expr(cls, value: str, str1: str, str2: str = '', str3: str = ''):
        return f'contains({cls.translate_expr(str1, str2, str3)}, "{value.lower()}")'


def check_and_update_listings(scraper: Scraper, listings: list[Listing],
                              published_listings: list[WebElement] | None = None,
                              listings_limit: int | None = None,
                              result: list[Listing] | None = None) -> None:
    if not listings:
        return

    if not result:
        result = []

    listings_attempts_limit = 2
    listings_counter = 0
    listings_queue = deque((listing, 0) for listing in listings)
    while listings_queue:
        listing, attempts = listings_queue.popleft()

        if not listing.price:
            continue

        # Check and remove listing
        # if it should be removed - remove listing
        # otherwise continue and don't post it second time
        published_listing_element = (
                scraper.find_element(selector=XPATH.selling_listing_container(listing.title),
                                     by=By.XPATH,
                                     exit_on_missing_element=False)
                or find_listing_by_title(scraper=scraper,
                                         title=listing.title)
        )

        if published_listing_element:
            published_listing = get_published_listing(scraper=scraper,
                                                      published_listing_element=published_listing_element,
                                                      extended_info=True)

            if (listing.price != published_listing.price
                    or listing.mileage != published_listing.mileage
                    or listing.fuel_type != published_listing.fuel_type
                    or not compare_text(listing.description, published_listing.description)):
                remove_published_listing(scraper=scraper,
                                         published_listing=published_listing)
            else:
                continue

        # Publishing listing
        is_published = publish_listing(data=listing, scraper=scraper)
        if is_published:
            listings_counter += 1
            result.append(listing)
            post_listing_to_groups(listing=listing, scraper=scraper)
        else:
            if attempts < listings_attempts_limit:
                listings_queue.appendleft((listing, attempts + 1))

        # Make pause
        if listings_queue or (listings_limit and listings_counter < listings_limit):
            scraper.wait_listing_random_time()


def check_and_remove_listings(scraper: Scraper,
                              listings: list[Listing],
                              published_listings: list[PublishedListing] | None = None) -> None:
    if published_listings is None:
        published_listing_elements = find_all_published_listing_elements(scraper=scraper)
        published_listings = get_all_published_listings(scraper=scraper,
                                                        published_listing_elements=published_listing_elements)

    for published_listing in published_listings:
        if (not published_listing.title or
                not published_listing.published_date):
            continue

        # Check conditions when listing should be removed

        # Try to find listing in database, if not present the listing should be removed
        # because it is not actual anymore
        is_not_present = not any(compare_title(published_listing.title, l.title) for l in listings)

        # Published date condition
        is_expired = (
                published_listing.published_date is not None
                and (datetime.today().date() - published_listing.published_date).days >= CONFIG['listing']['lifetime']
        )

        # Remove the listing if it needed
        if is_not_present or is_expired:
            remove_published_listing(scraper=scraper, published_listing=published_listing)


def find_all_published_listing_elements(scraper: Scraper) -> list[WebElement]:
    # Check the page and if it wrong page try go to correct page
    container_element_selector = "//div[translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'collection of your marketplace items']"
    container_element = scraper.find_element(selector=container_element_selector,
                                             by=By.XPATH,
                                             exit_on_missing_element=False)
    if not container_element:
        scraper.go_to_page(PAGES['selling'])

    # Find and get all published listings
    element_selector = f"{container_element_selector}/div/div/div[2]/div[1]/div/div[2]/div/div/span/div/div/div"
    elements = scraper.find_elements_with_scrolling(by=By.XPATH, selector=element_selector)
    return elements


def get_all_published_listings(scraper: Scraper,
                               published_listing_elements: list[WebElement]) -> list[PublishedListing]:
    result = []

    for element in published_listing_elements:
        listing = get_published_listing(scraper=scraper, published_listing_element=element)
        result.append(listing)

    return result


def get_published_listing(
        scraper: Scraper,
        published_listing_element: WebElement,
        extended_info: bool = False
) -> PublishedListing:
    published_listening_title_element_selector = \
        './/div/div/div/div[2]/div/div[1]/div/div[2]/div/div[1]/span/span/span'
    published_listening_price_element_selector = \
        './/div/div/div/div[2]/div/div[1]/div/div[2]/div/div[2]/span'
    published_listening_old_price_element_selector = \
        f'.{published_listening_price_element_selector}/span/span'
    published_listening_published_date_element_selector = \
        './/div/div/div/div[2]/div/div[1]/div/div[3]/div[1]//span/span/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "listed")]'

    element = published_listing_element

    # title
    title = ''
    title_element = element.find_elements(
        by=By.XPATH,
        value=published_listening_title_element_selector
    )
    if title_element:
        title = title_element[0].text

    # price
    price = 0.0
    price_element = element.find_elements(
        by=By.XPATH,
        value=published_listening_price_element_selector
    )
    if price_element:
        price_element = price_element[0]
        price_text = price_element.text
        old_price_element = element.find_elements(
            by=By.XPATH,
            value=published_listening_old_price_element_selector)
        old_price_element = old_price_element[0] if old_price_element else None
        if old_price_element:
            price_text = price_text.replace(old_price_element.text, '')
        if price_text:
            price = float(re.sub(r"\D", "", price_text))

    # published date
    published_date = None
    published_date_element = element.find_elements(
        by=By.XPATH,
        value=published_listening_published_date_element_selector
    )
    if published_date_element:
        published_date_element = published_date_element[0]
        published_date_text = published_date_element.text.lower()
        published_date_text = published_date_text.split('listed', 1)[1]
        match = re.search(r"\d{1,2}/\d{1,2}", published_date_text)
        if match:
            published_date_text = match.group()
            try:
                date = datetime.strptime(published_date_text, "%m/%d").date()
                published_date = date.replace(year=datetime.now().year)
            except ValueError:
                pass

    #
    listing = PublishedListing()
    listing.title = title
    listing.price = price
    listing.published_date = published_date

    if extended_info:
        if click_listing_by_title(scraper=scraper, title=title):
            listing_link_element_selector = f'.//a[contains(@href, "marketplace/item") and .//span[translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz") = "{title.lower()}"]]'
            listing_link_element = scraper.find_element(
                selector=listing_link_element_selector,
                by=By.XPATH,
                exit_on_missing_element=False
            )
            if listing_link_element:
                scraper.element_click(selector=listing_link_element_selector, by=By.XPATH)

                xpath_element_with_photos = './/div[@aria-label="Marketplace Listing Viewer"]/div[2]/div/div/div[2]/div/div[1]'
                xpath_element_with_info = './/div[@aria-label="Marketplace Listing Viewer"]/div[2]/div/div/div[2]/div/div[2]'
                xpath_element_price = '//span[contains(text(), "CA$")]'
                xpath_element_description_see_more = '//span[text()="See more"]'
                xpath_element_description_see_less = '//span[text()="See less"]'
                xpath_element_description = f'//span[.{xpath_element_description_see_less} or .{xpath_element_description_see_more}]'
                xpath_mileage_element = '//div/div[2]/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "driven")]'
                xpath_fuel_type_element = '//div/div[2]/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "fuel type")]'

                # Get price
                price_element = scraper.find_element(
                    selector=f'{xpath_element_with_info}{xpath_element_price}',
                    by=By.XPATH,
                    exit_on_missing_element=False
                )
                if price_element:
                    price = float(re.sub(r"\D", "", price_element.text))
                    listing.price = price

                # Get description
                description_see_more_element = scraper.find_element(
                    selector=f'{xpath_element_with_info}{xpath_element_description_see_more}',
                    by=By.XPATH,
                    exit_on_missing_element=False
                )
                if description_see_more_element:
                    description_see_more_element.click()
                    description_element = scraper.find_element(
                        selector=f'{xpath_element_with_info}{xpath_element_description}',
                        by=By.XPATH,
                        exit_on_missing_element=False
                    )
                    if description_element:
                        description_text = description_element.text
                        description_element_child = description_element.find_element(By.XPATH, './*')
                        if description_element_child:
                            description_text = description_text.replace(description_element_child.text, '')
                        listing.description = description_text

                # Get mileage
                mileage_element = scraper.find_element(
                    selector=f'{xpath_element_with_info}{xpath_mileage_element}',
                    by=By.XPATH,
                    exit_on_missing_element=False
                )
                if mileage_element:
                    mileage = int(re.sub(r"\D", "", mileage_element.text))
                    listing.mileage = mileage

                # Get fuel type
                fuel_type_element = scraper.find_element(
                    selector=f'{xpath_element_with_info}{xpath_fuel_type_element}',
                    by=By.XPATH,
                    exit_on_missing_element=False
                )
                if fuel_type_element:
                    fuel_type = fuel_type_element.text.lower().replace("fuel type:", "").strip()
                    listing.fuel_type = FuelType.from_str(fuel_type)

                # Close listing detailed control panel
                close_button_selector = (
                    f'//*[{XPATH.translate_eq_expr("close", "@aria-label")} '
                    f'and {XPATH.translate_eq_expr("false", "@aria-hidden")} '
                    f'and {XPATH.translate_eq_expr("button", "@role")}]'
                )
                close_button = scraper.find_element_and_click(
                    selector=close_button_selector,
                    by=By.XPATH,
                    exit_on_missing_element=False,
                    use_cursor=True
                )
                if not close_button:
                    scraper.send_key(Keys.ESCAPE)

            # Close listing control window
            close_button_selector = (
                f'//*[{XPATH.translate_eq_expr("close", "@aria-label")} '
                f'and {XPATH.translate_eq_expr("0", "@tabindex")} '
                f'and {XPATH.translate_eq_expr("button", "@role")}]'
            )
            close_button = scraper.find_element_and_click(
                selector=close_button_selector,
                by=By.XPATH,
                exit_on_missing_element=False,
                use_cursor=True
            )
            if not close_button:
                scraper.send_key(Keys.ESCAPE)

    return listing


def remove_published_listing(scraper: Scraper, published_listing: PublishedListing) -> None:
    if not click_listing_by_title(scraper=scraper, title=published_listing.title):
        return

    # Click on the delete listing button
    delete_element_selector = (
        f"//div[not(@role='gridcell')]"
        f"/div[{XPATH.translate_eq_expr('delete', '@aria-label')} and @tabindex='0']"
    )
    delete_element = scraper.find_element_and_click(
        selector=delete_element_selector,
        by=By.XPATH,
        exit_on_missing_element=False
    )
    if not delete_element:
        scraper.send_key(Keys.ESCAPE)
        return

    # Click on confirm button to delete
    confirm_delete_element_selector = (
        f'//div[{XPATH.translate_eq_expr("delete listing", "@aria-label")}]'
        f'//div[{XPATH.translate_eq_expr("delete", "@aria-label")} and @tabindex="0"]'
    )
    confirm_delete_element = scraper.find_element_and_click(
        selector=confirm_delete_element_selector,
        by=By.XPATH,
        exit_on_missing_element=False
    )
    if not confirm_delete_element:
        confirm_delete_element_selector = (
            f'//div[{XPATH.translate_eq_expr("dialog", "@aria-label")}]'
            f'//div[{XPATH.translate_eq_expr("delete", "@aria-label")} and @tabindex="0"] and @role="button" and not(.//i)'
        )
        confirm_delete_element = scraper.find_element_and_click(
            selector=confirm_delete_element_selector,
            by=By.XPATH,
            exit_on_missing_element=False
        )

    if not confirm_delete_element:
        scraper.send_key(Keys.ESCAPE)
        scraper.wait_action_random_time()
        scraper.send_key(Keys.ESCAPE)
        return

    # Wait until the popup is closed
    scraper.element_wait_to_be_invisible('div[aria-label="Your Listing"]')


def publish_listing(data: Listing, scraper: Scraper):
    # Find and click listing create button
    create_listing_button_selector = 'div[aria-label="Marketplace sidebar"] a[aria-label="Create new listing"]'
    create_listing_button = scraper.find_element(selector=create_listing_button_selector,
                                                 exit_on_missing_element=False,
                                                 wait_element_time=20)
    if create_listing_button:
        scraper.element_click(selector=create_listing_button_selector, exit_on_missing_element=False, use_cursor=True)
    else:
        scraper.go_to_page(PAGES['create_new_listing'])

    # Choose listing type
    listing_type_button_selector = '//span[translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz") = "vehicle for sale"]'
    listing_type_button = scraper.find_element(selector=listing_type_button_selector,
                                               by=By.XPATH,
                                               exit_on_missing_element=False)
    if not listing_type_button:
        scraper.element_click(selector=listing_type_button_selector, by=By.XPATH, use_cursor=True)
    else:
        scraper.go_to_page(PAGES['create_new_listing_vehicle'])

    # Create string that contains all the image paths separated by \n
    images_path = generate_multiple_images_path(data.photos_folder, data.photos_names)
    # Add images to the listing
    scraper.input_file_add_files('input[accept="image/*,image/heif,image/heic"]', images_path)

    if data.vehicle_type:
        element_selector = '//span[text()="Vehicle type"]'
        element = scraper.find_element(selector=element_selector, by=By.XPATH, exit_on_missing_element=False)
        if element:
            scraper.scroll_to_element(selector=element_selector, by=By.XPATH, exit_on_missing_element=False)
            scraper.element_click(selector='//span[text()="Vehicle type"]', by=By.XPATH, exit_on_missing_element=False,
                                  use_cursor=True)
            scraper.element_click(selector=f'//span[text()="{str(data.vehicle_type)}"]', by=By.XPATH,
                                  exit_on_missing_element=False, use_cursor=True)

    if data.year:
        scraper.scroll_to_element_by_xpath('//span[text()="Year"]')
        scraper.element_click(selector='//span[text()="Year"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//span[text()="{str(data.year)}"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)

    if data.make:
        scraper.scroll_to_element_by_xpath('//span[text()="Make"]')
        scraper.element_click(selector='//span[text()="Make"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(
            selector=f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{data.make.lower()}')]",
            by=By.XPATH, exit_on_missing_element=False, use_cursor=True)

    if data.model:
        scraper.scroll_to_element_by_xpath('//span[text()="Model"]/following-sibling::input[1]')
        scraper.element_send_keys(selector='//span[text()="Model"]/following-sibling::input[1]',
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  text=data.model)

    if data.mileage:
        scraper.scroll_to_element_by_xpath('//span[text()="Mileage"]/following-sibling::input[1]')
        scraper.element_send_keys(selector='//span[text()="Mileage"]/following-sibling::input[1]',
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  text=str(data.mileage))

    if data.body_type:
        scraper.scroll_to_element_by_xpath('//span[text()="Body style"]')
        scraper.element_click(selector='//span[text()="Body style"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//span[text()="{str(data.body_type)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.exterior_color:
        scraper.scroll_to_element_by_xpath('//span[text()="Exterior color"]')
        scraper.element_click(selector='//span[text()="Exterior color"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//div/div/div/div/span[text()="{str(data.exterior_color)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.interior_color:
        scraper.scroll_to_element_by_xpath('//span[text()="Interior color"]')
        scraper.element_click(selector='//span[text()="Interior color"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//div/div/div/div/span[text()="{str(data.interior_color)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.vehicle_condition:
        scraper.scroll_to_element_by_xpath('//span[text()="Vehicle condition"]')
        scraper.element_click(selector='//span[text()="Vehicle condition"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//span[text()="{str(data.vehicle_condition)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.fuel_type:
        scraper.scroll_to_element_by_xpath('//span[text()="Fuel type"]')
        scraper.element_click(selector='//span[text()="Fuel type"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//div/div/div/div/div/span[text()="{str(data.fuel_type)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.transmission:
        scraper.scroll_to_element_by_xpath('//span[text()="Transmission"]')
        scraper.element_click(selector='//span[text()="Transmission"]', by=By.XPATH, exit_on_missing_element=False,
                              use_cursor=True)
        scraper.element_click(selector=f'//span[text()="{str(data.transmission)}"]', by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)

    if data.price:
        scraper.scroll_to_element_by_xpath('//span[text()="Price"]/following-sibling::input[1]')
        scraper.element_send_keys(selector='//span[text()="Price"]/following-sibling::input[1]',
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  text=str(int(data.price)))

    if data.description:
        description = data.description
        old_value = CONFIG['listing']['description']['replace']['old_value'] or ''
        new_value = CONFIG['listing']['description']['replace']['new_value'] or ''
        if old_value:
            description = description.replace(old_value, new_value)
        elif new_value:
            description = f"{description}{new_value}"

        scraper.scroll_to_element_by_xpath(xpath='//span[text()="Description"]/following-sibling::div/textarea')
        scraper.element_send_keys(selector='//span[text()="Description"]/following-sibling::div/textarea',
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  text=description)

    if data.location:
        scraper.scroll_to_element_by_xpath('//span[text()="Location"]/following-sibling::input[1]')
        scraper.element_send_keys(selector='//span[text()="Location"]/following-sibling::input[1]',
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  text=data.location)
        scraper.element_click('ul[role="listbox"] li:first-child > div', exit_on_missing_element=False,
                              use_cursor=False)

    next_button_selector = 'div [aria-label="Next"] > div'
    next_button = scraper.find_element(selector=next_button_selector,
                                       exit_on_missing_element=False,
                                       wait_element_time=3)
    if next_button:
        scraper.element_click(selector=next_button_selector,
                              by=By.CSS_SELECTOR,
                              exit_on_missing_element=False,
                              use_cursor=True)
        add_listing_to_multiple_groups(data, scraper)

    close_button_selector = '//span[text()="Close"]'
    close_button = scraper.find_element(selector=close_button_selector,
                                        by=By.XPATH,
                                        exit_on_missing_element=False,
                                        wait_element_time=10)
    if close_button:
        scraper.element_click(selector=close_button_selector,
                              by=By.XPATH,
                              exit_on_missing_element=False,
                              use_cursor=True)
        scraper.go_to_page(PAGES['selling'])
        return False

    # Publish the listing
    publish_button_selector = 'div[aria-label="Publish"]:not([aria-disabled])'
    publish_button = scraper.find_element(selector=publish_button_selector,
                                          by=By.CSS_SELECTOR,
                                          exit_on_missing_element=False,
                                          wait_element_time=10)
    if not publish_button:
        system_logger.error(f'Cant find element {publish_button_selector}')
        return False

    scraper.element_click(selector=publish_button_selector,
                          by=By.CSS_SELECTOR,
                          exit_on_missing_element=False,
                          use_cursor=True)
    scraper.go_to_page(PAGES['selling'])
    return True


def generate_multiple_images_path(path, images):
    # Last character must be '/' because after that we are adding the name of the image
    if path[-1] != '/':
        path += '/'

    images_path = ''

    # Split image names into array by this symbol ";"
    image_names = images

    # Create string that contains all the image paths separeted by \n
    if image_names:
        for image_name in image_names:
            # Remove whitespace before and after the string
            image_name = image_name.strip()

            # Add "\n" for indicating new file
            if images_path != '':
                images_path += '\n'

            images_path += path + image_name

    return images_path


def add_listing_to_multiple_groups(data: Listing, scraper: Scraper) -> None:
    # Create an array for group names by splitting the string by this symbol ";"
    group_names = define_groups_for_posting(data)
    if not group_names:
        return

    # Post in different groups
    for group_name in group_names:
        if not group_name:
            continue
        group_element_selector = f'//span[{XPATH.translate_cont_expr(group_name, "text()")}]'
        group_element = scraper.find_element(selector=group_element_selector,
                                             by=By.XPATH,
                                             exit_on_missing_element=False)
        if group_element:
            scraper.element_click(selector=group_element_selector,
                                  by=By.XPATH,
                                  exit_on_missing_element=False,
                                  use_cursor=True)


def post_listing_to_groups(listing: Listing, scraper: Scraper) -> None:
    # Create an array for group names by splitting the string by this symbol ";"
    group_names = define_groups_for_posting(listing)
    if not group_names:
        return

    # Wait before starting sharing to groups
    scraper.wait_random_time(30, 60)

    system_logger.info(f'Listing: {listing.title}({listing.vin}) '
                       f'Start posting listing to groups.')

    if not click_listing_by_title(scraper=scraper, title=listing.title):
        return

    # Post in different groups
    for group_name in group_names:
        post_listing_to_group(listing, scraper, group_name)


def post_listing_to_group(listing: Listing, scraper: Scraper, group_name: str) -> bool:
    system_logger.info(f'Listing: {listing.title}({listing.vin}) '
                       f'Start posting listing to group - "{group_name}".')

    # Click on the Share button to the listing that we want to share
    share_button_selector = (f'//*[{XPATH.translate_cont_expr(listing.title, "@aria-label")}]'
                             f'//span[{XPATH.translate_cont_expr("share", ".")}]')
    share_button = scraper.find_element_and_click(selector=share_button_selector,
                                                  by=By.XPATH,
                                                  exit_on_missing_element=False)
    if not share_button:
        return False

    # Click on the Share to a group button
    share_group_button_selector = f'//div[@role="button" and .//span[{XPATH.translate_eq_expr("group", "text()")}]]'
    share_group_button = scraper.find_element_and_click(selector=share_group_button_selector,
                                                        by=By.XPATH,
                                                        exit_on_missing_element=False)
    if not share_group_button:
        return False

    # Remove current text from this input
    search_input_selector = f'//*[{XPATH.translate_eq_expr("search for groups", "@aria-label")}]'
    scraper.element_delete_text(selector=search_input_selector,
                                by=By.XPATH,
                                exit_on_missing_element=False)

    # Enter the title of the group in the input for search
    scraper.element_send_keys(selector=search_input_selector,
                              by=By.XPATH,
                              text=group_name[:51])

    # Try to find group element for posting
    group_element_selector = f'//span[{XPATH.translate_cont_expr(group_name, "text()")}]'
    group_element = scraper.find_element_and_click(selector=group_element_selector,
                                                   by=By.XPATH,
                                                   exit_on_missing_element=False)
    if not group_element:
        return False

    # Enter text for posting
    post_text_field_element_selector = f'//*[{XPATH.translate_cont_expr("create a public post", "@aria-placeholder")}]'
    post_text_field_element = scraper.find_element(selector=post_text_field_element_selector,
                                                   by=By.XPATH,
                                                   exit_on_missing_element=False)
    if not post_text_field_element:
        post_text_field_element_selector = f'//*[{XPATH.translate_cont_expr("write something", "@aria-label")}]'
        post_text_field_element = scraper.find_element(selector=post_text_field_element_selector,
                                                       by=By.XPATH,
                                                       exit_on_missing_element=False)

    if post_text_field_element:
        scraper.element_send_keys(selector=post_text_field_element_selector,
                                  by=By.XPATH,
                                  text=listing.description)

    # Try to post listing in group
    post_button_selector = f'//*[{XPATH.translate_eq_expr("post", "@aria-label")} and not (@aria-disabled)]'
    post_button = scraper.find_element_and_click(selector=post_button_selector,
                                                 by=By.XPATH,
                                                 exit_on_missing_element=False)
    if not post_button:
        return False

    # Wait till the post is posted successfully
    scraper.element_wait_to_be_invisible(selector=f'//*[{XPATH.translate_cont_expr("dialog", "@role")}]',
                                         by=By.XPATH)
    scraper.element_wait_to_be_invisible(selector=f'//*[{XPATH.translate_cont_expr("posting", "@aria-label")}]',
                                         by=By.XPATH)

    success_result_element_text1 = 'shared to your group.'
    success_result_element_text2 = "thanks for your post! it's been submitted to group admins for approval."
    success_result_element_selector = (
        f'//span[{XPATH.translate_eq_expr(success_result_element_text1, "text()")} or '
        f'{XPATH.translate_eq_expr(success_result_element_text2, "text()")}]')
    success_result_element = scraper.find_element(selector=success_result_element_selector, by=By.XPATH,
                                                  condition=EC.visibility_of_element_located,
                                                  exit_on_missing_element=False, wait_element_time=1)
    if success_result_element:
        if success_result_element_text1 in success_result_element.text.lower():
            system_logger.info(f'Listing: {listing.title}({listing.vin}) '
                               f'Successfully shared to group {group_name}')
        elif success_result_element_text2 in success_result_element.text.lower():
            system_logger.info(f'Listing: {listing.title}({listing.vin}) '
                               f'Successfully submitted to group({group_name}) admins for approval')
        else:
            system_logger.info(f'Listing: {listing.title}({listing.vin}) '
                               f'Successfully shared to group {group_name} or submitted to group({group_name}) admins for approval')
        return True

    return False


def define_groups_for_posting(listing: Listing) -> list[str]:
    # Define groups for posting from listing
    # These groups may be unique for each listing
    group_names = listing.groups.copy()

    # Define groups for posting from settings
    # These groups are the same for all listings
    group_names_from_config = CONFIG['listing']['public_groups']
    if group_names_from_config:
        group_names_from_config = [g.strip() for g in group_names_from_config.split(';')]
        group_names.extend(group_names_from_config)

    return group_names


def click_listing_by_title(scraper: Scraper, title: str) -> bool:
    # Try to find listing container on page
    listing_container_selector = XPATH.selling_listing_container(title)
    listing_container = scraper.find_element(
        selector=listing_container_selector,
        by=By.XPATH,
        exit_on_missing_element=False
    )
    if not listing_container:
        listing_container = find_listing_by_title(scraper=scraper, title=title)

    if not listing_container:
        return False

    scraper.scroll_to_element(
        selector=listing_container,
        by=By.XPATH,
        exit_on_missing_element=False
    )

    listing_clickable_element_selector = XPATH.selling_listing_container_clickable_element(title)
    listing_clickable_element = scraper.find_element_and_click(
        listing_clickable_element_selector,
        by=By.XPATH,
        exit_on_missing_element=False,
        scroll_to=False
    )
    if listing_clickable_element:
        return True
    else:
        return scraper.element_click(listing_container)


def find_listing_by_title(scraper: Scraper, title: str) -> WebElement | None:
    # Find and check search input field
    search_input_selector = XPATH.selling_search_input()
    search_input = scraper.find_element(selector=search_input_selector,
                                        by=By.XPATH,
                                        exit_on_missing_element=False)
    if not search_input:
        system_logger.error(f'Cant find element {search_input_selector}')
        return None

    # Clear input field for searching listings before entering title
    scraper.element_delete_text(selector=search_input_selector,
                                by=By.XPATH,
                                exit_on_missing_element=False)

    # Enter the title of the listing in the input for search
    scraper.element_send_keys(selector=search_input_selector,
                              by=By.XPATH,
                              text=title,
                              exit_on_missing_element=False)

    return scraper.find_element(
        selector=XPATH.selling_listing_container(title),
        by=By.XPATH,
        exit_on_missing_element=False,
        wait_element_time=10)


def normalize_text_for_compare(text: str) -> str:
    if text is None:
        return ''
    text = unicodedata.normalize("NFKD", text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def normalize_title_for_compare(text: str) -> str:
    text = normalize_text_for_compare(text)
    text = text.replace(' ', '')
    return text


def compare_text(text1: str, text2: str) -> bool:
    return normalize_text_for_compare(text1) == normalize_text_for_compare(text2)


def compare_title(text1: str, text2: str) -> bool:
    return normalize_title_for_compare(text1) == normalize_title_for_compare(text2)
