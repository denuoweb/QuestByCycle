import os
import toml

SQLALCHEMY_ENGINE_OPTIONS = {
    # ping once before using a connection that came out of the pool
    "pool_pre_ping": True,
    # recycle connections after 55 min ( < RDS / PG default TCP idle timeout )
    "pool_recycle": 3300,        # seconds
}

def load_config():
    root_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(root_path, '../config.toml')
    if os.path.exists(config_path):
        return toml.load(config_path)
    else:
        raise FileNotFoundError("The configuration file was not found.")
