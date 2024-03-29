import logging

from peaqevcore.common.models.observer_types import ObserverTypes

_LOGGER = logging.getLogger(__name__)

class HubSettersMixin:
    async def async_set_init_dict(self, init_dict, override: bool = False) -> None:
        await self.sensors.locale.data.query_model.peaks.async_set_init_dict(init_dict, override=override)
        try:
            ff = getattr(self.sensors.locale.data.query_model.peaks, "export_peaks", {})
            _LOGGER.debug(f"intialized_peaks: {ff}")
        except Exception:
            pass

    async def async_set_chargerobject_value(self, value) -> None:
        if hasattr(self.sensors, "chargerobject"):
            setattr(self.sensors.chargerobject, "value", value)

    async def async_update_peak(self, val) -> None:
        await self.sensors.locale.async_try_update_peak(
            new_val=val[0], timestamp=val[1]
        )
        checkval = self.sensors.current_peak.value
        self.sensors.current_peak.value = (
            list(self.sensors.locale.data.query_model.peaks.p.values())
        )
        if checkval != self.sensors.current_peak.value:
            _LOGGER.info("observed peak updated to %s", self.sensors.current_peak.value)

    async def async_update_charger_done(self, val):
        setattr(self.sensors.charger_done, "value", bool(val))

    async def async_update_charger_enabled(self, val):
        await self.observer.async_broadcast(ObserverTypes.UpdateLatestChargerStart)
        if hasattr(self.sensors, "charger_enabled"):
            setattr(self.sensors.charger_enabled, "value", bool(val))
        else:
            raise Exception("Peaqev cannot function without a charger_enabled entity")