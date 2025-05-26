from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import CONF_NAME
from homeassistant.helpers import (
    config_validation as cv,
    entity_platform,
)
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, SERVICE_SEND_COMMAND, CONF_BROADLINK, MANUFACTURER, MODEL


_LOGGER = logging.getLogger(__name__)

COMMANDS = {
    "power": "JgA+AFgdDw4PDg8dDx0dDg8PDw4PDg8ODw4PDhAOHR0PDg8ODw8PDg8OHg4PHR0dDw4PDg8PDw4dDw8cDw8PAA0FAAAAAAAAAAAAAA==",
    "colours": "JgA8AFYfDRAPDg8dDR8dDwwRDRANEA0QDw8MEQ4PHR0NEQwRDRAPDg0QHB8dDw4dDw8ODx0dHQ8PDg8ODwANBQAAAAAAAAAAAAAAAA==",
    "menu": "JgA8AFgdDw4PDw4dDx0dDw8ODw4PDg8PDg8PDg8OHh0ODw8ODw4PDg8PHR0dDw8dDg8PDh0dHg4PHQ8ODwANBQAAAAAAAAAAAAAAAA==",
    "play_pause": "JgA+AFgdDRAPDw4dDx0dDw0QDg8PDg8PDBEPDg8OHh0MEQ0QDRAPDg8PHR0dDw0fDg8PDh0PDRAPDg8ODx0PAA0FAAAAAAAAAAAAAA==",
    "mute": "JgA8AFYfDRANEA0fDR8bEQwRDRANEA0QDREMEQ0QGx8NEQwRDRAODw0QHB8bEQ4dDRANEQ4PDRAbEQ4eGwANBQAAAAAAAAAAAAAAAA==",
    "up": "JgA8AFYfDw4PDwwfDR8cEA0QDRANEQwRDRANEA0QHh0NEA0QDRANEQwRGx8bEQ0fDBEdHR0PDR8NEA0QDQANBQAAAAAAAAAAAAAAAA==",
    "down": "JgA6AFcdDw8ODw4eDh0eDg8ODw4PDw4PDw4PDg8OHh0PDg8ODw4PDw4PHR0cEA8dDw4dHR4ODx0PDh0ADQUAAAAAAAAAAAAAAAAAAA==",
    "left": "JgA6AFYfDRANEQ4dDR8cEA0QDRANEQwRDRANEA0QHB8NEA0QDRANEQwRGx8bEQ0fDBEbHxwQDR8bHw0ADQUAAAAAAAAAAAAAAAAAAA==",
    "right": "JgA6AFYfDBEMEQ0fDh0cEA8ODREMEQ4PDRAPDg8PHR0PDg8ODw8MEQ0QHR0cEA8dDRAdHh0ODx0cEA0ADQUAAAAAAAAAAAAAAAAAAA==",
    "ok": "JgA8AFgdDg8PDg8dDR8dDwwRDg8PDg8ODREMEQ4PHR0PDg8PDg8NEA8OHh0dDg8dDw4eHR0PDg8OHg4PDQANBQAAAAAAAAAAAAAAAA==",
    "back": "JgA8AFgdDw4PDw4dDx0eDg8ODw4PDw4PDw4PDg8OHh0ODw8ODw4PDw4PHR0dDw8dHR0PDg8ODw8ODx0PDgANBQAAAAAAAAAAAAAAAA==",
    "home": "JgA8AFYfDBENEA0fDR8dDg0RDBENEA0QDw4NEQwRGx8NEA0RDBENEA0QHBANHxsfHBANHw4PGxEOHgwRDQANBQAAAAAAAAAAAAAAAA==",
    "plus": "JgA+AFceDg8ODw0fDh4dDg8ODw8ODw8ODw4PDg0RHR0PDg0QDw8ODw4PHR0eDg8dDw4PDh4ODR8PDg8ODREOAA0FAAAAAAAAAAAAAA==",
    "mic": "JgA6AFgdDw4PDg8dDx0dDw4PDw4PDg8ODw8ODw4PHR0PDw4PDg8PDg8OHh0dDg8dDw4PDx0dHR0eDg8ADQUAAAAAAAAAAAAAAAAAAA==",
    "vol_up": "JgA+AFUfDREMEQ0fDB8cEA0QDREMEQ0QDRANEA0RGx8NEA0QDREMEQ0QGx8cEA0fDRANEA0QHB8NEA0QDRANAA0FAAAAAAAAAAAAAA==",
    "vol_down": "JgA8AFgdDw4PDg8dDx0dDw4PDw4PDg8PDg8ODw8OHR4ODw8ODw4PDg8PHR0dDw4eDg8ODw8OHR0PDw4PHQANBQAAAAAAAAAAAAAAAA==",
    "one": "JgA+AFYfDRANEA0fDR8bEA4QDBENEA0QDRANEQwRGx8ODw4QDRAMEQ4PGx8cEA0fDRANEA0RDBENEA0QDRAcAA0FAAAAAAAAAAAAAA==",
    "two": "JgA+AFYfDRANEQwfDR8cEA0QDRAPDw4PDBENEA0QHB8MEQ0QDRAPDg8PGx8bEQ4eDBEODw0QDRAPDwwRGx8NAA0FAAAAAAAAAAAAAA==",
    "three": "JgA+AFUfDw8MEQ8dDh0eDg8ODw8MEQ0QDRANEA0RHR0NEA8ODw8MEQ0QGx8cEA0fDRAPDg8ODw8NEA0QHQ8NAA0FAAAAAAAAAAAAAA==",
    "four": "JgA+AFYfDBENEA0fDR8bEA0RDBENEA0QDRANEQwRGx8NEA0RDBENEA0QHB8bEA0fDRANEQwRDRANEBwfDBENAA0FAAAAAAAAAAAAAA==",
    "five": "JgA8AFYfDRANEA0fDR8bEQwRDRANEA0QDREMEQ0QGx8NEA0RDBENEA0QHB8bEA4eDg8NEQwRDRANEBwfGwANBQAAAAAAAAAAAAAAAA==",
    "six": "JgA+AFYfDRANEQwfDR8cEA0QDRANEQwRDRANEA0QHB8NEA0QDRANEQwRGx8bEQ0fDBENEA0QDRANERsQDR8NAA0FAAAAAAAAAAAAAA==",
    "seven": "JgA+AFYfDRANEA0fDh4bEQwRDRANEA0QDREMEQ0QGx8ODw0RDBENEA0QHB8bEA0fDg8NEQwRDRANEBwQDRANAA0FAAAAAAAAAAAAAA==",
    "eight": "JgA+AFUfDREMEQ0fDB8cEA0QDREMEQ0QDRANEA0RGx8ODw0QDRENEA0QGx8cEA0fDRAODw0QDREbHw4PDRANAA0FAAAAAAAAAAAAAA==",
    "nine": "JgA8AFYfDBENEA0fDR8cDw0RDBENEA0QDRANEQwRGx8NEA0RDBENEA0QHB8bEA0fDRANEA0RDBEbHw0QHAANBQAAAAAAAAAAAAAAAA==",
    "zero": "JgBAAFceDg8PDg8dDh4dDg8ODw8ODw8ODw4PDg8PHR0PDg8ODw8ODw8OHR0eDg8dDw4PDg8PDg8PDg8ODw4PDw4ADQUAAAAAAAAAAA==",
}

SUPPORT_FEATURES = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    async_add_entities(
        [
            CDXDevice(
                hass, config_entry.data[CONF_NAME], config_entry.data[CONF_BROADLINK]
            )
        ]
    )

    # Register entity services
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SEND_COMMAND,
        {
            vol.Required("command"): cv.string,
        },
        CDXDevice.send_command.__name__,
    )


class CDXDevice(MediaPlayerEntity):
    # Representation of a Emotiva Processor

    def __init__(self, hass, name, broadlink_entity):
        self._hass = hass
        self._state = MediaPlayerState.IDLE
        self._entity_id = f"media_player.{DOMAIN}"
        self._unique_id = f"{DOMAIN}_" + name.replace(" ", "_").replace(
            "-", "_"
        ).replace(":", "_")
        self._device_class = "receiver"
        self._name = name
        self._broadlink_entity = broadlink_entity

    @property
    def should_poll(self):
        return False

    @property
    def icon(self):
        return "mdi:audio-video"

    @property
    def name(self):
        # return self._device.name
        return None

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
            },
            name=self._name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def entity_id(self):
        return self._entity_id

    @property
    def device_class(self):
        return self._device_class

    @entity_id.setter
    def entity_id(self, entity_id):
        self._entity_id = entity_id

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        return SUPPORT_FEATURES

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

    async def async_media_stop(self) -> None:
        """Send stop command to media player."""
        await self._send_broadlink_command("stop")
        self._state = MediaPlayerState.IDLE
        self.async_schedule_update_ha_state()

    async def async_media_play(self) -> None:
        """Send play command to media player."""
        await self._send_broadlink_command("play")
        self._state = MediaPlayerState.PLAYING
        self.async_schedule_update_ha_state()

    async def async_media_pause(self) -> None:
        """Send pause command to media player."""
        await self._send_broadlink_command("pause")
        self._state = MediaPlayerState.PAUSED
        self.async_schedule_update_ha_state()

    async def async_media_next_track(self) -> None:
        """Send next track command."""
        await self._send_broadlink_command("next")

    async def async_media_previous_track(self) -> None:
        """Send next track command."""
        await self._send_broadlink_command("previous")

    async def async_mute_volume(self, mute: bool) -> None:
        await self._send_broadlink_command("mute")
        self._muted = not self._muted
        self.async_schedule_update_ha_state()

    async def async_volume_up(self):
        await self._send_broadlink_command("volume_up")

    async def async_volume_down(self):
        await self._send_broadlink_command("volume_down")
