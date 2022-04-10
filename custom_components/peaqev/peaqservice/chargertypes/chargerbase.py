import logging
import homeassistant.helpers.template as template

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
            "idle": [],
            "connected": [],
            "charging": []
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

    @servicecalls.setter
    def servicecalls(self, obj):
        assert type(obj) is dict
        self._servicecalls = obj

    def validatecharger(self):
        try:
            assert len(self.chargerentity) > 0
            assert len(self.powermeter) > 0
            assert len(self.powerswitch) > 0
            assert self.servicecalls["domain"] is not None
            assert self.servicecalls["on"] is not None
            assert self.servicecalls["off"] is not None
            assert self.servicecalls["pause"] is not None
            assert self.servicecalls["resume"] is not None
            if self.allowupdatecurrent:
                assert self.servicecalls["updatecurrent"] is not None
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
