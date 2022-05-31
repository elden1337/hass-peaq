import logging

import homeassistant.helpers.template as template
from peaqevcore.Models import CHARGERSTATES

from custom_components.peaqev.peaqservice.chargertypes.calltype import CallType
from custom_components.peaqev.peaqservice.chargertypes.servicecalls import ServiceCalls

_LOGGER = logging.getLogger(__name__)


class ChargerBase:
    def __init__(self, hass):
        self._hass = hass
        self._chargerEntity = None
        self._powermeter = None
        self.powermeter_factor = 1
        self._powerswitch = None
        self.ampmeter = None
        self.ampmeter_is_attribute = None
        self._servicecalls = None
        self._chargerstates = {
            CHARGERSTATES.Idle: [],
            CHARGERSTATES.Connected: [],
            CHARGERSTATES.Charging: [],
            CHARGERSTATES.Done: []
        }
        self._entityschema = ""
        self._entities = None

    @property
    def chargerstates(self) -> dict:
        return self._chargerstates

    @property
    def powermeter(self):
        return self._powermeter

    @powermeter.setter
    def powermeter(self, val):
        assert isinstance(val, str)
        self._powermeter = val

    @property
    def powerswitch(self):
        return self._powerswitch

    @powerswitch.setter
    def powerswitch(self, val):
        assert isinstance(val, str)
        self._powerswitch = val

    @property
    def chargerentity(self):
        return self._chargerentity

    @chargerentity.setter
    def chargerentity(self, val):
        assert isinstance(val, str)
        self._chargerentity = val

    @property
    def servicecalls(self):
        return self._servicecalls

    @property
    def native_chargerstates(self) -> list:
        return self._native_chargerstates

    def _set_servicecalls(
            self,
            domain: str,
            on_call: CallType,
            off_call: CallType,
            pause_call: CallType = None,
            resume_call: CallType = None,
            allowupdatecurrent: bool = False,
            update_current_call: str = None,
            update_current_params: dict = None
    ) -> None:
        self._servicecalls = ServiceCalls(
            domain,
            on_call,
            off_call,
            pause_call,
            resume_call,
            allowupdatecurrent,
            update_current_call,
            update_current_params
        )

    def validatecharger(self):
        try:
            assert len(self.chargerentity) > 0
            assert len(self.powermeter) > 0
            assert len(self.powerswitch) > 0
            assert self.servicecalls.domain is not None
            assert self.servicecalls.on is not None
            assert self.servicecalls.off is not None
            assert self.servicecalls.pause is not None
            assert self.servicecalls.resume is not None
            if self.servicecalls.allowupdatecurrent is True:
                assert self.servicecalls.update_current.call is not None
        except Exception as e:
            msg = f"Peaqev could not initialize charger: {e}"
            _LOGGER.error(msg)
        debugprint = {
            "chargerentity": self.chargerentity,
            "powermeter": self.powermeter,
            "powermeter_factor": self.powermeter_factor,
            "powerswitch": self.powerswitch,
            "ampmeter": self.ampmeter,
            "ampmeter_is_attribute": self.ampmeter_is_attribute,
            "servicecalls_on": self.servicecalls.on,
            "servicecalls_off": self.servicecalls.off,
            "servicecalls_resume": self.servicecalls.resume,
            "servicecalls_pause": self.servicecalls.pause,
            "updatecurrent": self.servicecalls.update_current.call
        }
        _LOGGER.info(debugprint)

    def getentities(self, domain: str, endings: list):
        entities = template.integration_entities(self._hass, domain)

        if len(entities) < 1:
            _LOGGER.error("no entities!")
        else:
            _endings = endings
            namelrg = entities[0].split(".")
            candidate = ""

            for e in _endings:
                if namelrg[1].endswith(e):
                    candidate = namelrg[1].replace(e, '')

            self._entityschema = candidate
            self._entities = entities
