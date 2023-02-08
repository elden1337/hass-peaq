class Callback:
    def __init__(self):
        self._observers: list = []

    def callback(self):
        for callback in self._observers:
            # print('announcing change')
            callback()

    def bind_to(self, callback):
        # print(f'bound {id(self)}')
        self._observers.append(callback)
