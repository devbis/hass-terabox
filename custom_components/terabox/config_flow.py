"""Config flow to configure the SFTP Storage integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from . import TeraboxClient
from .const import (
    CONF_BACKUP_LOCATION,
    CONF_BROWSERID,
    CONF_CSRF_TOKEN,
    CONF_JSTOKEN,
    CONF_NDUS,
    DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): TextSelector(
            config=TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_BACKUP_LOCATION): str,

        vol.Optional(CONF_JSTOKEN): TextSelector(
            config=TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_CSRF_TOKEN): str,
        vol.Optional(CONF_BROWSERID): str,
        vol.Optional(CONF_NDUS): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_JSTOKEN): str,
        vol.Optional(CONF_CSRF_TOKEN): str,
        vol.Optional(CONF_BROWSERID): str,
        vol.Optional(CONF_NDUS): str,
    }
)


# class SFTPStorageException(Exception):
#     """Base exception for SFTP Storage integration."""
#
#
# class SFTPStorageInvalidPrivateKey(SFTPStorageException):
#     """Exception raised during config flow - when user provided invalid private key file."""
#
#
# class SFTPStorageMissingPasswordOrPkey(SFTPStorageException):
#     """Exception raised during config flow - when user did not provide password or private key file."""


class TeraboxFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle an Terabox Storage config flow."""

    def __init__(self) -> None:
        """Initialize SFTP Storage Flow Handler."""
        self._client_keys: list = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial (authentication) configuration step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA
            )

        # self._async_abort_entries_match(
        #     {
        #         CONF_EMAIL: user_input[CONF_EMAIL],
        #         CONF_BACKUP_LOCATION: user_input[CONF_BACKUP_LOCATION],
        #     }
        # )

        errors: dict[str, str] = {}
        cookies: dict[str, str] | None = {
            CONF_JSTOKEN: user_input.get(CONF_JSTOKEN, ""),
            CONF_CSRF_TOKEN: user_input.get(CONF_CSRF_TOKEN, ""),
            CONF_BROWSERID: user_input.get(CONF_BROWSERID, ""),
            CONF_NDUS: user_input.get(CONF_NDUS, ""),
        }
        if not all(bool(value) for value in cookies.values()):
            cookies = None

        terabox_client = TeraboxClient(
            self.hass,
            email=user_input[CONF_EMAIL],
            password=user_input[CONF_PASSWORD],
            cookies=cookies,
        )
        try:
            await terabox_client.login()
        except (ConfigEntryNotReady, ConfigEntryAuthFailed):
            errors["base"] = "invalid_auth"
        else:
            unique_id = f'terabox_{terabox_client.account_id}'
            await self.async_set_unique_id(unique_id)

            # _LOGGER.debug("Creating an entry for %s", device_info["name"])
        if user_input[CONF_EMAIL] == "" or user_input[CONF_PASSWORD] == "":
            errors["base"] = "invalid_auth"
        else:
            return self.async_create_entry(
                title=terabox_client.account_id,
                data={
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                    CONF_BACKUP_LOCATION: user_input.get(CONF_BACKUP_LOCATION, ""),
                },
                options=cookies,
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    # @staticmethod
    # @callback
    # def async_get_options_flow(
    #     config_entry: ConfigEntry,
    # ) -> SchemaOptionsFlowHandler:
    #     """Return the options flow."""
    #     return SchemaOptionsFlowHandler(config_entry, OPTIONS_FLOW)


#     async def async_step_user(
#         self,
#         user_input: dict[str, Any] | None = None,
#         step_id: str = "user",
#     ) -> ConfigFlowResult:
#         """Handle a flow initiated by the user."""
#         errors: dict[str, str] = {}
#         placeholders: dict[str, str] = {}
#
#         if user_input is not None:
#             LOGGER.debug("Source: %s", self.source)
#
#             self._async_abort_entries_match(
#                 {
#                     CONF_EMAIL: user_input[CONF_EMAIL],
#                     CONF_BACKUP_LOCATION: user_input[CONF_BACKUP_LOCATION],
#                 }
#             )
#
#             try:
#                 # Create a session using your credentials
#                 user_config = TeraboxConfigEntryData(
#                     host=user_input[CONF_HOST],
#                     port=user_input[CONF_PORT],
#                     username=user_input[CONF_USERNAME],
#                     password=user_input.get(CONF_PASSWORD),
#                     private_key_file=user_input.get(CONF_PRIVATE_KEY_FILE),
#                     backup_location=user_input[CONF_BACKUP_LOCATION],
#                 )
#
#                 placeholders["backup_location"] = user_config.backup_location
#
#                 # Raises:
#                 # - OSError, if host or port are not correct.
#                 # - SFTPStorageInvalidPrivateKey, if private key is not valid format.
#                 # - asyncssh.misc.PermissionDenied, if credentials are not correct.
#                 # - SFTPStorageMissingPasswordOrPkey, if password and private key are not provided.
#                 # - asyncssh.sftp.SFTPNoSuchFile, if directory does not exist.
#                 # - asyncssh.sftp.SFTPPermissionDenied, if we don't have access to said directory
#                 async with (
#                     connect(
#                         host=user_config.host,
#                         port=user_config.port,
#                         options=await self.hass.async_add_executor_job(
#                             get_client_options, user_config
#                         ),
#                     ) as ssh,
#                     ssh.start_sftp_client() as sftp,
#                 ):
#                     await sftp.chdir(user_config.backup_location)
#                     await sftp.listdir()
#
#                 LOGGER.debug(
#                     "Will register SFTP Storage agent with user@host %s@%s",
#                     user_config.host,
#                     user_config.username,
#                 )
#
#             except OSError as e:
#                 LOGGER.exception(e)
#                 placeholders["error_message"] = str(e)
#                 errors["base"] = "os_error"
#             except SFTPStorageInvalidPrivateKey:
#                 errors["base"] = "invalid_key"
#             except PermissionDenied as e:
#                 placeholders["error_message"] = str(e)
#                 errors["base"] = "permission_denied"
#             except SFTPStorageMissingPasswordOrPkey:
#                 errors["base"] = "key_or_password_needed"
#             except SFTPNoSuchFile:
#                 errors["base"] = "sftp_no_such_file"
#             except SFTPPermissionDenied:
#                 errors["base"] = "sftp_permission_denied"
#             except Exception as e:  # noqa: BLE001
#                 LOGGER.exception(e)
#                 placeholders["error_message"] = str(e)
#                 placeholders["exception"] = type(e).__name__
#                 errors["base"] = "unknown"
#             else:
#                 return self.async_create_entry(
#                     title=f"{user_config.username}@{user_config.host}",
#                     data=user_input,
#                 )
#             finally:
#                 # We remove the saved private key file if any error occurred.
#                 if errors and bool(user_input.get(CONF_PRIVATE_KEY_FILE)):
#                     keyfile = Path(user_input[CONF_PRIVATE_KEY_FILE])
#                     keyfile.unlink(missing_ok=True)
#                     with suppress(OSError):
#                         keyfile.parent.rmdir()
#
#         if user_input:
#             user_input.pop(CONF_PRIVATE_KEY_FILE, None)
#
#         return self.async_show_form(
#             step_id=step_id,
#             data_schema=self.add_suggested_values_to_schema(DATA_SCHEMA, user_input),
#             description_placeholders=placeholders,
#             errors=errors,
#         )
#
#
# async def save_uploaded_pkey_file(hass: HomeAssistant, uploaded_file_id: str) -> str:
#     """Validate the uploaded private key and move it to the storage directory.
#
#     Return a string representing a path to private key file.
#     Raises SFTPStorageInvalidPrivateKey if the file is invalid.
#     """
#
#     def _process_upload() -> str:
#         with process_uploaded_file(hass, uploaded_file_id) as file_path:
#             try:
#                 # Initializing this will verify if private key is in correct format
#                 SSHClientConnectionOptions(client_keys=[file_path])
#             except KeyImportError as err:
#                 LOGGER.debug(err)
#                 raise SFTPStorageInvalidPrivateKey from err
#
#             dest_path = Path(hass.config.path(STORAGE_DIR, DOMAIN))
#             dest_file = dest_path / f".{ulid()}_{DEFAULT_PKEY_NAME}"
#
#             # Create parent directory
#             dest_file.parent.mkdir(exist_ok=True)
#             return str(shutil.move(file_path, dest_file))
#
#     return await hass.async_add_executor_job(_process_upload)
