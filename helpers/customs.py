import os

import toml

class TConfig():
    def __init__(self):
        with open('config.toml', 'r') as file:
            os.environ['UID'] = str(os.getuid())
            file = file.read().format_map(os.environ)
            self.config = toml.loads(file)

    def get_from(self, section, field, default=None, check_path=False):
        if section not in self.config:
            raise KeyError(f"Section '{section}' not in config file")
        retval = self.config[section].get(field, default)
        return retval if not check_path or (check_path and os.path.exists(retval)) else default
    
