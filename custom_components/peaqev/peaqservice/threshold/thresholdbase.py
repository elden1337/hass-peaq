class ThresholdBase:

    @staticmethod
    def _stop(
              nowmin:int,
              is_cautionhour:bool
              ) -> float:
        if is_cautionhour is True and nowmin < 45:
            ret = (((nowmin+pow(1.075, nowmin)) * 0.0032) + 0.7)
        else:
            ret = (((nowmin + pow(1.071, nowmin)) * 0.00165) + 0.8)
        return round(ret * 100, 2)

    @staticmethod
    def _start(
               nowmin: int,
               is_cautionhour: bool
               ) -> float:
        if is_cautionhour is True and nowmin < 45:
            ret = (((nowmin+pow(1.081, nowmin)) * 0.0049) + 0.4)
        else:
            ret = (((nowmin + pow(1.066, nowmin)) * 0.0045) + 0.5)
        return round(ret * 100, 2)
    
    @staticmethod
    def _allowedcurrent(
            nowmin: int,
            movingavg: float,
            charger_enabled: bool,
            charger_done: bool,
            currentsdict: dict,
            totalenergy: float,
            peak: float
            ) -> int:
        ret = 6
        if charger_enabled is False or charger_done is True or movingavg == 0:
            return ret
        currents = currentsdict
        for key, value in currents.items():
            if ((((movingavg + key) / 60) * (60 - nowmin) + totalenergy * 1000) / 1000) < peak:
                ret = value
                break
        return ret
