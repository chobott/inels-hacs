"""iNELS binary sensor entity."""
from __future__ import annotations

from dataclasses import dataclass

from inelsmqtt.devices import Device

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .entity import InelsHacsBaseEntity
from .const import (
    DEVICES,
    DOMAIN,
    ICON_BINARY_INPUT,
    ICON_CARD_PRESENT,
    ICON_HEAT_WAVE,
    ICON_PROXIMITY,
    ICON_SNOWFLAKE,
    LOGGER,
    OLD_ENTITIES,
)


# BINARY SENSOR PLATFORM
@dataclass
class InelsHacsBinarySensorType:
    """Binary sensor type property description"""

    name: str
    icon: str = None
    is_binary_input: bool = False
    indexed: bool = False
    device_class: BinarySensorDeviceClass = None


INELS_HACS_BINARY_SENSOR_TYPES: dict[str, InelsHacsBinarySensorType] = {
    "low_battery": InelsHacsBinarySensorType(
        name="Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    "prox": InelsHacsBinarySensorType(
        name="Proximity Sensor",
        icon=ICON_PROXIMITY,
        device_class=BinarySensorDeviceClass.MOVING,
    ),
    "input": InelsHacsBinarySensorType(
        name="Binary input sensor",
        icon=ICON_BINARY_INPUT,
        is_binary_input=True,
        indexed=True,
    ),
    "heating_out": InelsHacsBinarySensorType(
        name="Heating",
        icon=ICON_HEAT_WAVE,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    "cooling_out": InelsHacsBinarySensorType(
        name="Cooling",
        icon=ICON_SNOWFLAKE,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    "detected": InelsHacsBinarySensorType(
        name="Detector",
    ),
    "tamper": InelsHacsBinarySensorType(
        name="Tamper",
        device_class=BinarySensorDeviceClass.TAMPER,
    ),
    "motion": InelsHacsBinarySensorType(
        name="Motion detector",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    "flooded": InelsHacsBinarySensorType(
        name="Flooded",
        device_class=BinarySensorDeviceClass.MOISTURE,
    ),
    "card_present": InelsHacsBinarySensorType(
        name="Card present",
        icon=ICON_CARD_PRESENT,
        device_class=BinarySensorDeviceClass.OCCUPANCY,
    ),
}


@dataclass
class InelsHacsBinarySensorEntityDescriptionMixin:
    """Mixin keys."""


@dataclass
class InelsHacsBinarySensorEntityDescription(
    BinarySensorEntityDescription, InelsHacsBinarySensorEntityDescriptionMixin
):
    """Class for describing binary sensor iNELS entities."""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Load iNELS binary sensor."""
    device_list: list[Device] = hass.data[DOMAIN][config_entry.entry_id][DEVICES]
    old_entities: list[str] = hass.data[DOMAIN][config_entry.entry_id][
        OLD_ENTITIES
    ].get(Platform.BINARY_SENSOR)

    items = INELS_HACS_BINARY_SENSOR_TYPES.items()
    entities: list[InelsHacsBaseEntity] = []
    for device in device_list:
        for key, type_dict in items:
            if hasattr(device.state, key):
                if type_dict.is_binary_input:
                    binary_sensor_type = InelsHacsBinaryInputSensor
                else:
                    binary_sensor_type = InelsHacsBinarySensor

                if not type_dict.indexed:
                    entities.append(
                        binary_sensor_type(
                            device=device,
                            key=key,
                            index=-1,
                            description=InelsHacsBinarySensorEntityDescription(
                                key=key,
                                name=type_dict.name,
                                icon=type_dict.icon,
                                device_class=type_dict.device_class,
                            ),
                        )
                    )
                else:
                    for k in range(len(device.state.__dict__[key])):
                        entities.append(
                            binary_sensor_type(
                                device=device,
                                key=key,
                                index=k,
                                description=InelsHacsBinarySensorEntityDescription(
                                    key=f"{key}{k}",
                                    name=f"{type_dict.name} {k+1}",
                                    icon=type_dict.icon,
                                    device_class=type_dict.device_class,
                                ),
                            )
                        )

    async_add_entities(entities, True)

    if old_entities:
        for entity in entities:
            if entity.entity_id in old_entities:
                old_entities.pop(old_entities.index(entity.entity_id))

    hass.data[DOMAIN][config_entry.entry_id][Platform.BINARY_SENSOR] = old_entities


class InelsHacsBinarySensor(InelsHacsBaseEntity, BinarySensorEntity):
    """The platform class for binary sensors for home assistant."""

    entity_description: InelsHacsBinarySensorEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsHacsBinarySensorEntityDescription,
    ) -> None:
        """Initialize a binary sensor."""
        super().__init__(device=device, key=key, index=index)

        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.BINARY_SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

    @property
    def unique_id(self) -> str | None:
        """Return unique_id of the entity."""
        return super().unique_id

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return super().name

    @property
    def is_on(self) -> bool | None:
        """Return true is sensor is on."""
        if self.index != -1:
            return self._device.values.ha_value.__dict__[self.key][self.index]

        return self._device.values.ha_value.__dict__[self.key]


class InelsHacsBinaryInputSensor(InelsHacsBaseEntity, BinarySensorEntity):
    """The platform class for binary sensors of binary values for home assistant."""

    entity_description: InelsHacsBinarySensorEntityDescription

    def __init__(
        self,
        device: Device,
        key: str,
        index: int,
        description: InelsHacsBinarySensorEntityDescription,
    ) -> None:
        """Initialize a binary sensor."""
        super().__init__(
            device=device,
            key=key,
            index=index,
        )

        self.entity_description = description

        self._attr_unique_id = slugify(f"{self._attr_unique_id}_{description.key}")
        self.entity_id = f"{Platform.BINARY_SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"{self._attr_name} {description.name}"

    @property
    def available(self) -> bool:
        """Return availability of device."""

        val = self._device.values.ha_value.__dict__[self.key]
        last_val = self._device.last_values.ha_value.__dict__[self.key]
        if self.index != -1:
            val = val[self.index]
            last_val = last_val[self.index]

        if val in [0, 1]:
            return True
        if last_val != val:
            if val == 2:
                LOGGER.warning("%s ALERT", self._attr_unique_id)
            elif val == 3:
                LOGGER.warning("%s TAMPER", self._attr_unique_id)
        return False

    @property
    def unique_id(self) -> str | None:
        """Return unique_id of the entity."""
        return super().unique_id

    @property
    def name(self) -> str | None:
        """Return name of the entity."""
        return super().name

    @property
    def is_on(self) -> bool | None:
        """Return true is sensor is on."""
        if self.index != -1:
            return self._device.values.ha_value.__dict__[self.key][self.index] == 1
        return self._device.values.ha_value.__dict__[self.key] == 1
