
async def async_set_startpeak_dict(user_input) -> dict:
    return {1: user_input["jan"], 2: user_input["feb"], 3: user_input["mar"], 4: user_input["apr"],
           5: user_input["may"], 6: user_input["jun"], 7: user_input["jul"], 8: user_input["aug"],
           9: user_input["sep"], 10: user_input["oct"], 11: user_input["nov"], 12: user_input["dec"]}
