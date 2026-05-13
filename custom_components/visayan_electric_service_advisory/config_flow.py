"""Config flow for Visayan Electric Service Advisory."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_LOCATIONS


class VECOServiceAdvisoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Visayan Electric Service Advisory."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            locations_raw = user_input.get(CONF_LOCATIONS, "")
            locations = [
                loc.strip()
                for loc in locations_raw.split(",")
                if loc.strip()
            ]
            if not locations:
                errors[CONF_LOCATIONS] = "no_locations"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Visayan Electric Service Advisory",
                    data={CONF_LOCATIONS: locations},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATIONS): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "example": "Canduman, Jagobiao",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow."""
        return VECOOptionsFlow(config_entry)


class VECOOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Visayan Electric Service Advisory."""

    def __init__(self, config_entry):
        """Initialise options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}

        if user_input is not None:
            locations_raw = user_input.get(CONF_LOCATIONS, "")
            locations = [
                loc.strip()
                for loc in locations_raw.split(",")
                if loc.strip()
            ]
            if not locations:
                errors[CONF_LOCATIONS] = "no_locations"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_LOCATIONS: locations},
                )

        current_locations = self.config_entry.options.get(
            CONF_LOCATIONS,
            self.config_entry.data.get(CONF_LOCATIONS, []),
        )
        current_locations_str = ", ".join(current_locations)

        schema = vol.Schema(
            {
                vol.Required(CONF_LOCATIONS, default=current_locations_str): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "example": "Canduman, Jagobiao",
            },
        )
