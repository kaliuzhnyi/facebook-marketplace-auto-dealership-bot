# Remove and then publish each listing
import re
import unicodedata
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from config import CONFIG
from helpers.model import Listing, PublishedListing
from helpers.scraper import Scraper


def check_and_update_listings(scraper: Scraper, listings: list[Listing],
                              published_listings: list[WebElement] | None = None) -> None:
    if not listings:
        return

    # Check if listing is already listed and remove it then publish it like a new one
    for listing in listings:

        # Remove listing if it needed
        published_listing_element = find_published_listing_element(scraper=scraper, listing_title=listing.title)
        if published_listing_element:
            published_listing = get_published_listing(
                scraper=scraper,
                published_listing_element=published_listing_element,
                extended_info=True)

            if (listing.price != published_listing.price
                    or listing.mileage != published_listing.mileage
                    or not compare_text(listing.description, published_listing.description)):
                remove_published_listing(scraper=scraper, published_listing=published_listing)

        # Publish the listing in marketplace
        is_published = publish_listing(data=listing, scraper=scraper)

        # Make a random delay between publishing
        scraper.wait_listing_random_time()

        # If the listing is not published from the first time, try again
        if not is_published:
            publish_listing(data=listing, scraper=scraper)


def check_and_remove_listings(scraper: Scraper,
                              listings: list[Listing],
                              published_listings: list[PublishedListing] | None = None) -> None:
    if published_listings is None:
        published_listing_elements = find_all_published_listing_elements(scraper=scraper)
        published_listings = get_all_published_listings(scraper=scraper,
                                                        published_listing_elements=published_listing_elements)

    for published_listing in published_listings:
        # Check conditions when listing should be removed

        # Title condition
        title_missing = not any(published_listing.title.lower() == l.title.lower() for l in listings)

        # Published date condition
        is_expired = (
                published_listing.published_date is not None
                and (datetime.today().date() - published_listing.published_date).days >= CONFIG['listing']['lifetime']
        )

        # Remove the listing if it needed
        if title_missing or is_expired:
            remove_published_listing(scraper=scraper, published_listing=published_listing)


def find_all_published_listing_elements(scraper: Scraper) -> list[WebElement]:
    scraper.go_to_page('https://facebook.com/marketplace/you/selling')

    # Find and get all published listings
    element_selector = '//div[@aria-label="Collection of your marketplace items"]/div/div/div[2]/div[1]/div/div[2]/div/div/span/div/div/div'
    elements = scraper.find_elements_with_scrolling(
        by=By.XPATH,
        selector=element_selector
    )

    return elements


def get_all_published_listings(scraper: Scraper, published_listing_elements: list[WebElement]) -> list[
    PublishedListing]:
    result = []

    for element in published_listing_elements:
        listing = get_published_listing(scraper=scraper, published_listing_element=element)
        result.append(listing)

    return result


def find_published_listing_element(scraper: Scraper, listing_title: str) -> WebElement | None:
    return find_listing_by_title(
        scraper=scraper,
        title=listing_title)


def get_published_listing(scraper: Scraper,
                          published_listing_element: WebElement,
                          extended_info: bool = False) -> PublishedListing:
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
        value=published_listening_title_element_selector)
    if title_element:
        title = title_element[0].text

    # price
    price = 0.0
    price_element = element.find_elements(
        by=By.XPATH,
        value=published_listening_price_element_selector)
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
        value=published_listening_published_date_element_selector)
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
        listing_element = find_listing_by_title(scraper=scraper, title=title)
        if listing_element:
            listing_element.click()
            listing_link_element = scraper.find_element_by_xpath(
                xpath=f'.//a[contains(@href, "marketplace/item") and .//span[translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz") = "{title.lower()}"]]',
                exit_on_missing_element=False
            )
            if listing_link_element:
                listing_link_element.click()

                xpath_element_with_photos = './/div[@aria-label="Marketplace Listing Viewer"]/div[2]/div/div/div[2]/div/div[1]'
                xpath_element_with_info = './/div[@aria-label="Marketplace Listing Viewer"]/div[2]/div/div/div[2]/div/div[2]'
                xpath_element_price = '//span[contains(text(), "CA$")]'
                xpath_element_description_see_more = '//span[text()="See more"]'
                xpath_element_description_see_less = '//span[text()="See less"]'
                xpath_element_description = f'//span[.{xpath_element_description_see_less} or .{xpath_element_description_see_more}]'
                xpath_mileage_element = '//div/div[2]/span[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "driven")]'

                # Get price
                price_element = scraper.find_element_by_xpath(
                    xpath=f'{xpath_element_with_info}{xpath_element_price}',
                    exit_on_missing_element=False
                )
                if price_element:
                    price = float(re.sub(r"\D", "", price_element.text))
                    listing.price = price

                # Get description
                description_see_more_element = scraper.find_element_by_xpath(
                    xpath=f'{xpath_element_with_info}{xpath_element_description_see_more}',
                    exit_on_missing_element=False
                )
                if description_see_more_element:
                    description_see_more_element.click()
                    description_element = scraper.find_element_by_xpath(
                        xpath=f'{xpath_element_with_info}{xpath_element_description}',
                        exit_on_missing_element=False
                    )
                    if description_element:
                        description_text = description_element.text
                        description_element_child = description_element.find_element(By.XPATH, './*')
                        if description_element_child:
                            description_text = description_text.replace(description_element_child.text, '')
                        listing.description = description_text

                # Get mileage
                mileage_element = scraper.find_element_by_xpath(
                    xpath=f'{xpath_element_with_info}{xpath_mileage_element}',
                    exit_on_missing_element=False
                )
                if mileage_element:
                    mileage = int(re.sub(r"\D", "", mileage_element.text))
                    listing.mileage = mileage

    return listing


def remove_published_listing(scraper: Scraper, published_listing: PublishedListing) -> None:
    listing_title = find_listing_by_title(
        scraper=scraper,
        title=published_listing.title)
    if not listing_title:
        return

    # Click on listing to open listing card
    listing_title.click()

    # Click on the delete listing button
    delete_element_selector = "//div[not(@role='gridcell')]/div[translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'delete' and @tabindex='0']"
    delete_element = scraper.find_element(
        selector=delete_element_selector,
        by=By.XPATH,
        wait_element_time=3
    )
    if not delete_element:
        return

    scraper.wait_action_random_time()
    delete_element.click()

    # Click on confirm button to delete
    confirm_delete_element_selector = "//div[translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'delete listing']//div[translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = 'delete' and @tabindex='0']"
    confirm_delete_element = scraper.find_element(
        selector=confirm_delete_element_selector,
        by=By.XPATH,
        wait_element_time=3
    )
    if not confirm_delete_element:
        return

    scraper.wait_action_random_time()
    confirm_delete_element.click()

    # Wait until the popup is closed
    scraper.element_wait_to_be_invisible('div[aria-label="Your Listing"]')


def publish_listing(data: Listing, scraper: Scraper):
    listing_type = 'vehicle'
    create_listing_button_selector = 'div[aria-label="Marketplace sidebar"] a[aria-label="Create new listing"]'
    create_listing_button = scraper.find_element(selector=create_listing_button_selector,
                                                 exit_on_missing_element=False,
                                                 wait_element_time=20)

    if create_listing_button:
        # Click on create new listing button
        scraper.element_click(create_listing_button_selector)
    else:
        # Refresh marketplace selling page
        scraper.go_to_page('https://facebook.com/marketplace/you/selling')
        scraper.element_click(create_listing_button_selector)

    # Choose listing type
    scraper.element_click('//span[text()="Vehicle for sale"]', by=By.XPATH)

    # Create string that contains all the image paths separated by \n
    images_path = generate_multiple_images_path(data.photos_folder, data.photos_names)
    # Add images to the listing
    scraper.input_file_add_files('input[accept="image/*,image/heif,image/heic"]', images_path)

    # Add specific fields based on the listing_type
    function_name = 'add_fields_for_' + listing_type
    # Call function by name dynamically
    globals()[function_name](data, scraper)

    if data.price:
        scraper.scroll_to_element_by_xpath('//span[text()="Price"]/following-sibling::input[1]')
        scraper.element_send_keys_by_xpath('//span[text()="Price"]/following-sibling::input[1]', int(data.price))

    if data.description:
        scraper.scroll_to_element_by_xpath('//span[text()="Description"]/following-sibling::div/textarea')
        scraper.element_send_keys_by_xpath('//span[text()="Description"]/following-sibling::div/textarea',
                                           data.description)

    if data.location:
        scraper.scroll_to_element_by_xpath('//span[text()="Location"]/following-sibling::input[1]')
        scraper.element_send_keys_by_xpath('//span[text()="Location"]/following-sibling::input[1]', data.location)
        scraper.element_click('ul[role="listbox"] li:first-child > div')

    next_button_selector = 'div [aria-label="Next"] > div'
    next_button = scraper.find_element(selector=next_button_selector,
                                       exit_on_missing_element=False,
                                       wait_element_time=3)
    if next_button:
        # Go to the next step
        scraper.element_click(next_button_selector)
        # Add listing to multiple groups
        add_listing_to_multiple_groups(data, scraper)

    close_button_selector = '//span[text()="Close"]'
    close_button = scraper.find_element_by_xpath(xpath=close_button_selector,
                                                 exit_on_missing_element=False,
                                                 wait_element_time=10)
    if close_button:
        scraper.element_click_by_xpath(close_button_selector)
        scraper.go_to_page('https://facebook.com/marketplace/you/selling')
        return False

    # Publish the listing
    scraper.element_click('div[aria-label="Publish"]:not([aria-disabled])')

    leave_page_selector = '//div[@tabindex="0"] //span[text()="Leave Page"]'
    leave_page = scraper.find_element_by_xpath(leave_page_selector, False, 15)
    if leave_page:
        scraper.element_click_by_xpath(leave_page_selector)

    # Wait until the listing is published
    wait_until_listing_is_published(listing_type, scraper)

    if not next_button:
        post_listing_to_multiple_groups(data, listing_type, scraper)

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


# Add specific fields for listing from type vehicle
def add_fields_for_vehicle(data: Listing, scraper):
    if data.vehicle_type:
        scraper.element_click_by_xpath('//span[text()="Vehicle type"]')
        scraper.element_click_by_xpath(f'//span[text()="{str(data.vehicle_type)}"]')

    if data.year:
        scraper.scroll_to_element_by_xpath('//span[text()="Year"]')
        scraper.element_click_by_xpath('//span[text()="Year"]')
        scraper.element_click_by_xpath(f'//span[text()="{str(data.year)}"]')

    if data.make:
        scraper.element_click_by_xpath('//span[text()="Make"]')
        scraper.element_click_by_xpath(
            f"//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{data.make.lower()}')]")

    if data.model:
        scraper.element_send_keys_by_xpath('//span[text()="Model"]/following-sibling::input[1]', data.model)

    if data.mileage:
        scraper.element_send_keys_by_xpath('//span[text()="Mileage"]/following-sibling::input[1]', data.mileage)

    if data.body_type:
        scraper.scroll_to_element_by_xpath('//span[text()="Body style"]')
        scraper.element_click_by_xpath('//span[text()="Body style"]')
        scraper.element_click_by_xpath(f'//span[text()="{str(data.body_type)}"]')

    if data.exterior_color:
        scraper.element_click_by_xpath('//span[text()="Exterior color"]')
        scraper.element_click_by_xpath(f'//div/div/div/div/span[text()="{str(data.exterior_color)}"]')

    if data.interior_color:
        scraper.element_click_by_xpath('//span[text()="Interior color"]')
        scraper.element_click_by_xpath(f'//div/div/div/div/span[text()="{str(data.interior_color)}"]')

    if data.vehicle_condition:
        scraper.element_click_by_xpath('//span[text()="Vehicle condition"]')
        scraper.element_click_by_xpath(f'//span[text()="{str(data.vehicle_condition)}"]')

    if data.fuel_type:
        scraper.element_click_by_xpath('//span[text()="Fuel type"]')
        scraper.element_click_by_xpath(f'//div/div/div/div/div/span[text()="{str(data.fuel_type)}"]')

    if data.transmission:
        scraper.element_click_by_xpath('//span[text()="Transmission"]')
        scraper.element_click_by_xpath(f'//span[text()="{str(data.transmission)}"]')


# Add specific fields for listing from type item
def add_fields_for_item(data, scraper):
    scraper.element_send_keys_by_xpath('//span[text()="Title"]/following-sibling::input[1]', data['Title'])

    # Scroll to "Category" select field
    scraper.scroll_to_element_by_xpath('//span[text()="Category"]')
    # Expand category select
    scraper.element_click_by_xpath('//span[text()="Category"]')
    # Select category
    scraper.element_click_by_xpath('//span[text()="' + data['Category'] + '"]')

    # Expand category select
    scraper.element_click_by_xpath('//div/span[text()="Condition"]')
    # Select category
    scraper.element_click_by_xpath('//span[@dir="auto"][text()="' + data['Condition'] + '"]')

    if data['Category'] == 'Sports & Outdoors':
        scraper.element_send_keys_by_xpath('//span[text()="Brand"]/following-sibling::input[1]', data['Brand'])


def generate_title_for_listing_type(data, listing_type):
    title = ''

    if listing_type == 'item':
        title = data['Title']

    if listing_type == 'vehicle':
        title = data.year + ' ' + data.make + ' ' + data.model

    return title


def add_listing_to_multiple_groups(data: Listing, scraper: Scraper):
    # Create an array for group names by splitting the string by this symbol ";"
    group_names = data.groups

    # If the groups are empty do not do anything
    if not group_names:
        return

    # Post in different groups
    for group_name in group_names:
        group_element_selector = f'//span[text()="{group_name.strip()}"]'
        group_element = scraper.find_element_by_xpath(xpath=group_element_selector,
                                                      exit_on_missing_element=False)
        if group_element:
            scraper.element_click_by_xpath(group_element_selector)


def post_listing_to_multiple_groups(data: Listing, listing_type, scraper):
    title = generate_title_for_listing_type(data, listing_type)
    title_element = find_listing_by_title(
        scraper=scraper,
        title=title)

    # If there is no add with this title do not do anything
    if not title_element:
        return

    # Create an array for group names by splitting the string by this symbol ";"
    group_names = data.groups

    # If the groups are empty do not do anything
    if not group_names:
        return

    search_input_selector = '[aria-label="Search for groups"]'

    # Post in different groups
    for group_name in group_names:
        # Click on the Share button to the listing that we want to share
        scraper.element_click_by_xpath('//*[contains(@aria-label, "' + title + '")]//span//span[contains(., "Share")]')

        # Click on the Share to a group button
        scraper.element_click_by_xpath('//span[text()="Group"]')

        # Remove whitespace before and after the name
        group_name = group_name.strip()

        # Remove current text from this input
        scraper.element_delete_text(search_input_selector)
        # Enter the title of the group in the input for search
        scraper.element_send_keys(search_input_selector, group_name[:51])

        scraper.element_click_by_xpath('//span[text()="' + group_name + '"]')

        if (scraper.find_element(selector='[aria-label="Create a public post…"]',
                                 exit_on_missing_element=False,
                                 wait_element_time=3)):
            scraper.element_send_keys('[aria-label="Create a public post…"]', data.description)
        elif (scraper.find_element(selector='[aria-label="Write something..."]',
                                   exit_on_missing_element=False,
                                   wait_element_time=3)):
            scraper.element_send_keys('[aria-label="Write something..."]', data.description)

        scraper.element_click('[aria-label="Post"]:not([aria-disabled])')
        # Wait till the post is posted successfully
        scraper.element_wait_to_be_invisible('[role="dialog"]')
        scraper.element_wait_to_be_invisible('[aria-label="Loading...]"')
        scraper.find_element_by_xpath('//span[text()="Shared to your group."]', False, 10)


def find_listing_by_title(scraper: Scraper, title: str) -> WebElement | None:
    # Find and check search input field
    search_input_selector = 'input[placeholder="Search your listings"]'
    search_input = scraper.find_element(selector=search_input_selector,
                                        exit_on_missing_element=False)
    if not search_input:
        return None

    # Clear input field for searching listings before entering title
    scraper.element_delete_text(search_input_selector)

    # Enter the title of the listing in the input for search
    scraper.element_send_keys(selector=search_input_selector,
                              text=title)

    return scraper.find_element_by_xpath(
        xpath=f'//span[translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz") = "{title.lower()}"]',
        exit_on_missing_element=False,
        wait_element_time=10)


def wait_until_listing_is_published(listing_type, scraper):
    if listing_type == 'item':
        scraper.element_wait_to_be_invisible_by_xpath('//h1[text()="Item for sale"]')
    elif listing_type == 'vehicle':
        scraper.element_wait_to_be_invisible_by_xpath('//h1[text()="Vehicle for sale"]')

def normalize_text_for_compare(text: str) -> str:
    if text is None:
        return ''
    text = unicodedata.normalize("NFKD", text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'[\n\r\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

def compare_text(text1: str, text2: str) -> bool:
    return normalize_text_for_compare(text1) == normalize_text_for_compare(text2)