
def nametoid(input) -> str:
    return input.lower().replace(" ", "_").replace(",", "")

def try_parse(input:str, parsetype:type):
    try:
        ret = parsetype(input)
        return ret
    except:
        return False