# Remove and then publish each listing
from selenium.webdriver.common.by import By

from helpers.csv_helper import Row
from helpers.scraper import Scraper


def update_listings(listings: list[Row], scraper: Scraper):
    if not listings:
        return

    # Check if listing is already listed and remove it then publish it like a new one
    for listing in listings:
        # Remove listing if it is already published
        remove_listing(listing, type, scraper)

        # Publish the listing in marketplace
        is_published = publish_listing(listing, type, scraper)

        # If the listing is not published from the first time, try again
        if not is_published:
            publish_listing(listing, type, scraper)


def remove_listing(data: Row, scraper: Scraper):
    listing_type = 'vehicle'

    title = data.title
    listing_title = find_listing_by_title(title, scraper)

    # Listing not found so stop the function
    if not listing_title:
        return

    listing_title.click()

    # Click on the delete listing button
    scraper.element_click('div:not([role="gridcell"]) > div[aria-label="Delete"][tabindex="0"]')

    # Click on confirm button to delete
    confirm_delete_selector = 'div[aria-label="Delete listing"] div[aria-label="Delete"][tabindex="0"]'
    if scraper.find_element(selector=confirm_delete_selector,
                            exit_on_missing_element=False,
                            wait_element_time=3):
        scraper.element_click(confirm_delete_selector)
    else:
        confirm_delete_selector = 'div[aria-label="Delete Listing"] div[aria-label="Delete"][tabindex="0"]'
        if scraper.find_element(selector=confirm_delete_selector,
                                exit_on_missing_element=True,
                                wait_element_time=3):
            scraper.element_click(confirm_delete_selector)

    # Wait until the popup is closed
    scraper.element_wait_to_be_invisible('div[aria-label="Your Listing"]')


def publish_listing(data: Row, listing_type, scraper):
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
    # scraper.element_click('a[href="/marketplace/create/' + listing_type + '/"]')

    # Create string that contains all of the image paths separeted by \n
    images_path = generate_multiple_images_path(data.photos_folder, data.photos_names)
    # Add images to the the listing
    scraper.input_file_add_files('input[accept="image/*,image/heif,image/heic"]', images_path)

    # Add specific fields based on the listing_type
    function_name = 'add_fields_for_' + listing_type
    # Call function by name dynamically
    globals()[function_name](data, scraper)

    if data.price:
        scraper.element_send_keys_by_xpath('//span[text()="Price"]/following-sibling::input[1]', data.price)

    if data.description:
        scraper.element_send_keys_by_xpath('//span[text()="Description"]/following-sibling::div/textarea',
                                           data.description)

    if data.location:
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
    close_button = scraper.find_element_by_xpath(close_button_selector, False, 10)
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

    # Create string that contains all of the image paths separeted by \n
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
def add_fields_for_vehicle(data: Row, scraper):
    # Expand vehicle type select
    if data.vehicle_type:
        scraper.element_click_by_xpath('//span[text()="Vehicle type"]')
        scraper.element_click_by_xpath('//span[text()="' + data.vehicle_type + '"]')

    # Scroll to years select
    if data.year:
        scraper.scroll_to_element_by_xpath('//span[text()="Year"]')
        scraper.element_click_by_xpath('//span[text()="Year"]')
        scraper.element_click_by_xpath('//span[text()="' + str(data.year) + '"]')

    # Scroll to make select
    if data.make:
        scraper.scroll_to_element_by_xpath('//span[text()="Make"]')
        scraper.element_click_by_xpath('//span[text()="Make"]')
        scraper.element_click_by_xpath('//span[text()="' + data.make + '"]')

    if data.model:
        scraper.element_send_keys_by_xpath('//span[text()="Model"]/following-sibling::input[1]', data.model)

    # Scroll to body type select
    if data.body_type:
        scraper.scroll_to_element_by_xpath('//span[text()="Body style"]')
        scraper.element_click_by_xpath('//span[text()="Body style"]')
        scraper.element_click_by_xpath('//span[text()="' + data.body_type + '"]')

    # Scroll to exterior color select
    if data.exterior_color:
        scraper.scroll_to_element_by_xpath('//span[text()="Exterior color"]')
        scraper.element_click_by_xpath('//span[text()="Exterior color"]')
        scraper.element_click_by_xpath('//span[text()="' + data.exterior_color + '"]')

    # Scroll to interior color select
    if data.interior_color:
        scraper.scroll_to_element_by_xpath('//span[text()="Interior color"]')
        scraper.element_click_by_xpath('//span[text()="Interior color"]')
        scraper.element_click_by_xpath('//span[text()="' + data.interior_color + '"]')

    # Scroll to mileage input
    if data.mileage:
        scraper.scroll_to_element_by_xpath('//span[text()="Mileage"]/following-sibling::input[1]')
        scraper.element_send_keys_by_xpath('//span[text()="Mileage"]/following-sibling::input[1]', data.mileage)

    # Vehicle condition
    if data.vehicle_condition:
        scraper.element_click_by_xpath('//span[text()="Vehicle condition"]')
        scraper.element_click_by_xpath('//span[text()="' + data.vehicle_condition + '"]')

    # Fuel Type
    if data.fuel_type:
        scraper.element_click_by_xpath('//span[text()="Fuel type"]')
        scraper.element_click_by_xpath('//span[text()="' + data.fuel_type + '"]')

    # Transmission
    if data.transmission:
        scraper.element_click_by_xpath('//span[text()="Transmission"]')
        scraper.element_click_by_xpath('//span[text()="' + data.transmission + '"]')


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


def add_listing_to_multiple_groups(data: Row, scraper):
    # Create an array for group names by spliting the string by this symbol ";"
    group_names = data.groups

    # If the groups are empty do not do nothing
    if not group_names:
        return

    # Post in different groups
    for group_name in group_names:
        # Remove whitespace before and after the name
        group_name = group_name.strip()

        scraper.element_click_by_xpath('//span[text()="' + group_name + '"]')


def post_listing_to_multiple_groups(data: Row, listing_type, scraper):
    title = generate_title_for_listing_type(data, listing_type)
    title_element = find_listing_by_title(title, scraper)

    # If there is no add with this title do not do nothing
    if not title_element:
        return

    # Create an array for group names by spliting the string by this symbol ";"
    group_names = data.groups

    # If the groups are empty do not do nothing
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


def find_listing_by_title(title: str, scraper: Scraper):
    # Find and check search input field
    search_input_selector = 'input[placeholder="Search your listings"]'
    search_input = scraper.find_element(selector=search_input_selector,
                                        exit_on_missing_element=False)
    if not search_input:
        return False

    # Clear input field for searching listings before entering title
    scraper.element_delete_text(search_input_selector)

    # Enter the title of the listing in the input for search
    scraper.element_send_keys(selector=search_input_selector,
                              text=title)

    return scraper.find_element_by_xpath(xpath=f'//span[text()="{title}"]',
                                         exit_on_missing_element=False,
                                         wait_element_time=10)


def wait_until_listing_is_published(listing_type, scraper):
    if listing_type == 'item':
        scraper.element_wait_to_be_invisible_by_xpath('//h1[text()="Item for sale"]')
    elif listing_type == 'vehicle':
        scraper.element_wait_to_be_invisible_by_xpath('//h1[text()="Vehicle for sale"]')
