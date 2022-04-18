import unittest
from predictionbase import PredictionBase

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

if __name__ == '__main__':
    unittest.main()