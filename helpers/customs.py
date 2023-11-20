import configparser
import os
import re

class CustomConfigParser(configparser.ConfigParser):
    def read(self, filenames, encoding=None):
        os.environ['UID'] = str(os.getuid())
        super().read(filenames, encoding)

        for section in self.sections():
            for option in self.options(section):
                value = self.get(section, option)
                expanded_value = self._expand_env_variables(value)
                self.set(section, option, expanded_value)

    def _expand_env_variables(self, value):
        # Replaces $VARIABLE or ${VARIABLE} with the environment variable value
        pattern = r'\$\{(\w+)\}'
        def replace_with_env(match):
            variable_name = match.group(1)
            return os.environ.get(variable_name, '')
        result_string = re.sub(pattern, replace_with_env, value)
    
        return result_string.replace("\"", "")


