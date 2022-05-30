from custom_components.peaqev.peaqservice.util.constants import CALL, SWITCH


class CallType:
    def __init__(self, call: str, params: dict = {}, call_type: str = CALL):
        self._call = call
        self._params = params
        self._call_type = call_type

    @property
    def call(self) -> str:
        return self._call

    @property
    def params(self) -> dict:
        return self._params

    @property
    def call_type(self) -> str:
        return self._call_type
