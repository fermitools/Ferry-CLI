import os
from typing import Optional, Any

import toml


class TConfig:
    def __init__(self) -> None:
        with open("config.toml", "r") as file:
            os.environ["UID"] = str(os.getuid())
            file_mapped = file.read().format_map(os.environ)
            self.config = toml.loads(file_mapped)

    def get_from(
        self,
        section: str,
        field: str,
        default: Optional[Any] = None,
        check_path: bool = False,
    ) -> Any:
        if section not in self.config:
            raise KeyError(f"Section '{section}' not in config file")
        retval = self.config[section].get(field, default)
        return (
            retval
            if not check_path or (check_path and os.path.exists(retval))
            else default
        )
