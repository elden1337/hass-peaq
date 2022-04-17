import logging
import homeassistant.helpers.template as template
from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
from custom_components.peaqev.peaqservice.chargertypes.servicecalls import ServiceCalls
_LOGGER = logging.getLogger(__name__)


class ChargerBase:
    def __init__(self, hass):
        self._hass = hass
        self._chargerEntity = None
        self._powermeter = None
        self._powerswitch = None
        self.ampmeter = None
        self.ampmeter_is_attribute = None
        self._servicecalls = None
        self._chargerstates = {
            CHARGECONTROLLER.Idle: [],
            CHARGECONTROLLER.Connected: [],
            CHARGECONTROLLER.Charging: []
        }
        self._entityschema = ""

    @property
    def chargerstates(self) -> dict:
        return self._chargerstates

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
    def servicecalls(self):
        return self._servicecalls

    def _set_servicecalls(
            self,
            domain: str,
            on_call: str,
            off_call: str,
            pause_call: str = None,
            resume_call: str = None,
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
            _LOGGER.error("Peaqev could not initialize charger", e)

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
