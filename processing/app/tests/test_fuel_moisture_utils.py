import unittest
from app.fuel_moisture.utils import (
    convert_from_celsius_to_fahrenheit,
    convert_from_mm_to_inches,
    round_5_value,
    round_100_value,
    round_001_value,
    parse_label
)


class TestFuelMoistureUtils(unittest.TestCase):
    """Unit tests for the utility functions of the fuel_moisture module."""

    def test_convert_from_celsius_to_fahrenheit(self):
        """Test conversion from Celsius to Fahrenheit."""
        # Test with normal values
        self.assertEqual(convert_from_celsius_to_fahrenheit(0), 32)
        self.assertEqual(convert_from_celsius_to_fahrenheit(100), 212)
        self.assertEqual(convert_from_celsius_to_fahrenheit(-40), -40)
        
        # Test with decimal values
        self.assertAlmostEqual(convert_from_celsius_to_fahrenheit(25), 77)
        self.assertAlmostEqual(convert_from_celsius_to_fahrenheit(37), 98.6)
        
        # Test with non-numeric values (should return None)
        self.assertIsNone(convert_from_celsius_to_fahrenheit("25"))

    def test_convert_from_mm_to_inches(self):
        """Test conversion from millimeters to inches."""
        # Test with normal values
        self.assertAlmostEqual(convert_from_mm_to_inches(25.4), 1.0)
        self.assertAlmostEqual(convert_from_mm_to_inches(0), 0.0)
        self.assertAlmostEqual(convert_from_mm_to_inches(2.54), 0.1)
        self.assertAlmostEqual(convert_from_mm_to_inches(254), 10.0)
        
        # Test with negative values
        self.assertAlmostEqual(convert_from_mm_to_inches(-25.4), -1.0)
        
        # Test with non-numeric values (should return None)
        self.assertIsNone(convert_from_mm_to_inches("10"))

    def test_round_5_value(self):
        """Test rounding to the nearest multiple of 5."""
        # Test with normal values
        self.assertEqual(round_5_value(3), 5)
        self.assertEqual(round_5_value(7), 5)
        self.assertEqual(round_5_value(8), 10)
        self.assertEqual(round_5_value(12), 10)
        self.assertEqual(round_5_value(13), 15)
        
        # Test with negative values
        self.assertEqual(round_5_value(-3), -5)
        self.assertEqual(round_5_value(-7), -5)
        
        # Test with values already multiples of 5
        self.assertEqual(round_5_value(5), 5)
        self.assertEqual(round_5_value(10), 10)
        self.assertEqual(round_5_value(0), 0)
        
        # Test with decimal values
        self.assertEqual(round_5_value(2.6), 5)
        self.assertEqual(round_5_value(7.4), 5)
        self.assertEqual(round_5_value(7.5), 10)
        
        # Test with non-numeric values (should return None)
        self.assertIsNone(round_5_value("10"))

    def test_round_100_value(self):
        """Test rounding to the nearest multiple of 100."""
        # Test with normal values
        self.assertEqual(round_100_value(50), 0)
        self.assertEqual(round_100_value(51), 100)
        self.assertEqual(round_100_value(149), 100)
        self.assertEqual(round_100_value(150), 200)
        
        # Test with negative values
        self.assertEqual(round_100_value(-50), 0)
        self.assertEqual(round_100_value(-150), -200)
        
        # Test with values already multiples of 100
        self.assertEqual(round_100_value(0), 0)
        self.assertEqual(round_100_value(100), 100)
        self.assertEqual(round_100_value(200), 200)
        
        # Test with decimal values
        self.assertEqual(round_100_value(149.9), 100)
        self.assertEqual(round_100_value(150.1), 200)
        
        # Test with non-numeric values (should return None)
        self.assertIsNone(round_100_value("100"))

    def test_round_001_value(self):
        """Test rounding to the nearest multiple of 0.01."""
        # Test with normal values
        self.assertEqual(round_001_value(0.005), 0.00)
        self.assertEqual(round_001_value(0.015), 0.02)
        self.assertEqual(round_001_value(0.115), 0.12)
        
        # Test with negative values
        self.assertEqual(round_001_value(-0.005), 0.00)
        self.assertEqual(round_001_value(-0.015), -0.02)
        
        # Test with values already multiples of 0.01
        self.assertEqual(round_001_value(0.01), 0.01)
        self.assertEqual(round_001_value(0.1), 0.10)
        
        # Test with integer values
        self.assertEqual(round_001_value(1), 1.00)
        
        # Test with non-numeric values (should return None)
        self.assertIsNone(round_001_value("0.01"))

    def test_parse_label(self):
        """Test parsing labels in formats <X, >X and X-Y."""
        # Test with format "<X"
        self.assertEqual(parse_label("<5"), (-900, 5))
        self.assertEqual(parse_label("<10"), (-900, 10))
        
        # Test with format ">X"
        self.assertEqual(parse_label(">5"), (5, 900))
        self.assertEqual(parse_label(">10"), (10, 900))
        
        # Test with format "X-Y"
        self.assertEqual(parse_label("5-10"), (5, 10))
        self.assertEqual(parse_label("0-100"), (0, 100))
        
        # Test with invalid formats (should return None)
        self.assertIsNone(parse_label("invalid"))
        self.assertIsNone(parse_label("5>"))
        self.assertIsNone(parse_label("5<"))
        self.assertIsNone(parse_label("-10-10"), (-10, 10))
        
        # Test with labels that can't be parsed as integers
        self.assertIsNone(parse_label("<a"))
            
        self.assertIsNone(parse_label(">a"))
            
        self.assertIsNone(parse_label("a-b"))


if __name__ == '__main__':
    unittest.main()