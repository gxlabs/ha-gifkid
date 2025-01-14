"""The GifKid integration."""
from __future__ import annotations

import logging
from datetime import timedelta

import async_timeout
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    COORDINATOR,
    DEFAULT_SCAN_INTERVAL,
    CONF_API_DOMAIN,
    DEFAULT_API_DOMAIN,
    API_USER_AGENT,
)

PLATFORMS: list[Platform] = [Platform.LIGHT]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GifKid from a config entry."""
    client_id = entry.data[CONF_CLIENT_ID]
    api_domain = entry.data.get(CONF_API_DOMAIN, DEFAULT_API_DOMAIN)
    session = async_get_clientsession(hass)

    coordinator = GifKidDataUpdateCoordinator(
        hass,
        config_entry_id=entry.entry_id,
        client_id=client_id,
        api_domain=api_domain,
        session=session,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class GifKidDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching GifKid data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        client_id: str,
        api_domain: str,
        session,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry_id = config_entry_id
        self.client_id = client_id
        self.api_domain = api_domain
        self.session = session
        self._headers = {
            "User-Agent": API_USER_AGENT.format(client_id=client_id),
            "Content-Type": "application/json",
        }

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            async with async_timeout.timeout(10):
                response = await self.session.get(
                    f"https://{self.api_domain}/device-configurations",
                    headers=self._headers,
                )
                response.raise_for_status()
                return await response.json()

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
