
from peaqevcore.services.threshold.threshold import Threshold
from peaqevcore.services.threshold.threshold_lite import ThresholdLite
from peaqevcore.services.threshold.thresholdbase import ThresholdBase


class ThresholdFactory:
    @staticmethod
    def create(hub) -> ThresholdBase:
        if hub.options.peaqev_lite:
            return ThresholdLite(hub)
        return Threshold(hub)