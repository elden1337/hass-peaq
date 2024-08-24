class OptionsComparer:
    def compare(self, other) -> list:
        diff = []
        for key, value in self.__dict__.items():
            if key not in other.__dict__.keys():
                diff.append(key)
            elif value != other.__dict__[key]:
                diff.append(key)
        return diff
