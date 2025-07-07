import os
import threading

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from config import CONFIG_LOG_USER_FILE_PATH, CONFIG_LOG_SYSTEM_FILE_PATH, CONFIG_DATA_PATH, CONFIG, save_config
from helpers.csv_helper import get_data_from_csv
from helpers.data_helper import import_data_to_csv
from helpers.listing_helper import update_listings
from helpers.scraper import Scraper, ScraperDriverManager

scraper_driver_manager: ScraperDriverManager | None = None
scraper: Scraper | None = None


def launch_browser_and_open_gui():
    global scraper, scraper_driver_manager

    launch_facebook_marketplace_bot()

    scraper_driver_manager = ScraperDriverManager()
    scraper_driver_manager.create_tab('gui', True)
    scraper_driver_manager.driver.get('http://localhost:8080')


def launch_facebook_marketplace_bot():
    current_log_file = CONFIG_LOG_USER_FILE_PATH

    def run_marketplace_bot():
        global scraper, scraper_driver_manager

        # scraper_driver_manager.create_tab('facebook', True)
        # scraper = Scraper(driver=scraper_driver_manager.driver,
        #                   url='https://facebook.com')
        # scraper.add_login_functionality(login_url='https://facebook.com',
        #                                 is_logged_in_selector='svg[aria-label="Your profile"]',
        #                                 cookies_file_name='facebook')
        # scraper.go_to_page('https://facebook.com/marketplace/you/selling')


        # # Import data from external resources to csv file
        #import_data_to_csv(CONFIG_DATA_PATH)
        # # Get data for vehicle type listings from csvs/vehicles.csv
        vehicle_listings = get_data_from_csv(CONFIG_DATA_PATH)
        # Publish all of the vehicles into the facebook marketplace
        update_listings(vehicle_listings, scraper)

    def on_start_button_click():
        threading.Thread(target=run_marketplace_bot).start()

    def on_upload_data_button_click():
        import_data_to_csv(CONFIG_DATA_PATH)

    def on_save_config_button_click():
        CONFIG['scraper']['random_delay']['min'] = config_field_random_delay_min.value
        CONFIG['scraper']['random_delay']['max'] = config_field_random_delay_max.value
        save_config()
        ui.notify('Settings successfully saved', type='positive')

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
            'User log': CONFIG_LOG_USER_FILE_PATH,
            'System log': CONFIG_LOG_SYSTEM_FILE_PATH,
        }

        current_log_file = log_file_map.get(selected.value, CONFIG_LOG_USER_FILE_PATH)

    ui.timer(0.5, update_log_view)

    with ui.column().classes('w-full items-center'):
        ui.markdown('# **Facebook Marketplace Auto Dealership Bot**')
        ui.markdown('Publish all your ads easy')

        with ui.row():
            ui.button(text="Start",
                      on_click=on_start_button_click)
            with ui.button(text="Upload data",
                           on_click=on_upload_data_button_click,
                           color='secondary'):
                ui.tooltip('Upload and/or update data to inner database from external resources')

        with ui.expansion('Config').classes('w-full'):
            with ui.row():
                ui.button(text="Save",
                          on_click=on_save_config_button_click)
            config_field_random_delay_min = ui.number(label='Random delay, min (seconds)',
                      value=CONFIG['scraper']['random_delay']['min'],
                      format='%.2f')
            config_field_random_delay_max = ui.number(label='Random delay, max (seconds)',
                      value=CONFIG['scraper']['random_delay']['max'],
                      format='%.2f')

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
