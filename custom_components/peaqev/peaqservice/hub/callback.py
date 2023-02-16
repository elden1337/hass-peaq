class ObserverDirector:
    _observers: dict = {}
    
    @staticmethod
    def attach(event_type: str, func) -> None:
        if event_type in ObserverDirector._observers:
            ObserverDirector._observers[event_type].append(func)
        ObserverDirector._observers[event_type] = [func]

    @staticmethod
    def notify(event_type, *args) -> None:
        try:
            for o in ObserverDirector._observers[event_type]:
                o(args)
        except:
            pass


class testclass:
    def __init__(self):
        ObserverDirector.attach("even 8", self.notified)
        ObserverDirector.attach("molusk", self.notified)

    def notified(self, *args):
        print(f"I was notified {args}")


class test_handling:
    def __init__(self):
        for i in range(0,100):
            if i%8 == 0:
                ObserverDirector.notify("even 8", i)


t = testclass()
tt = test_handling()
ObserverDirector.notify("molusk", "Magnus")


