import yaml
import os
import shutil

CONFIG_FILE = "config.yaml"
DEFAULT_CONFIG_FILE = "config.default.yaml"

def load_config():
    """
    Loads the configuration from config.yaml.
    If config.yaml does not exist, it creates it from config.default.yaml.
    """
    if not os.path.exists(CONFIG_FILE):
        if os.path.exists(DEFAULT_CONFIG_FILE):
            print(f"[INFO] {CONFIG_FILE} not found. Creating from {DEFAULT_CONFIG_FILE}...")
            shutil.copy(DEFAULT_CONFIG_FILE, CONFIG_FILE)
            print(f"[WARN] Please edit {CONFIG_FILE} with your API keys and settings.")
        else:
            raise FileNotFoundError(f"{DEFAULT_CONFIG_FILE} not found. Cannot create config.")

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config

def validate_config(config):
    """
    Validates critical configuration values.
    """
    required_keys = ["gemini_api_key", "note_session_cookie"]
    missing_keys = [key for key in required_keys if not config.get(key) or config.get(key).startswith("YOUR_")]
    
    if missing_keys:
        print(f"[WARN] The following configuration keys seem to be default or missing: {', '.join(missing_keys)}")
        print(f"[WARN] Please update {CONFIG_FILE}.")
        return False
    return True
