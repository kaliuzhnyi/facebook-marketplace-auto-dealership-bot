import os
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from config import CONFIG_LOG_USER_FILE_PATH, CONFIG_LOG_SYSTEM_FILE_PATH, CONFIG_DATA_PATH, CONFIG, save_config
from helpers.csv_helper import get_data_from_csv
from helpers.data_helper import import_data_to_csv
from helpers.listing_helper import check_and_update_listings, check_and_remove_listings
from helpers.scraper import Scraper, ScraperDriverManager
from logger import system_logger, user_logger

scraper_driver_manager: ScraperDriverManager | None = None
scraper: Scraper | None = None

scheduler = BackgroundScheduler()
scheduler.start()


def launch_browser_and_open_gui():
    global scraper, scraper_driver_manager

    launch_facebook_marketplace_bot()

    system_logger.info('Run browser with program UI')

    scraper_driver_manager = ScraperDriverManager()
    scraper_driver_manager.create_tab('gui', True)
    scraper_driver_manager.driver.get('http://localhost:8080')


def launch_facebook_marketplace_bot():
    current_log_file = CONFIG_LOG_USER_FILE_PATH

    button_stop = None
    button_start_with_schedule = None

    def run_marketplace_bot():
        global scraper, scraper_driver_manager

        scraper_driver_manager.create_tab('facebook', True)
        scraper = Scraper(driver=scraper_driver_manager.driver, url='https://facebook.com')
        scraper.add_login_functionality(login_url='https://facebook.com',
                                        is_logged_in_selector='svg[aria-label="Your profile"]',
                                        cookies_file_name='facebook')
        scraper.go_to_page('https://facebook.com/marketplace/you/selling')

        # Get data for vehicle type listings from csvs/vehicles.csv
        vehicle_listings = get_data_from_csv(CONFIG_DATA_PATH)
        # Publish all the vehicles into the facebook marketplace
        check_and_remove_listings(listings=vehicle_listings, scraper=scraper)
        check_and_update_listings(listings=vehicle_listings, scraper=scraper)

    def on_start_button_click() -> None:
        threading.Thread(target=run_marketplace_bot).start()

    def on_start_with_schedule_button() -> None:
        if button_start_with_schedule:
            button_start_with_schedule.disable()
        if button_stop:
            button_stop.enable()

        job_id = 'listing_publishing'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        trigger_crontab = CONFIG['scraper']['schedule']['crontab']
        if not trigger_crontab:
            return

        trigger = CronTrigger.from_crontab(trigger_crontab)
        scheduler.add_job(run_marketplace_bot, trigger=trigger, id=job_id)

    def on_stop_button() -> None:
        if button_start_with_schedule:
            button_start_with_schedule.enable()
        if button_stop:
            button_stop.disable()

        job_id = 'listing_publishing'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    def on_upload_data_button_click() -> None:
        import_data_to_csv(CONFIG['data']['path'], CONFIG['data']['upload_limit'])

    def on_save_config_button_click() -> None:
        CONFIG['scraper']['action_random_delay']['min'] = config_field_action_random_delay_min.value
        CONFIG['scraper']['action_random_delay']['max'] = config_field_action_random_delay_max.value
        CONFIG['scraper']['listing_random_delay']['min'] = config_field_listing_random_delay_min.value
        CONFIG['scraper']['listing_random_delay']['max'] = config_field_listing_random_delay_max.value
        CONFIG['scraper']['schedule']['crontab'] = config_field_scraper_schedule_crontab.value
        CONFIG['listing']['lifetime'] = config_field_listing_lifetime.value
        CONFIG['listing']['description']['replace']['old_value'] = config_listing_description_replace_old_value.value
        CONFIG['listing']['description']['replace']['new_value'] = config_listing_description_replace_new_value.value
        CONFIG['data']['path'] = config_field_data_path.value
        CONFIG['data']['upload_limit'] = config_field_data_upload_limit.value
        save_config()
        ui.notify('Settings successfully saved', type='positive')

    def on_clear_log_button_click() -> None:
        if os.path.exists(current_log_file):
            open(current_log_file, "w").close()

    def update_log_view() -> None:
        if os.path.exists(current_log_file):
            with open(current_log_file, 'r', encoding='utf-8') as f:
                log_area.value = f.read()

    def on_log_type_change(selected: ValueChangeEventArguments) -> None:
        nonlocal current_log_file

        log_file_map = {
            'User log': CONFIG_LOG_USER_FILE_PATH,
            'System log': CONFIG_LOG_SYSTEM_FILE_PATH,
        }

        current_log_file = log_file_map.get(selected.value, CONFIG_LOG_USER_FILE_PATH)

    system_logger.info('Build program UI - start')

    ui.timer(0.5, update_log_view)
    with ((ui.column().classes('w-full items-center'))):
        ui.markdown('# **Facebook Marketplace Auto Dealership Bot**')
        ui.markdown('Publish all your ads easy')

        with ui.row():
            with ui.button(text='Start with schedule', on_click=on_start_with_schedule_button,
                           color='positive') as button_start_with_schedule:
                ui.tooltip('Start process periodically with schedule. Upload data and publish listings')

            with ui.button(text='Stop', on_click=on_stop_button, color='negative') as button_stop:
                ui.tooltip('Start process.')

            with ui.button(text="Upload data", on_click=on_upload_data_button_click, color='secondary'):
                ui.tooltip('Upload and/or update data to inner database from external resources')

            with ui.button(text="Start", on_click=on_start_button_click):
                ui.tooltip('Start publish listings')

        with ui.expansion('Config').classes('w-full'):
            with ui.row():
                ui.button(text="Save", on_click=on_save_config_button_click)
            with ui.tabs().classes('w-full') as tabs:
                tab_panel_scraper = ui.tab('Scaper')
                tab_panel_listings = ui.tab('Listings')
                tab_panel_data = ui.tab('Data')

            with ui.tab_panels(tabs, value=tab_panel_scraper).classes('w-full'):
                with ui.tab_panel(tab_panel_scraper):
                    with ui.row().classes('w-full no-wrap'):
                        with ui.column().classes('w-1/3'):
                            ui.markdown('Action delay')
                            config_field_action_random_delay_min = (
                                ui.number(
                                    label='Random delay, min (seconds)',
                                    value=CONFIG['scraper']['action_random_delay']['min'],
                                    format='%.2f')
                                .tooltip('Min value of random delay between actions'))
                            config_field_action_random_delay_max = (
                                ui.number(
                                    label='Random delay, max (seconds)',
                                    value=CONFIG['scraper']['action_random_delay']['max'],
                                    format='%.2f')
                                .tooltip('Max value of random delay between actions'))
                        with ui.column().classes('w-1/3'):
                            ui.markdown('Listing delay')
                            config_field_listing_random_delay_min = (
                                ui.number(
                                    label='Random delay, min (seconds)',
                                    value=CONFIG['scraper']['listing_random_delay']['min'],
                                    format='%.2f')
                                .tooltip('Min value of random delay between listing'))
                            config_field_listing_random_delay_max = (
                                ui.number(
                                    label='Random delay, max (seconds)',
                                    value=CONFIG['scraper']['listing_random_delay']['max'],
                                    format='%.2f')
                                .tooltip('Max value of random delay between listing'))

                with ui.tab_panel(tab_panel_listings):
                    with ui.row().classes('w-full no-wrap'):
                        with ui.column().classes('w-1/3'):
                            ui.markdown('General')
                            config_field_listing_lifetime = (
                                ui.number(label='Lifetime (days)', value=CONFIG['listing']['lifetime'])
                                .props('step=1 min=1')
                                .tooltip(text='After this time, the listing will be removed and republished.'))
                            config_field_scraper_schedule_crontab = (
                                ui.input(label='Schedule (crontab)', value=CONFIG['scraper']['schedule']['crontab'])
                                .props('clearable')
                                .tooltip(text='Schedule to run job with listing publishing. More info: '
                                              'https://en.wikipedia.org/wiki/Cron and '
                                              'https://crontab.guru/'))
                        with ui.column().classes('w-2/3'):
                            ui.markdown('Description')
                            config_listing_description_replace_old_value = (
                                ui.textarea(label='Old value',
                                            value=CONFIG['listing']['description']['replace']['old_value'])
                                .tooltip(text='This value will be removed from listing description')
                                .classes('w-full h-1/4'))
                            config_listing_description_replace_new_value = (
                                ui.textarea(label='New value',
                                            value=CONFIG['listing']['description']['replace']['new_value'])
                                .tooltip(text='This value will be insert to listing description instead old value')
                                .classes('w-full h-1/4'))

                with ui.tab_panel(tab_panel_data):
                    config_field_data_path = (
                        ui.input(label='Path', value=CONFIG['data']['path'])
                        .props('clearable')
                        .tooltip(text='Path to file where listings are'))
                    config_field_data_upload_limit = (
                        ui.number(label='Upload limit', value=CONFIG['data']['upload_limit'])
                        .props('step=1 min=1')
                        .tooltip(text='Limit of listings which should be in file or '
                                      'which should be uploaded'))

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
                        .style('width: 100%; height: 100%;'))

    system_logger.info('Build program UI - end')


# if __name__ in {"__main__", "__mp_main__"}:
if __name__ == "__main__":
    system_logger.info('Start program')
    user_logger.info('Start program')
    threading.Thread(target=launch_browser_and_open_gui).start()
    ui.run(title="Facebook Bot Control",
           port=8080,
           show=False,
           reload=False)
