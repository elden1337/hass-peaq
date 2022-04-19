# import unittest
# import predictionbase as p
#
#
# class PredictionTests(unittest.TestCase):
#
#     def test_prediction(self):
#         ret = p.PredictionBase._predictedenergy(
#             nowmin=13,
#             nowsec=37,
#             poweravg=420,
#             totalhourlyenergy=0.24
#         )
#         retperc = p.PredictionBase._predictedpercentageofpeak(2, ret)
#
#         self.assertEqual(ret, 0.565)
#         self.assertEqual(retperc, 28.25)
#
#     def test_prediction_valueerrors(self):
#         self.assertRaises(
#             ValueError,
#             p.PredictionBase._predictedenergy,
#             nowmin=60,
#             nowsec=37,
#             poweravg=420,
#             totalhourlyenergy=0.24
#         )
#         self.assertRaises(
#             ValueError,
#             p.PredictionBase._predictedenergy,
#             nowmin=50,
#             nowsec=-1,
#             poweravg=420,
#             totalhourlyenergy=-1
#         )
#         self.assertRaises(ValueError, p.PredictionBase._predictedenergy, nowmin=50, nowsec=-1, poweravg=-1,
#                           totalhourlyenergy=0.05)
#         self.assertRaises(ValueError, p.PredictionBase._predictedenergy, nowmin=50, nowsec=37, poweravg=420,
#                           totalhourlyenergy=-1)
#
#
# def suite():
#     test_suite = unittest.TestSuite()
#     test_suite.addTest(unittest.makeSuite(PredictionTests))
#     return test_suite
#
#
# if __name__ == '__main__':
#     unittest.main()
