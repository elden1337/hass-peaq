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
        #update_current = threading.Thread(target=self._Prepare_Event_Loop)
        self._chargerblocked = True
        if self._hub.charger_enabled.value == True:
            if self._hub.chargecontroller.status.name == "Start":
                if self._hub.chargerobject_switch.value == "off" and not self._chargerstart: 
                    self.IsRunning(True)
                    await self._hub.hass.services.async_call(self._servicecalls['domain'],self._servicecalls['on'])
                    if self._hub.chargertypedata.charger.allowupdatecurrent:
                        #update_current.run()
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
        result1 = await self._hass.async_add_executor_job(self.wait1)
        while self._hub.chargerobject_switch.value == "on" and self._chargerstop == False:
            result2 = await self._hass.async_add_executor_job(self.wait2)
            await self._hub.hass.services.async_call(
                self._servicecalls['domain'], 
                self._servicecalls['updatecurrent']['name'], 
                {self._servicecalls['updatecurrent']['param']: self._hub.threshold.allowedcurrent}
                )
            result3 = await self._hass.async_add_executor_job(self.wait3)

    def wait1(self) -> bool:
        while self._hub.chargerobject_switch.value == "off" and self._chargerstop == False:
            time.sleep(3)
        return True

    def wait2(self) -> bool:
        while int(self._hub.chargerobject_switch.current) == int(self._hub.threshold.allowedcurrent):
                time.sleep(3)
        return True

    def wait3(self) -> bool:
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
        