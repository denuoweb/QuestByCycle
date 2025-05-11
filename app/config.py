import os
import toml

def load_config():
    root_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_path, '../config.toml')
    if os.path.exists(config_path):
        return toml.load(config_path)
    else:
        raise FileNotFoundError("The configuration file was not found.")
