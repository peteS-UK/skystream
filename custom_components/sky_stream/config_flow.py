import logging

from typing import Dict

import voluptuous as vol

from .const import DOMAIN, CONF_BROADLINK, TITLE

from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_BROADLINK): EntitySelector(
            EntitySelectorConfig(
                filter={"integration": "broadlink", "domain": "remote"}
            )
        ),
    }
)


class SelectError(exceptions.HomeAssistantError):
    """Error"""

    pass


async def validate_auth(hass: core.HomeAssistant, data: dict) -> None:
    if "name" not in data.keys():
        data["name"] = ""

    if len(data["name"]) < 1:
        # Manual entry requires host and name and model
        raise ValueError


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(self.hass, user_input)
            except ValueError:
                errors["base"] = "data"

            if not errors:
                # Input is valid, set data.
                self.data = user_input
                return self.async_create_entry(title=TITLE, data=self.data)

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )
