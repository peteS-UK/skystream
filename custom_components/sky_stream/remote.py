from __future__ import annotations

import logging

from collections.abc import Iterable
from typing import Any
from homeassistant.exceptions import HomeAssistantError

from homeassistant import config_entries, core
from homeassistant.components.remote import (
    RemoteEntity,
)

from homeassistant.const import CONF_NAME

from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CONF_BROADLINK,
    COMMANDS,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    async_add_entities(
        [Device(hass, config_entry.data[CONF_NAME], config_entry.data[CONF_BROADLINK])]
    )


class Device(RemoteEntity):
    # Representation of a Emotiva Processor

    def __init__(self, hass, name, broadlink_entity):
        self._hass = hass
        self._entity_id = f"remote.{DOMAIN}"
        self._unique_id = f"{DOMAIN}_" + name.replace(" ", "_").replace(
            "-", "_"
        ).replace(":", "_")
        self._name = "Remote"
        self._broadlink_entity = broadlink_entity

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        return self._name

    @property
    def has_entity_name(self):
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._unique_id)
            }
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def entity_id(self):
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id):
        self._entity_id = entity_id

    async def _send_broadlink_command(self, command):
        await self._hass.services.async_call(
            "remote",
            "send_command",
            {
                "entity_id": self._broadlink_entity,
                "num_repeats": "1",
                "delay_secs": "0.4",
                "command": f"b64:{COMMANDS[command]}",
            },
        )

    async def async_turn_off(self) -> None:
        await self._send_broadlink_command("power")

    async def async_turn_on(self) -> None:
        await self._send_broadlink_command("power")

    async def async_toggle(self) -> None:
        await self._send_broadlink_command("power")

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        try:
            _command_list = command[0].replace(" ", "").split(",")
            if len(_command_list) > 1:
                raise HomeAssistantError("Only a single command is supported.")
            else:
                await self._send_broadlink_command(command)
        except Exception:
            raise HomeAssistantError("Invalid remote command format.")
