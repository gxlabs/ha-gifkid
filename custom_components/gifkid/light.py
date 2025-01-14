"""Platform for GifKid light integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GifKid lights."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    
    lights = []
    for device in coordinator.data["device_configurations"]:
        lights.append(GifKidLight(coordinator, device, entry))
    
    async_add_entities(lights)

class GifKidLight(CoordinatorEntity, LightEntity):
    """Representation of a GifKid Light."""

    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{device['device_id']}"
        self._attr_name = device["name"]
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["device_id"])},
            name=device["name"],
            manufacturer="GX Labs",
            model="LED Display",
        )

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        device = self._get_device()
        return device["is_enabled"] if device else False

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        device = self._get_device()
        if device and device["brightness"] is not None:
            return int(device["brightness"] * 255)
        return None

    def _get_device(self) -> dict | None:
        """Get the device configuration from coordinator data."""
        for device in self.coordinator.data["device_configurations"]:
            if device["device_id"] == self._device["device_id"]:
                return device
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255)
        brightness_decimal = brightness / 255

        # Update enabled state
        await self._async_update_device(True, brightness_decimal)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        await self._async_update_device(False, self.brightness / 255 if self.brightness else 0.5)

    async def _async_update_device(self, is_enabled: bool, brightness: float) -> None:
        """Update device state."""
        headers = self.coordinator._headers
        data = {
            "is_enabled": is_enabled,
            "brightness": brightness,
        }

        async with self.coordinator.session.patch(
            f"https://{self.coordinator.api_domain}/device-configurations/{self._device['device_id']}",
            headers=headers,
            json=data,
        ) as response:
            response.raise_for_status()
            
        # Schedule coordinator update
        await self.coordinator.async_request_refresh()
