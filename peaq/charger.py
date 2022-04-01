import time
import logging

_LOGGER = logging.getLogger(__name__)

class Charger():
    def __init__(self, hub, hass, servicecalls : dict):
        self._hass = hass
        self._hub = hub
        self._chargerblocked = False
        self._chargerstart = False
        self._chargerstop = False
        self._servicecalls = servicecalls

    async def Charge(self):
        """g"""
        
        self._chargerblocked = True
        if self._hub.charger_enabled.value == True:
            if self._hub.chargecontroller.status.name == "Start":
                if self._hub.chargerobject_switch.value == "off" and not self._chargerstart: 
                    self.IsRunning(True)
                    await self._hub.hass.services.async_call(self._servicecalls['domain'],self._servicecalls['on'])
                    if self._hub.chargertypedata.charger.allowupdatecurrent:
                        self._hass.async_create_task(self._UpdateMaxCurrent())
            elif self._hub.chargecontroller.status.name == "Stop" or self._hub.charger_done.value or self._hub.chargecontroller.status.name == "Idle":
                if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                    self.IsRunning(False)
                    await self._hub.hass.services.async_call(
                        self._servicecalls['domain'], 
                        self._servicecalls['off']
                        )
        else: 
           if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                self.IsRunning(False)
                await self._hub.hass.services.async_call(self._servicecalls['domain'], self._servicecalls['off'])  
        self._chargerblocked = False

    async def _UpdateMaxCurrent(self):
        """g"""

        result1 = await self._hass.async_add_executor_job(self._Wait1)
        while self._hub.chargerobject_switch.value == "on" and self._chargerstop == False:
            result2 = await self._hass.async_add_executor_job(self._Wait2)
            await self._hub.hass.services.async_call(
                self._servicecalls['domain'], 
                self._servicecalls['updatecurrent']['name'], 
                {self._servicecalls['updatecurrent']['param']: self._hub.threshold.allowedcurrent}
                )
            result3 = await self._hass.async_add_executor_job(self._Wait3)

    def _Wait1(self) -> bool:
        """Wait for the chargerswitch to be turned on before commencing the _UpdateMaxCurrent-method (this is because there is a slight delay between execution and params being set."""

        while self._hub.chargerobject_switch.value == "off" and self._chargerstop == False:
            time.sleep(3)
        return True

    def _Wait2(self) -> bool:
        """Wait for the perceived max current to become different than the currently set one by the charger."""

        while int(self._hub.chargerobject_switch.current) == int(self._hub.threshold.allowedcurrent) and self._chargerstop == False:
                time.sleep(3)
        return True

    def _Wait3(self) -> bool:
        """Wait for a maximum of three minutes or until the charger is switched off or stopped by the script"""

        timer = 180
        starttime = time.time()
        while self._hub.chargerobject_switch.value == "on" and self._chargerstop == False and time.time() - starttime < timer:
            time.sleep(3)
        return True

    def IsRunning(self, determinator: bool):
        if determinator:
            self._chargerstart = True
            self._chargerstop = False
        elif not determinator:
            self._chargerstart = False
            self._chargerstop = True
        