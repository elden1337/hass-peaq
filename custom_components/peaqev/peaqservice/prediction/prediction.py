from datetime import datetime

from peaqevcore.prediction_service.prediction import PredictionBase as _core


class Prediction:
    def __init__(self, hub=None):
        self._hub = hub

    @property
    def predictedenergy(self) -> float:
        return _core.predicted_energy(
            datetime.now().minute,
            datetime.now().second,
            self._hub.powersensormovingaverage.value if self._hub.powersensormovingaverage.value is not None else 0,
            self._hub.totalhourlyenergy.value,
            self._hub.locale.data.is_quarterly(self._hub.locale.data)
        )

    @property
    def predictedpercentageofpeak(self) -> float:
        return _core.predicted_percentage_of_peak(
            self._hub.currentpeak.value,
            self.predictedenergy
        )
