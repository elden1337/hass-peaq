class Schedule:

    async def set_schedule(
            self,
            charge_amount:float,
            departure_time:str,
            schedule_starttime:str = None,
            override_settings:bool = False
    ) -> bool:
        pass

    async def _parse_data(self):
        #parse the datetime(s)
        #if the starttime is None, set it to now()
        pass


    async def _inspect_hours(self):
        """inspect the hourly pricing"""
        pass

    async def _make_calulation(self):
        """calculate based on the pricing of hours, current peak and the avg24hr energy consumption"""
        pass


    #todo: make new averagesensor which stores average 24h for the house (to help scheduler be as accurate as possible)