# import unittest
# from thresholdbase import ThresholdBase
#
#
# class ThresholdTests(unittest.TestCase):
#     t = ThresholdBase()
#
#     def test_start(self):
#         ret = self.t._start(50, False)
#         self.assertEqual(ret, 83.49)
#
#     def test_start_caution_non_caution_late(self):
#         ret = self.t._start(50, False)
#         ret2 = self.t._start(50, True)
#         self.assertEqual(ret, ret2)
#
#     def test_start_caution_non_caution_early(self):
#         ret = self.t._start(40, False)
#         ret2 = self.t._start(40, True)
#         self.assertNotEqual(ret, ret2)
#         self.assertTrue(ret > ret2)
#
#     def test_stop(self):
#         ret = self.t._stop(13, False)
#         self.assertEqual(ret, 82.55)
#
#     def test_stop_caution_non_caution_late(self):
#         ret = self.t._stop(50, False)
#         ret2 = self.t._stop(50, True)
#         self.assertEqual(ret, ret2)
#
#     def test_stop_caution_non_caution_early(self):
#         ret = self.t._stop(40, False)
#         ret2 = self.t._stop(40, True)
#         self.assertNotEqual(ret, ret2)
#         self.assertTrue(ret > ret2)
#
#
# if __name__ == '__main__':
#     unittest.main()