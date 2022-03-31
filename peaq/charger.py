import time
import threading
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class Charger():
    def __init__(self, hub, servicecalls : dict):
        self._hub = hub
        self._chargerblocked = False
        self._chargerstart = False
        self._chargerstop = False
        self._servicecalls = servicecalls

    async def Charge(self):
        update_current = threading.Thread(target=self._Prepare_Event_Loop)
        self._chargerblocked = True
        if self._hub.charger_enabled.value:
            if self._hub.chargecontroller.status.name == "Start":
                if self._hub.chargerobject_switch.value == "off" and not self._chargerstart: 
                    self.IsRunning(True)
                    await self._hub.hass.services.async_call(self._servicecalls['domain'],self._servicecalls['on'])
                    if self._hub.chargertypedata.allowupdatecurrent:
                        update_current.run()
            elif self._hub.chargecontroller.status.name == "Stop" or self._hub.charger_done.value or self._hub.chargecontroller.status.name == "Idle":
                if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                    self.IsRunning(False)
                    await self._hub.hass.services.async_call(
                        self._servicecalls['domain'], 
                        self._servicecalls['off']
                        )
                    if self._hub.chargertypedata.allowupdatecurrent:                        
                        if update_current.is_alive:
                            update_current.join()
        else: 
           if self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
                self.IsRunning(False)
                await self._hub.hass.services.async_call(self._servicecalls['domain'], self._servicecalls['off'])  
                if self._hub.chargertypedata.allowupdatecurrent:
                    if update_current.is_alive:
                        update_current.join()
        self._chargerblocked = False

    def _Prepare_Event_Loop(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._UpdateMaxCurrent())
        loop.close()

    async def _UpdateMaxCurrent(self):
        while self._hub.chargerobject_switch.value == "on" and not self._chargerstop:
            while self._hub.chargerobject_switch.current == self._hub.threshold.allowedcurrent:
                time.sleep(3)
            _LOGGER.info("updating max current", self._hub.threshold.allowedcurrent)
            await self._hub.hass.services.async_call(
                self._servicecalls['domain'], 
                self._servicecalls['updatecurrent']['name'], 
                {f"{self._servicecalls['updatecurrent']['param']}: {self._hub.threshold.allowedcurrent}"}
                )
            time.sleep(180)

    def IsRunning(self, determinator: bool):
        if determinator:
            self._chargerstart = True
            self._chargerstop = False
        elif not determinator:
            self._chargerstart = False
            self._chargerstop = True
        