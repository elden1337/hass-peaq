from peaqevcore.session_service.session import SessionPrice as _core_session_price

class Session:
    def __init__(self, charger):
        self._charger = charger
        self.core = _core_session_price()
        self.core._set_delta()

    @property
    def session_energy(self):
        return self.core.total_energy

    @session_energy.setter
    def session_energy(self, val):
        self.core.update_power_reading(val)
        self.update_session_pricing()

    @property
    def session_price(self):
        return self.core.total_price

    @session_price.setter
    def session_price(self, val):
        self.core.update_price(val)
        self.update_session_pricing()

    def update_session_pricing(self):
        if self._charger.session_is_active is False:
            self.core.terminate()
