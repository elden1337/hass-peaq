

class Charger():
    def __init__(self, hub):
        self._hub = hub
        self.chargerblocked = False
        self.chargerstart = False
        self.chargerstop = False

    async def Charge(self, domain:str, call_on:str, call_off:str):
        self.chargerblocked = True
        if self._hub.charger_enabled.value:
            if self._hub.chargecontroller.status.name == "Start":
                if not self._hub.chargerobject_switch.value and not self.chargerstart: 
                    self.chargerstart = True
                    self.chargerstop = False
                    await self._hub.hass.services.async_call(domain,call_on)
            elif self._hub.chargecontroller.status.name == "Stop" or self._hub.charger_done.value or self._hub.chargecontroller.status.name == "Idle":
                if self._hub.chargerobject_switch.value and not self.chargerstop:
                    self.chargerstop = True
                    self.chargerstart = False 
                    await self._hub.hass.services.async_call(domain, call_off)              
        else: 
           if self._hub.chargerobject_switch.value and not self.chargerstop:
                self.chargerstop = True
                self.chargerstart = False
                await self._hub.hass.services.async_call(domain, call_off)  
        self.chargerblocked = False


    async def UpdateMaxCurrent():
        pass