"""Constants for the Terabox integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN = "terabox"

SCAN_INTERVAL = timedelta(hours=6)
DRIVE_FOLDER_PREFIX = "hass_backup"

STORAGE_KEY = "terraform_cookies"
STORAGE_VERSION = 1

CONF_BACKUP_LOCATION: Final = "backup_location"
CONF_NDUS: Final = "ndus"
CONF_CSRF_TOKEN: Final = "csrfToken"
CONF_BROWSERID: Final = "browserid"
CONF_JSTOKEN: Final = "jstoken"
