"""Button platform for Visayan Electric Service Advisory."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR
from .coordinator import VECOServiceAdvisoryCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities from a config entry."""
    coordinator: VECOServiceAdvisoryCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    
    async_add_entities([
        ManualScrapeButton(coordinator, entry),
    ])


class ManualScrapeButton(CoordinatorEntity, ButtonEntity):
    """Button to manually trigger a scrape of the latest advisory."""

    _attr_icon = "mdi:refresh"
    _attr_name = "Visayan Electric Manual Scrape"

    def __init__(self, coordinator: VECOServiceAdvisoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_manual_scrape"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Visayan Electric Service Advisory",
            "manufacturer": "Visayan Electric Company",
            "model": "Service Advisory Scraper",
            "entry_type": "service",
        }

    async def async_press(self) -> None:
        """Handle the button press – force a refresh of the coordinator."""
        await self.coordinator.async_refresh()
