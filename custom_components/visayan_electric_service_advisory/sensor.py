"""Sensor platform for Visayan Electric Service Advisory."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    """Set up sensor and button entities from a config entry."""
    coordinator: VECOServiceAdvisoryCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    
    # Add only the advisory count sensor
    async_add_entities([
        VECOAdvisoryCountSensor(coordinator, entry),
    ])




class VECOAdvisoryCountSensor(CoordinatorEntity, SensorEntity):
    """Sensor that reports the total number of parsed service advisories from the latest post."""

    _attr_icon = "mdi:lightning-bolt"
    _attr_native_unit_of_measurement = "advisories"

    def __init__(
        self,
        coordinator: VECOServiceAdvisoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_advisory_count"
        self._attr_name = "Visayan Electric Service Advisories"

    @property
    def native_value(self) -> int:
        """Return number of advisories."""
        if self.coordinator.data is None:
            return 0
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        """Return all advisories as attributes."""
        if self.coordinator.data is None:
            return {"advisories": []}

        return {
            "advisories": [
                {
                    "date": adv["date"],
                    "time": adv["time"],
                    "duration": adv["duration"],
                    "cancelled": adv["cancelled"],
                    "purpose": adv["purpose"],
                    "areas_affected": adv["areas_affected"],
                    "map": adv["map"],
                    "post_url": adv["post_url"],
                    "post_title": adv["post_title"],
                }
                for adv in self.coordinator.data
            ]
        }

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Visayan Electric Service Advisory",
            "manufacturer": "Visayan Electric Company",
            "model": "Service Advisory Scraper",
            "entry_type": "service",
        }
