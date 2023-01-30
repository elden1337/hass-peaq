import logging

from peaqevcore.models.chargecontroller_states import ChargeControllerStates
from peaqevcore.services.chargecontroller.chargecontrollerbase import ChargeControllerBase as _core

from custom_components.peaqev.peaqservice.chargecontroller.chargecontrollerbase import ChargeControllerBase

_LOGGER = logging.getLogger(__name__)


class ChargeController(ChargeControllerBase):
    def __init__(self, hub):
        super().__init__(hub)
        self._hub = hub
        self._core = _core(charger_state_translation=self._hub.chargertype.charger.chargerstates)

    @property
    def below_startthreshold(self) -> bool:
        return self._core._below_start_threshold(
            predicted_energy=self._hub.prediction.predictedenergy,
            current_peak=self._hub.current_peak_dynamic,
            threshold_start=self._hub.threshold.start/100
        )

    @property
    def above_stopthreshold(self) -> bool:
        return self._core._above_stop_threshold(
            predicted_energy=self._hub.prediction.predictedenergy,
            current_peak=self._hub.current_peak_dynamic,
            threshold_stop=self._hub.threshold.stop/100
        )

    def __get_status_charging(self) -> ChargeControllerStates:
        if not self._hub.power_canary.alive:
            return ChargeControllerStates.Stop
        if self.above_stopthreshold and self._hub.sensors.totalhourlyenergy.value > 0 and self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data) is False:
            return ChargeControllerStates.Stop
        return ChargeControllerStates.Start

    def __get_status_connected(self, charger_state=None) -> ChargeControllerStates:
        if charger_state is not None and self._hub.sensors.carpowersensor.value < 1 and self.__is_done(charger_state):
            ret = ChargeControllerStates.Done
        else:
            if (self.below_startthreshold and self._hub.sensors.totalhourlyenergy.value != 0) or self._hub.sensors.locale.data.free_charge(self._hub.sensors.locale.data) is True:
                ret = ChargeControllerStates.Start
            else:
                ret = ChargeControllerStates.Stop
        return ret
