"""API for Terabox."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import aiofiles
from aiohttp import ClientResponse
from aiohttp.client_exceptions import ClientError, ClientResponseError
from aioterabox.api import TeraboxClient as TeraboxApiClient
from aioterabox.exceptions import TeraboxApiError, TeraboxNotFoundError
from homeassistant.components.backup import AgentBackup, suggested_filename
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_BACKUP_LOCATION

_UPLOAD_AND_DOWNLOAD_TIMEOUT = 12 * 3600
_UPLOAD_MAX_RETRIES = 20

_LOGGER = logging.getLogger(__name__)


@dataclass
class StorageQuotaData:
    """Class to represent storage quota data."""

    limit: int | None
    usage: int
    # usage_in_drive: int
    # usage_in_trash: int


@dataclass(kw_only=True)
class BackupMetadata:
    """Represent single backup file metadata."""

    file_path: str
    metadata: dict[str, str | dict[str, list[str]]]
    metadata_file: str


class TeraboxClient:
    """Terabox client."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry | None = None,
        *,
        email: str,
        password: str,
        cookies: dict[str, Any] | None = None,
    ) -> None:
        """Initialize Terabox client."""
        # self._ha_instance_id = ha_instance_id
        self.hass = hass
        self.config_entry = config_entry
        self._email = email
        self._password = password
        self._initial_cookies = cookies
        self._session = async_get_clientsession(hass)
        self._api = TeraboxApiClient(
            email=self._email,
            password=self._password,
            session=self._session,
            cookies=cookies,
        )

    @property
    def email(self) -> str:
        """Return the email address."""
        return self._email

    @property
    def account_id(self) -> str | None:
        """Return the account ID."""
        if not self._api.account:
            raise TeraboxApiError("Account information not loaded")
        return str(self._api.account['account_id'])

    @property
    def backup_location(self) -> str:
        """Return the backup location."""
        if self.config_entry:
            return f'/{self.config_entry.data[CONF_BACKUP_LOCATION].strip("/")}'
        return ''

    async def login(self) -> None:
        """Login to Terabox."""
        try:
            await self._api.login()
            await self._api.get_account_id()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed("Invalid authentication") from err
            raise ConfigEntryNotReady("Unable to connect to Terabox") from err
        except ClientError as err:
            raise ConfigEntryNotReady("Unable to connect to Terabox") from err

        # Save cookies
        if self.config_entry:
            options = dict(self.config_entry.options or {})
            # options.update({'cookies': self._api._cookies})
            options.update(self._api._cookies)
            self.hass.config_entries.async_update_entry(self.config_entry, options=options)

    async def async_get_storage_quota(self) -> StorageQuotaData:
        """Get storage quota of the current user."""
        res = await self._api.get_storage_quota()

        limit = res.get("total")
        return StorageQuotaData(
            limit=int(limit) if limit is not None else None,
            usage=int(res.get("used", 0)),
        )

    async def async_create_ha_root_folder_if_not_exists(self) -> tuple[str, str]:
        """Create Home Assistant folder if it doesn't exist."""
        try:
            await self._api.list_remote_directory(self.backup_location)
        except TeraboxNotFoundError:
            _LOGGER.debug("Creating new folder: %s", self.backup_location)
            res = await self._api.create_directory(self.backup_location)
            _LOGGER.debug("Created folder: %s", res)
            return str(res['fs_id']), res['path']
        return '', self.backup_location

    async def async_upload_backup(
        self,
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        backup: AgentBackup,
    ) -> None:
        """Upload a backup."""
        folder_id, _ = await self.async_create_ha_root_folder_if_not_exists()

        file_name = suggested_filename(backup)
        file_path = f"{self.backup_location}/{file_name}"
        iterator = await open_stream()
        _LOGGER.debug("Uploading backup to %s", file_path)
        async with aiofiles.tempfile.NamedTemporaryFile(suffix=file_name) as tmpfile:
            async for b in iterator:
                await tmpfile.write(b)
            await tmpfile.flush()
            await tmpfile.seek(0)
            _LOGGER.debug("%s to %s", tmpfile.name, file_path)
            try:
                upload_details = await self._api.upload_file(
                    tmpfile.name,
                    file_path,
                )
            except TimeoutError:
                raise HomeAssistantError(f"Timeout while uploading backup: {file_path}")
        real_uploaded_path = upload_details['path']

        _LOGGER.debug("Writing backup metadata for %s", real_uploaded_path)
        metadata: dict[str, str | dict[str, list[str]]] = {
            "file_path": real_uploaded_path,
            "metadata": backup.as_dict(),
        }
        async with aiofiles.tempfile.NamedTemporaryFile(suffix='.json') as tmpfile:
            await tmpfile.write(json.dumps(metadata).encode())
            await tmpfile.flush()
            await tmpfile.seek(0)
            await self._api.upload_file(
                tmpfile.name,
                f"{self.backup_location}/.{backup.backup_id}.metadata.json",
            )

        # Save cookies, it usually changes after upload
        if self.config_entry:
            options = dict(self.config_entry.options or {})
            if options != dict(self._api._cookies):
                options.update(self._api._cookies)
            self.hass.config_entries.async_update_entry(self.config_entry, options=options)

    async def async_list_backups(self) -> list[AgentBackup]:
        """List backups."""
        try:
            file_infos = await self._api.list_remote_directory(self.backup_location)
        except TeraboxApiError as err:
            _LOGGER.error("Failed to list backups: %s", err)
            file_infos = []

        backups = []
        metadatas = []
        for file in file_infos:
            if file.path.endswith(".metadata.json"):
                metadatas.append(file.path)
        if metadatas:
            meta = await self._api.get_files_meta(metadatas)
            for file in meta:
                async with self._session.get(file['dlink']) as resp:
                    metadata = BackupMetadata(
                        **(await resp.json(content_type=None)),
                        metadata_file=file['path'],
                    )
                    backups.append(AgentBackup.from_dict(metadata.metadata))
        return backups

    async def async_get_size_of_all_backups(self) -> int:
        """Get size of all backups."""
        backups = await self.async_list_backups()

        return sum(backup.size for backup in backups)

    async def _load_metadata(self, backup_id: str) -> BackupMetadata:
        # Test for metadata file existence.
        metadata_file = (
            f"{self.backup_location}/.{backup_id}.metadata.json"
        )
        try:
            res = await self._api.get_files_meta([metadata_file])
        except TeraboxNotFoundError:
            raise FileNotFoundError(
                f"Metadata file not found at remote location: {metadata_file}"
            )

        async with self._session.get(res[0]['dlink']) as resp:
            content = await resp.json(content_type=None)
            return BackupMetadata(
                **content,
                metadata_file=metadata_file
            )

    async def async_get_backup_file_url(self, backup_id: str) -> tuple[str | None, BackupMetadata | None]:
        """Get file_id of backup if it exists."""

        metadata: BackupMetadata = await self._load_metadata(backup_id)

        metas = await self._api.get_files_meta([metadata.file_path])
        # fs_ids = [str(file['fs_id']) for file in metas]
        # links = await self._api.download_file(fs_ids)
        for file in metas:
            return str(file['dlink']), metadata
        return None, None

    async def async_delete(self, file_paths: list[str]) -> None:
        """Delete file."""
        await self._api.delete_files(file_paths)

    async def async_download(self, file_url: str) -> ClientResponse:
        """Download a file in chunks."""

        resp = await self._session.get(
            file_url,
            cookies=self._api.request_cookies,
            headers={
                "Accept-Encoding": "identity",
                "Referer": "https://www.terabox.com/",
            },
        )
        resp.raise_for_status()
        return resp

    # async def async_download_to_file(self, file_url: str, aiofile: Any) -> None:
    #     """Download a file in chunks.
    #     I couldn't find a better way to stream download with aioterabox,
    #     just streaming causes connection reset errors.
    #     """
    #
    #     resp = await self._session.get(
    #         file_url,
    #         cookies=self._api.request_cookies,
    #         headers={
    #             "Accept-Encoding": "identity",
    #             "Referer": "https://www.terabox.com/",
    #             "Range": "bytes=0-",
    #         },
    #     )
    #     resp.raise_for_status()
    #
    #     async for chunk in resp.content.iter_chunked(1024 * 1024):
    #         await aiofile.write(chunk)
