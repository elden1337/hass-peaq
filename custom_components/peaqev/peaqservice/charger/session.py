from peaqevcore.session_service.session import SessionPrice as _core_session_price

class Session:
    def __init__(self, charger):
        self._charger = charger
        self._session_data = self._init_session_data()
        self.session_price = 0
        self.session_energy = 0

    def _init_session_data(self):
        s = _core_session_price()
        s._set_delta()
        return s

    @property
    def session_data(self):
        return self._session_data

    @property
    def session_energy(self):
        return self._session_energy

    @session_energy.setter
    def session_energy(self, val):
        self._session_price = val

    @property
    def session_price(self):
        return self._session_price

    @session_price.setter
    def session_price(self, val):
        self._session_price = val

    def update_session_pricing(self):
        if self._charger._session_is_active is False:
            self._session_price.terminate()
        else:
            status = self._session_price.get_status()
            self.session_price = float(status["price"])
            self.session_energy = float(status["energy"]["value"])
