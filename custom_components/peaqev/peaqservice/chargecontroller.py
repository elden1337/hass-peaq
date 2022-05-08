import logging
import time
from datetime import datetime
from peaqevcore.Chargecontroller import ChargeControllerBase
from peaqevcore.Models import CHARGERSTATES
from custom_components.peaqev.peaqservice.util.constants import CHARGERCONTROLLER

_LOGGER = logging.getLogger(__name__)
DONETIMEOUT = 180


class ChargeController:
    def __init__(self, hub):
        self._hub = hub
        self.name = f"{self._hub.hubname} {CHARGERCONTROLLER}"
        self._status = CHARGERSTATES.Idle
        self._latestchargerstart = time.time()
        self._core = ChargeControllerBase(charger_state_translation=self._hub.chargertype.charger.chargerstates)

    @property
    def latest_charger_start(self) -> float:
        return self._latestchargerstart

    @latest_charger_start.setter
    def latest_charger_start(self, val):
        self._latestchargerstart = val

    @property
    def below_startthreshold(self) -> bool:
        return self._core.below_start_threshold(
            predicted_energy=self._hub.prediction.predictedenergy,
            current_peak=self._hub.current_peak_dynamic,
            threshold_start=self._hub.threshold.start/100
        )

    @property
    def above_stopthreshold(self) -> bool:
        return self._core.above_stop_threshold(
            predicted_energy=self._hub.prediction.predictedenergy,
            current_peak=self._hub.current_peak_dynamic,
            threshold_stop=self._hub.threshold.stop/100
        )

    @property
    def status(self):
        return self._get_status()

    def update_latestchargerstart(self):
        self.latest_charger_start = time.time()

    def _get_status(self):
        ret = CHARGERSTATES.Error
        update_timer = False
        charger_state = self._hub.chargerobject.value.lower()
        free_charge = self._hub.locale.data.free_charge

        #hax for easee. fix dict-type completed in CHARGERSTATES generic dict
        if charger_state == "completed":
            self._hub.charger_done.value = True
            ret = CHARGERSTATES.Done
        # hax for easee. fix dict-type completed in CHARGERSTATES generic dict
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle]:
            update_timer = True
            ret = CHARGERSTATES.Idle
            if self._hub.charger_done.value is True:
                self._hub.charger_done.value = False
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Connected] and self._hub.charger_enabled.value is False:
            update_timer = True
            ret = CHARGERSTATES.Connected
        elif charger_state not in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Idle] and self._hub.charger_done.value is True:
            ret = CHARGERSTATES.Done
        elif datetime.now().hour in self._hub.hours.non_hours and free_charge is False:
            update_timer = True
            ret = CHARGERSTATES.Stop
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Connected]:
            if self._hub.carpowersensor.value < 1 and time.time() - self.latest_charger_start > DONETIMEOUT:
                ret = CHARGERSTATES.Done
            else:
                if (self.below_startthreshold and self._hub.totalhourlyenergy.value > 0) or free_charge is True:
                    ret = CHARGERSTATES.Start
                else:
                    update_timer = True
                    ret = CHARGERSTATES.Stop
        elif charger_state in self._hub.chargertype.charger.chargerstates[CHARGERSTATES.Charging]:
            update_timer = True
            if self.above_stopthreshold and self._hub.totalhourlyenergy.value > 0 and free_charge is False:
                ret = CHARGERSTATES.Stop
            else:
                ret = CHARGERSTATES.Start

        if update_timer is True:
            self.update_latestchargerstart()
        return ret


