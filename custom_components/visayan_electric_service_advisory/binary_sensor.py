"""Binary sensor platform for Visayan Electric Service Advisory."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR, CONF_LOCATIONS
from .coordinator import VECOServiceAdvisoryCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from a config entry."""
    coordinator: VECOServiceAdvisoryCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    async_add_entities([VECOAreaAffectedBinarySensor(coordinator, entry)])


class VECOAreaAffectedBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor that indicates if a configured location is affected."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-outline"

    def __init__(
        self,
        coordinator: VECOServiceAdvisoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_area_affected"
        self._attr_name = "Visayan Electric Area Affected"

    @property
    def is_on(self) -> bool:
        """Return true if any configured location is affected."""
        if self.coordinator.data is None:
            return False

        # Get configured locations from entry data or options
        locations = self._entry.options.get(
            CONF_LOCATIONS,
            self._entry.data.get(CONF_LOCATIONS, [])
        )

        for adv in self.coordinator.data:
            # Skip cancelled advisories
            if adv.get("cancelled"):
                continue

            areas = adv.get("areas_affected", "").lower()
            for loc in locations:
                if loc.lower() in areas:
                    return True

        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return the specific advisories that match the location."""
        if self.coordinator.data is None:
            return {"matching_advisories": []}

        locations = self._entry.options.get(
            CONF_LOCATIONS,
            self._entry.data.get(CONF_LOCATIONS, [])
        )

        matching = []
        for adv in self.coordinator.data:
            if adv.get("cancelled"):
                continue

            areas = adv.get("areas_affected", "").lower()
            is_match = False
            for loc in locations:
                if loc.lower() in areas:
                    is_match = True
                    break
            
            if is_match:
                matching.append(adv)

        return {"matching_advisories": matching}

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
