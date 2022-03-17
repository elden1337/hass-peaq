
class Extensions:
    
    @staticmethod
    def NameToId(input) -> str:
        return input.lower().replace(" ", "_").replace(",", "")
