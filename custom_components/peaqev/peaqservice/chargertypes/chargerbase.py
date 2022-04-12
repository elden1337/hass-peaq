import logging
import homeassistant.helpers.template as template
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.util.constants import (
    CHARGERTYPEHELPERS_DOMAIN,
    CHARGERTYPEHELPERS_ON,
    CHARGERTYPEHELPERS_OFF,
    CHARGERTYPEHELPERS_PAUSE,
    CHARGERTYPEHELPERS_RESUME,
    CHARGERTYPEHELPERS_UPDATECURRENT,
    CHARGERTYPEHELPERS_NAME,
    CHARGERTYPEHELPERS_PARAMS,
)
_LOGGER = logging.getLogger(__name__)


class ChargerBase():
    def __init__(self, hass, currentupdate: bool):
        self._hass = hass
        self._chargerEntity = None
        self._powermeter = None
        self._powerswitch = None
        self._allowupdatecurrent = currentupdate
        self.ampmeter = None
        self.ampmeter_is_attribute = None
        self._servicecalls = {}
        self._chargerstates = {
            CHARGECONTROLLER.Idle: [],
            CHARGECONTROLLER.Connected: [],
            CHARGECONTROLLER.Charging: []
        }
        self._entityschema = ""

    @property
    def chargerstates(self) -> dict:
        return self._chargerstates

    @property
    def allowupdatecurrent(self) -> bool:
        return self._allowupdatecurrent

    """Power meter"""
    @property
    def powermeter(self):
        return self._powermeter

    @powermeter.setter
    def powermeter(self, val):
        assert type(val) is str
        self._powermeter = val

    """Power Switch"""
    @property
    def powerswitch(self):
        return self._powerswitch

    @powerswitch.setter
    def powerswitch(self, val):
        assert type(val) is str
        self._powerswitch = val

    """Charger entity"""
    @property
    def chargerentity(self):
        return self._chargerentity

    @chargerentity.setter
    def chargerentity(self, val):
        assert type(val) is str
        self._chargerentity = val

    """Service calls"""
    @property
    def servicecalls(self) -> dict:
        return self._servicecalls

    def _set_servicecalls(
            self,
            domain: str,
            on_call: str,
            off_call: str,
            pause_call: str = None,
            resume_call: str = None,
            update_current_call: str = None,
            update_current_params: dict = None
    ) -> None:
        self._servicecalls = {
                CHARGERTYPEHELPERS_DOMAIN: domain,
                CHARGERTYPEHELPERS_ON: on_call,
                CHARGERTYPEHELPERS_OFF: off_call,
                CHARGERTYPEHELPERS_PAUSE: pause_call if pause_call is not None else off_call,
                CHARGERTYPEHELPERS_RESUME: resume_call if resume_call is not None else on_call,
                CHARGERTYPEHELPERS_UPDATECURRENT: {
                    CHARGERTYPEHELPERS_NAME: update_current_call,
                    CHARGERTYPEHELPERS_PARAMS: update_current_params
                }
            }

    def validatecharger(self):
        try:
            assert len(self.chargerentity) > 0
            assert len(self.powermeter) > 0
            assert len(self.powerswitch) > 0
            assert self.servicecalls[CHARGERTYPEHELPERS_DOMAIN] is not None
            assert self.servicecalls[CHARGERTYPEHELPERS_ON] is not None
            assert self.servicecalls[CHARGERTYPEHELPERS_OFF] is not None
            assert self.servicecalls[CHARGERTYPEHELPERS_PAUSE] is not None
            assert self.servicecalls[CHARGERTYPEHELPERS_RESUME] is not None
            if self.allowupdatecurrent:
                assert self.servicecalls[CHARGERTYPEHELPERS_UPDATECURRENT] is not None
        except Exception as e:
            _LOGGER.error("Peaqev could not initialize charger", e)

    def getentities(self, domain:str, endings:list):
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

