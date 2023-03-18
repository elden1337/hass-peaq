import time

def nametoid(input_string) -> str:
    if isinstance(input_string, str):
        return input_string.lower().replace(" ", "_").replace(",", "")
    return input_string


def dt_from_epoch(epoch: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))
