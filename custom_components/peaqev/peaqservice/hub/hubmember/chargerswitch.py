import logging

from custom_components.peaqev.peaqservice.hub.hubmember.hubmember import HubMember

_LOGGER = logging.getLogger(__name__)


class ChargerSwitch(HubMember):
    def __init__(
            self,
            hass,
            data_type: type,
            listenerentity,
            initval,
            currentname: str,
            ampmeter_is_attribute: bool,
            hubdata=None
    ):
        self._hubdata = hubdata
        self._hass = hass
        self._value = initval
        self._current = 0
        self._current_attr_name = currentname
        self._ampmeter_is_attribute = ampmeter_is_attribute
        super().__init__(data_type, listenerentity, initval)

    @property
    def is_initialized(self) -> bool:
        if not self._hubdata.chargerobject.is_initialized:
            return False
        return super().is_initialized

    @property
    def current(self) -> int:
        if self._current == 0:
            return 6
        return self._current

    @current.setter
    def current(self, value):
        try:
            self._current = int(value)
        except ValueError as v:
            msg = f"[{value}] could not set value as chargercurrent. {v}"
            _LOGGER.error(msg)

    def updatecurrent(self):
        if self._ampmeter_is_attribute is True:
            ret = self._hass.states.get(self.entity)
            if ret is not None:
                ret_attr = str(ret.attributes.get(self._current_attr_name))
                self.current = ret_attr
            else:
                _LOGGER.error("chargerobject state was none")
        else:
            ret = self._hass.states.get(self._current_attr_name)
            if ret is not None:
                self.current = ret.state
            else:
                _LOGGER.error("chargerobject state was none")
