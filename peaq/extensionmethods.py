
def NameToId(input) -> str:
    return input.lower().replace(" ", "_").replace(",", "")

def Is_Float(element) -> bool:
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False

def Is_Int(element) -> bool:
    if element is None:
        return False
    try:
        int(element)
        return True
    except ValueError:
        return False