from dataclasses import dataclass


@dataclass
class FunctionCall:
    function: any
    call_async: bool = False
