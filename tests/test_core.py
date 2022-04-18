import unittest
from custom_components.peaqev.peaqservice.prediction.predictionbase import PredictionBase
from custom_components.peaqev.peaqservice.threshold.thresholdbase import  ThresholdBase

class PredictionTests(unittest.TestCase):
    p = PredictionBase()

    def test_prediction(self):
        ret = self.p._predictedenergy(
            nowmin=13,
            nowsec=37,
            poweravg=420,
            totalhourlyenergy=0.24
        )
        retperc = self.p._predictedpercentageofpeak(2, ret)

        self.assertEqual(ret, 0.565)
        self.assertEqual(retperc, 28.25)

    def test_prediction_valueerrors(self):
        self.assertRaises(
            ValueError,
            self.p._predictedenergy,
            nowmin=60,
            nowsec=37,
            poweravg=420,
            totalhourlyenergy=0.24
        )
        self.assertRaises(
            ValueError,
            self.p._predictedenergy,
            nowmin=50,
            nowsec=-1,
            poweravg=420,
            totalhourlyenergy=-1
        )
        self.assertRaises(ValueError, self.p._predictedenergy, nowmin=50, nowsec=-1, poweravg=-1,
                          totalhourlyenergy=0.05)
        self.assertRaises(ValueError, self.p._predictedenergy, nowmin=50, nowsec=37, poweravg=420,
                          totalhourlyenergy=-1)



class ThresholdTests(unittest.TestCase):
    t = ThresholdBase()

    def test_start(self):
        ret = self.t._start(50, False)
        self.assertEqual(ret, 83.49)

    def test_start_caution_non_caution_late(self):
        ret = self.t._start(50, False)
        ret2 = self.t._start(50, True)
        self.assertEqual(ret, ret2)

    def test_start_caution_non_caution_early(self):
        ret = self.t._start(40, False)
        ret2 = self.t._start(40, True)
        self.assertNotEqual(ret, ret2)
        self.assertTrue(ret > ret2)

    def test_stop(self):
        ret = self.t._stop(13, False)
        self.assertEqual(ret, 82.55)

    def test_stop_caution_non_caution_late(self):
        ret = self.t._stop(50, False)
        ret2 = self.t._stop(50, True)
        self.assertEqual(ret, ret2)

    def test_stop_caution_non_caution_early(self):
        ret = self.t._stop(40, False)
        ret2 = self.t._stop(40, True)
        self.assertNotEqual(ret, ret2)
        self.assertTrue(ret > ret2)


#if __name__ == '__main__':
    #unittest.main()
