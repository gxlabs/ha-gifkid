"""Config flow for GifKid integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_API_DOMAIN,
    DEFAULT_API_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class GifKidConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GifKid."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate the client ID by making a test API call
                session = async_get_clientsession(self.hass)
                api_domain = user_input.get(CONF_API_DOMAIN, DEFAULT_API_DOMAIN)
                headers = {
                    "User-Agent": f"gifkid_app:{user_input[CONF_CLIENT_ID]}",
                }
                
                async with session.get(
                    f"https://{api_domain}/device-configurations",
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        return self.async_create_entry(
                            title="GifKid",
                            data={
                                CONF_CLIENT_ID: user_input[CONF_CLIENT_ID],
                                CONF_API_DOMAIN: api_domain,
                            },
                        )
                    else:
                        errors["base"] = "cannot_connect"
                        
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Optional(
                        CONF_API_DOMAIN, 
                        default=DEFAULT_API_DOMAIN
                    ): str,
                }
            ),
            errors=errors,
        )
