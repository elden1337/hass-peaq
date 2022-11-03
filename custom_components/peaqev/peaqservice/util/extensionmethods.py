
def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(" ", "_").replace(",", "")
    return input_string

def try_parse(input_string:str, parsetype:type):
    try:
        ret = parsetype(input_string)
        return ret
    except Exception as e:
        return False
