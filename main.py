import os
import threading

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from config_loader import LOG_USER_FILE_PATH, LOG_SYSTEM_FILE_PATH, DATA_PATH
from helpers.csv_helper import get_data_from_csv
from helpers.listing_helper import update_listings
from helpers.scraper import Scraper

scraper: Scraper | None = None


def launch_browser_and_open_gui():
    global scraper

    launch_facebook_marketplace_bot()

    scraper = Scraper()
    scraper.create_tab('gui', True)
    scraper.go_to_page('http://localhost:8080')


def launch_facebook_marketplace_bot():
    current_log_file = LOG_USER_FILE_PATH

    def run_marketplace_bot():
        global scraper

        scraper.create_tab('facebook', True)
        scraper.go_to_page('https://facebook.com')
        scraper.add_login_functionality(login_url='https://facebook.com',
                                        after_login_url='https://facebook.com',
                                        is_logged_in_selector='svg[aria-label="Your profile"]',
                                        cookies_file_name='facebook')
        scraper.go_to_page('https://facebook.com/marketplace/you/selling')


        # # Import data from external resources to csv file
        # # import_data_to_csv(DATA_PATH)
        # # Get data for vehicle type listings from csvs/vehicles.csv
        vehicle_listings = get_data_from_csv(DATA_PATH)
        # Publish all of the vehicles into the facebook marketplace
        update_listings(vehicle_listings, 'vehicle', scraper)

    def on_start_button_click():
        threading.Thread(target=run_marketplace_bot).start()

    def on_clear_log_button_click():
        if os.path.exists(current_log_file):
            open(current_log_file, "w").close()

    def update_log_view():
        if os.path.exists(current_log_file):
            with open(current_log_file, 'r', encoding='utf-8') as f:
                log_area.value = f.read()

    def on_log_type_change(selected: ValueChangeEventArguments):
        nonlocal current_log_file

        log_file_map = {
            'User log': LOG_USER_FILE_PATH,
            'System log': LOG_SYSTEM_FILE_PATH,
        }

        current_log_file = log_file_map.get(selected.value, LOG_USER_FILE_PATH)

    ui.timer(0.5, update_log_view)

    with ui.column().classes('w-full items-center'):
        ui.markdown('# **Facebook Marketplace Auto Dealership Bot**')
        ui.markdown('Publish all your ads easy')

        with ui.row():
            ui.button(text="Start",
                      on_click=on_start_button_click)

        with ui.expansion('Log').classes('w-full'):
            with ui.row():
                ui.button(text="Clear Log",
                          on_click=on_clear_log_button_click)
                ui.select(
                    options=['User log', 'System log'],
                    value='User log',
                    on_change=on_log_type_change
                ).props('outlined dense')

            log_area = (ui.textarea(label='Log Output', value='')
                        .props('readonly')
                        .style('width: 100%; height: 300px;'))


# if __name__ in {"__main__", "__mp_main__"}:
if __name__ == "__main__":
    threading.Thread(target=launch_browser_and_open_gui).start()
    ui.run(title="Facebook Bot Control",
           port=8080,
           show=False,
           reload=False)
