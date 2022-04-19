#from custom_components.peaqev.peaqservice.util.chargerstates import CHARGECONTROLLER
#from custom_components.peaqev.peaqservice.chargecontroller.chargecontroller import ChargeController
#import time

#DONETIMEOUT = 180


class ChargeControllerBase:

    # @staticmethod
    # def _let_charge(
    #     charger_state: str,
    #     charger_enabled: bool,
    #     charger_done: bool,
    #     total_hourly_energy: float,
    #     car_power_sensor: float,
    #     non_hours: list,
    #     now_hour: int,
    #     charger_states: dict
    #     ):
    #
    #     ret = CHARGECONTROLLER.Error
    #     update_timer = False
    #
    #     if charger_state in charger_states[CHARGECONTROLLER.Idle]:
    #         update_timer = True
    #         ret = CHARGECONTROLLER.Idle
    #     elif charger_state in charger_states[CHARGECONTROLLER.Connected] and charger_enabled is False:
    #         update_timer = True
    #         ret = CHARGECONTROLLER.Connected
    #     elif charger_state not in charger_states[CHARGECONTROLLER.Idle] and charger_done is True:
    #         ret = CHARGECONTROLLER.Done
    #     elif now_hour in non_hours:
    #         update_timer = True
    #         ret = CHARGECONTROLLER.Stop
    #     elif charger_state in charger_states[CHARGECONTROLLER.Connected]:
    #         if car_power_sensor < 1 and time.time() - ChargeController.latest_charger_start > DONETIMEOUT:
    #             ret = CHARGECONTROLLER.Done
    #         else:
    #             if ChargeController.below_startthreshold and total_hourly_energy > 0:
    #                 ret = CHARGECONTROLLER.Start
    #             else:
    #                 update_timer = True
    #                 ret = CHARGECONTROLLER.Stop
    #     elif charger_state in charger_states[CHARGECONTROLLER.Charging]:
    #         update_timer = True
    #         if ChargeController.above_stopthreshold and total_hourly_energy > 0:
    #             ret = CHARGECONTROLLER.Stop
    #         else:
    #             ret = CHARGECONTROLLER.Start
    #
    #     if update_timer is True:
    #         ChargeController.update_latestchargerstart()
    #     return ret

    @staticmethod
    def _below_startthreshold(
            predicted_energy: float,
            current_peak: float,
            threshold_start: float
    ) -> bool:
        return (predicted_energy * 1000) < (
                (current_peak * 1000) * (threshold_start / 100))

    @staticmethod
    def _above_stopthreshold(
            predicted_energy: float,
            current_peak: float,
            threshold_stop: float
    ) -> bool:
        return (predicted_energy * 1000) > (
                (current_peak * 1000) * (threshold_stop / 100))