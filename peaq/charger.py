

class Charger():
    def __init__(self, hub):
        self._hub = hub
        self.chargerblocked = False
        self.chargerStart = False
        self.chargerStop = False

    async def Charge(self, domain:str, call_on:str, call_off:str):
        self.chargerblocked = True
        if self._hub.chargerenabled.value == True:
            if self._hub.chargecontroller.status.name == "Start":
                if self._hub.chargerobject_switch.value == "off" and self.chargerStart == False: 
                    self.chargerStart = True
                    self.chargerStop = False
                    await self._hub.hass.services.async_call(domain,call_on)
            elif self._hub.chargecontroller.status.name == "Stop" or self._hub.charger_done.value == True or self._hub.chargecontroller.status.name == "Idle":
                if self._hub.chargerobject_switch.value == "on" and self.chargerStop == False:
                    self.chargerStop = True
                    self.chargerStart = False 
                    await self._hub.hass.services.async_call(domain, call_off)              
        else: 
           if self._hub.chargerobject_switch.value == "on" and self.chargerStop == False:
                self.chargerStop = True
                self.chargerStart = False
                await self._hub.hass.services.async_call(domain, call_off)  
        self.chargerblocked = False


    async def UpdateMaxCurrent():
        pass