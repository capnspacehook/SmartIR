import logging
from homeassistant.components.button import ButtonEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the helper button platform."""

    if discovery_info is None:
        return

    _LOGGER.debug(f"Setup button platform {discovery_info}")
    async_add_entities(
        [
            SmartIRClimateButton(
                discovery_info["climate"],
                discovery_info["action"],
            )
        ]
    )


class SmartIRClimateButton(ButtonEntity):
    def __init__(self, parent, action):
        _LOGGER.debug(f"Create button {action} for SmartIRClimate {parent._name}")
        self.hass = parent.hass
        self._parent = parent
        self._action = action
        self._unique_id = f"{self._parent._unique_id}_{action}"
        self._name = f"{self._parent._name} {action}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the button."""
        return self._name

    async def async_press(self) -> None:
        _LOGGER.debug(f"Button {self._name} pressed")
        await self._parent.send_command(self._action)
        self.async_write_ha_state()
