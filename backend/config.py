# backend/config.py

class Config:
    def __init__(self):
        self._settings = {
            "locale": "en"
        }

    def get_setting(self, key, default=None):
        return self._settings.get(key, default)

    def set_setting(self, key, value):
        self._settings[key] = value


# global config object (as expected by QBR)
config = Config()