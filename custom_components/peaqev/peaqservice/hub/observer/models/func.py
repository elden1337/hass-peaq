from dataclasses import dataclass


@dataclass
class Func:
    function: any
    call_async: bool = False
