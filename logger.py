import logging

from config import CONFIG_LOG_USER_FILE_PATH, CONFIG_LOG_SYSTEM_FILE_PATH

# --- USER Logger ---
user_logger = logging.getLogger("user")
user_logger.setLevel(logging.INFO)

user_handler = logging.FileHandler(CONFIG_LOG_USER_FILE_PATH, encoding="utf-8")
user_handler.setLevel(logging.INFO)
user_handler.setFormatter(logging.Formatter(fmt='[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))

if not user_logger.hasHandlers():
    user_logger.addHandler(user_handler)
    user_logger.propagate = False  # чтобы не улетало в root

# --- SYSTEM Logger ---
system_logger = logging.getLogger("system")
system_logger.setLevel(logging.DEBUG)

system_handler = logging.FileHandler(CONFIG_LOG_SYSTEM_FILE_PATH, encoding="utf-8")
system_handler.setLevel(logging.DEBUG)
system_handler.setFormatter(
    logging.Formatter(fmt='[%(asctime)s] %(levelname)s in %(funcName)s (%(filename)s:%(lineno)d): %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S'))

if not system_logger.hasHandlers():
    system_logger.addHandler(system_handler)
    system_logger.propagate = False
