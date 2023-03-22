from peaqevcore.models.chargertype.calltype import CallType
from peaqevcore.models.chargertype.calltype_enum import CallTypes

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
        self._call_on = schema.get(CallTypes.On)
        self._call_off = schema.get(CallTypes.Off)
        self._call_pause = schema.get(CallTypes.Pause, schema.get(CallTypes.Off, None))
        self._call_resume = schema.get(CallTypes.Resume, schema.get(CallTypes.On, None))
        self._call_update_current = schema.get(CallTypes.UpdateCurrent, None)

    def _validate(self) -> bool:
        return True
