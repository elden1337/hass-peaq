from homeassistant.components.sql.sensor import (
    SQLSensor
)
from custom_components.peaqev.const import DOMAIN
import custom_components.peaqev.peaqservice.util.extensionmethods as ex


class PeaqSQLSensor(SQLSensor):
    def __init__(self, hub, sessmaker, query, entry_id):
        self._hub = hub
        self._attr_name = f"{hub.hubname} {query['name']}"
        self._attr_unique_id = f"{DOMAIN}_{self._hub.hub_id}_{ex.nametoid(self._attr_name)}"
        sm = sessmaker
        super().__init__(
            self._attr_name,
            sm,
            query["query"],
            "state",
            "kW",
            None,
            entry_id
            )

    @property
    def icon(self) -> str:
        return "mdi:chart-arc"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._hub.hub_id)}}