MAINS_THRESHOLD = 0.9

class PowerOrchestrator:
    def __init(self, hub):
        self._hub = hub
        self._fuse_max = hub.options.fuse_max
        self._current_amps: int = 0
        self._current_car_power: int = 0
        self._current_total_power: int = 0
        self._threephase_amps: dict = {}

    @property
    def threephase_amps(self) -> dict:
        return self._threephase_amps

    @property
    def alive(self) -> bool:
        """if returns false no charging can be conducted"""
        return False

    def allow_adjustment(self, new_amps:int) -> bool:
        """this method returns true if the desired adjustment 'new_amps' is not breaching threshold"""
        return False


    def _set_allowed_threephase_amps(self) -> dict:
        #only allow amps 16-32 threephase if user has set this value high enough
        pass

    """
    1 if trying to raise amps and they would hit mains-treshold, dont raise
    2 if approaching mains-threshold on current amps. Lower if possible, else turn off
    3 only allow amps 16-32 threephase if user has set this value high enough
    """