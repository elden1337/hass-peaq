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

    async def charge(self):
        """Main function to turn charging on or off"""

        self._chargerblocked = True
        if self._hub.charger_enabled.value == True:
            if self._hub.chargecontroller.status.name == "Start":
                if self._hub.chargerobject_switch.value == "off" and not self._chargerstart: 
                    self._is_running(True)
                    await self._hub.hass.services.async_call(self._servicecalls['domain'],self._servicecalls['on'])
                    if self._hub.chargertypedata.charger.allowupdatecurrent:
                        self._hass.async_create_task(self._updatemaxcurrent())
            elif self._hub.chargecontroller.status.name == "Stop" or self._hub.charger_done.value or self._hub.chargecontroller.status.name == "Idle":
                if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                    self._is_running(False)
                    await self._hub.hass.services.async_call(
                        self._servicecalls['domain'], 
                        self._servicecalls['off']
                        )
        else: 
           if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                self._is_running(False)
                await self._hub.hass.services.async_call(self._servicecalls['domain'], self._servicecalls['off'])  
        self._chargerblocked = False

    async def _updatemaxcurrent(self):
        """If enabled, let the charger periodically update it's current during charging."""

        result1 = await self._hass.async_add_executor_job(self._wait1)
        while self._hub.chargerobject_switch.value == "on" and self._chargerstop == False:
            result2 = await self._hass.async_add_executor_job(self._wait2)
            if self._servicecalls['updatecurrent']['params']['charger'].len > 0 and self._servicecalls['updatecurrent']['params']['chargerid'].len > 0:
                serviceparams = {
                    self._servicecalls['updatecurrent']['params']['charger']: self._servicecalls['updatecurrent']['params']['chargerid'],
                    self._servicecalls['updatecurrent']['params']['current']: self._hub.threshold.allowedcurrent
                    }
            else:
                serviceparams = {
                    self._servicecalls['updatecurrent']['params']['current']: self._hub.threshold.allowedcurrent
                    }
            await self._hub.hass.services.async_call(
                self._servicecalls['domain'], 
                self._servicecalls['updatecurrent']['name'], 
                serviceparams
                )
            result3 = await self._hass.async_add_executor_job(self._wait3)

    def _wait1(self) -> bool:
        """Wait for the chargerswitch to be turned on before commencing the _UpdateMaxCurrent-method"""

        while self._hub.chargerobject_switch.value == "off" and self._chargerstop == False:
            time.sleep(3)
        return True

    def _wait2(self) -> bool:
        """Wait for the perceived max current to become different than the currently set one by the charger"""

        while int(self._hub.chargerobject_switch.current) == int(self._hub.threshold.allowedcurrent) and self._chargerstop == False:
                time.sleep(3)
        return True

    def _wait3(self) -> bool:
        """Wait for a maximum of three minutes or until the charger is switched off or stopped by the script"""

        timer = 180
        starttime = time.time()
        while self._hub.chargerobject_switch.value == "on" and self._chargerstop == False and time.time() - starttime < timer:
            time.sleep(3)
        return True

    def _is_running(self, determinator: bool):
        if determinator:
            self._chargerstart = True
            self._chargerstop = False
        elif not determinator:
            self._chargerstart = False
            self._chargerstop = True
        