import yaml


def load_config(path="settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
DATA_PATH = CONFIG['data']['path']
PHOTOS_BASE_FOLDER = CONFIG['photos']['base_folder']
DEALER_URL = CONFIG['dealer']['url']
DEALER_LICENSE_ID = CONFIG['dealer']['license_id']
LOG_USER_FILE_PATH = CONFIG['log']['user']['file_path']
LOG_SYSTEM_FILE_PATH = CONFIG['log']['system']['file_path']
