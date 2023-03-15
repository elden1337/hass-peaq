
from peaqevcore.services.threshold.threshold import Threshold
from peaqevcore.services.threshold.threshold_lite import ThresholdLite


class ThresholdFactory:
    @staticmethod
    def create(hub):
        if hub.options.peaqev_lite:
            return ThresholdLite(hub)
        return Threshold(hub)