from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.calltype_enum import CallTypes
from custom_components.peaqev.peaqservice.chargertypes.const import (
    COMMAND,
    PARAMETERS)

REQUIRED_CALLTYPES = [CallTypes.On, CallTypes.Off]


class IChargerTypeCalls:
    def __init__(self, schema):
        self._call_on: CallType = None
        self._call_off: CallType = None
        self._call_resume: CallType = None
        self._call_pause: CallType = None
        self._call_update_current: CallType = None
        self._setup(schema)
        self._validate()

    @property
    def call_on(self) -> CallType:
        return self._call_on

    @property
    def call_off(self) -> CallType:
        return self._call_off

    @property
    def call_resume(self) -> CallType:
        return self._call_resume

    @property
    def call_pause(self) -> CallType:
        return self._call_pause

    @property
    def call_update_current(self) -> CallType:
        return self._call_update_current

    def _setup(self, schema: dict) -> None:
        assert all(REQUIRED_CALLTYPES in schema.keys()), f"Missing required calltypes: {REQUIRED_CALLTYPES}"

        CALLTYPES_CALL = {
            CallTypes.On: self._call_on,
            CallTypes.Off: self._call_off,
            CallTypes.Pause: self._call_pause,
            CallTypes.Resume: self._call_resume,
            CallTypes.UpdateCurrent: self._call_update_current
            }
        
        for k, v in schema.items():
            _type = self.__create_calltype(v)
            CALLTYPES_CALL[k] = _type  

    def __create_calltype(self, calltype: dict) -> CallType:
        return CallType(call=calltype.get(COMMAND), params=calltype.get(PARAMETERS))

    def _validate(self) -> bool:
        return True
    
    def _get_call_type(self, call: CallTypes) -> CallType:
        _callsdict = {
            CallTypes.On: self.on,
            CallTypes.Off: self.off,
            CallTypes.Pause: self.pause,
            CallTypes.Resume: self.resume,
            CallTypes.UpdateCurrent: self.update_current
        }
        return _callsdict.get(call)
