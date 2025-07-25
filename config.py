from pathlib import Path

import yaml

CONFIG_FILE_PATH = 'config.yaml'
CONFIG = {}


def load_config(config_file_path: str = CONFIG_FILE_PATH):
    global CONFIG
    if Path(config_file_path).exists():
        with open(config_file_path, 'r', encoding='utf-8') as f:
            CONFIG = yaml.safe_load(f) or {}
    else:
        CONFIG = {}


def save_config(config_file_path: str = CONFIG_FILE_PATH):
    global CONFIG
    with open(config_file_path, "w", encoding="utf-8") as f:
        yaml.dump(CONFIG, f, default_flow_style=False, allow_unicode=True)


load_config()

CONFIG_DATA_PATH = CONFIG['data']['path']
CONFIG_PHOTOS_BASE_FOLDER = CONFIG['photos']['base_folder']
CONFIG_DEALER_URL = CONFIG['dealer']['url']
CONFIG_DEALER_LICENSE_ID = CONFIG['dealer']['license_id']
CONFIG_LOG_USER_FILE_PATH = CONFIG['log']['user']['file_path']
CONFIG_LOG_SYSTEM_FILE_PATH = CONFIG['log']['system']['file_path']
