import unittest
from src.calculations import calculate_volume

class TestCalculations(unittest.TestCase):

    def test_calculate_volume(self):
        self.assertAlmostEqual(calculate_volume(10, 5), 16.666666666666668)
        self.assertAlmostEqual(calculate_volume(0, 5), 0)
        self.assertAlmostEqual(calculate_volume(10, 0), 0)
        self.assertAlmostEqual(calculate_volume(0, 0), 0)
        self.assertAlmostEqual(calculate_volume(15, 3), 15.0)

if __name__ == '__main__':
    unittest.main()