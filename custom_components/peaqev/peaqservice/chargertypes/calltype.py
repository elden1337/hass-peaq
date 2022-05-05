
class CallType:
    def __init__(self, call: str, params: dict = {}):
        self._call = call
        self._params = params

    @property
    def call(self) -> str:
        return self._call

    @property
    def params(self) -> dict:
        return self._params