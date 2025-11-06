import yaml
from pathlib import Path


config_path = Path(__file__).resolve().parent.parent / "config" / "config.yaml"
def load_config(config_path: str = config_path) -> dict:
    with open(config_path, "r") as file:
        config=yaml.safe_load(file)
        print("Configuration loaded successfully.")
        print(config)
    return config


#load_config("config/config.yaml")