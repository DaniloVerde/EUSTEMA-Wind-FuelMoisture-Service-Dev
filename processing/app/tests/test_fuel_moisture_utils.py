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
    """Test unitari per le funzioni di utility del modulo fuel_moisture."""

    def test_convert_from_celsius_to_fahrenheit(self):
        """Testa la conversione da Celsius a Fahrenheit."""
        # Test con valori normali
        self.assertEqual(convert_from_celsius_to_fahrenheit(0), 32)
        self.assertEqual(convert_from_celsius_to_fahrenheit(100), 212)
        self.assertEqual(convert_from_celsius_to_fahrenheit(-40), -40)
        
        # Test con valori decimali
        self.assertAlmostEqual(convert_from_celsius_to_fahrenheit(25), 77)
        self.assertAlmostEqual(convert_from_celsius_to_fahrenheit(37), 98.6)
        
        # Test con valori non numerici (dovrebbe restituire None)
        self.assertIsNone(convert_from_celsius_to_fahrenheit("25"))

    def test_convert_from_mm_to_inches(self):
        """Testa la conversione da millimetri a pollici."""
        # Test con valori normali
        self.assertAlmostEqual(convert_from_mm_to_inches(25.4), 1.0)
        self.assertAlmostEqual(convert_from_mm_to_inches(0), 0.0)
        self.assertAlmostEqual(convert_from_mm_to_inches(2.54), 0.1)
        self.assertAlmostEqual(convert_from_mm_to_inches(254), 10.0)
        
        # Test con valori negativi
        self.assertAlmostEqual(convert_from_mm_to_inches(-25.4), -1.0)
        
        # Test con valori non numerici (dovrebbe restituire None)
        self.assertIsNone(convert_from_mm_to_inches("10"))

    def test_round_5_value(self):
        """Testa l'arrotondamento al multiplo di 5 più vicino."""
        # Test con valori normali
        self.assertEqual(round_5_value(3), 5)
        self.assertEqual(round_5_value(7), 5)
        self.assertEqual(round_5_value(8), 10)
        self.assertEqual(round_5_value(12), 10)
        self.assertEqual(round_5_value(13), 15)
        
        # Test con valori negativi
        self.assertEqual(round_5_value(-3), -5)
        self.assertEqual(round_5_value(-7), -5)
        
        # Test con valori già multipli di 5
        self.assertEqual(round_5_value(5), 5)
        self.assertEqual(round_5_value(10), 10)
        self.assertEqual(round_5_value(0), 0)
        
        # Test con valori decimali
        self.assertEqual(round_5_value(2.6), 5)
        self.assertEqual(round_5_value(7.4), 5)
        self.assertEqual(round_5_value(7.5), 10)
        
        # Test con valori non numerici (dovrebbe restituire None)
        self.assertIsNone(round_5_value("10"))

    def test_round_100_value(self):
        """Testa l'arrotondamento al multiplo di 100 più vicino."""
        # Test con valori normali
        self.assertEqual(round_100_value(50), 0)
        self.assertEqual(round_100_value(51), 100)
        self.assertEqual(round_100_value(149), 100)
        self.assertEqual(round_100_value(150), 200)
        
        # Test con valori negativi
        self.assertEqual(round_100_value(-50), 0)
        self.assertEqual(round_100_value(-150), -200)
        
        # Test con valori già multipli di 100
        self.assertEqual(round_100_value(0), 0)
        self.assertEqual(round_100_value(100), 100)
        self.assertEqual(round_100_value(200), 200)
        
        # Test con valori decimali
        self.assertEqual(round_100_value(149.9), 100)
        self.assertEqual(round_100_value(150.1), 200)
        
        # Test con valori non numerici (dovrebbe restituire None)
        self.assertIsNone(round_100_value("100"))

    def test_round_001_value(self):
        """Testa l'arrotondamento al multiplo di 0.01 più vicino."""
        # Test con valori normali
        self.assertEqual(round_001_value(0.005), 0.00)
        self.assertEqual(round_001_value(0.015), 0.02)
        self.assertEqual(round_001_value(0.115), 0.12)
        
        # Test con valori negativi
        self.assertEqual(round_001_value(-0.005), 0.00)
        self.assertEqual(round_001_value(-0.015), -0.02)
        
        # Test con valori già multipli di 0.01
        self.assertEqual(round_001_value(0.01), 0.01)
        self.assertEqual(round_001_value(0.1), 0.10)
        
        # Test con valori interi
        self.assertEqual(round_001_value(1), 1.00)
        
        # Test con valori non numerici (dovrebbe restituire None)
        self.assertIsNone(round_001_value("0.01"))

    def test_parse_label(self):
        """Testa il parsing delle etichette nei formati <X, >X e X-Y."""
        # Test con formato "<X"
        self.assertEqual(parse_label("<5"), (-900, 5))
        self.assertEqual(parse_label("<10"), (-900, 10))
        
        # Test con formato ">X"
        self.assertEqual(parse_label(">5"), (5, 900))
        self.assertEqual(parse_label(">10"), (10, 900))
        
        # Test con formato "X-Y"
        self.assertEqual(parse_label("5-10"), (5, 10))
        self.assertEqual(parse_label("0-100"), (0, 100))
        
        # Test con formati non validi (dovrebbe restituire None)
        self.assertIsNone(parse_label("invalid"))
        self.assertIsNone(parse_label("5>"))
        self.assertIsNone(parse_label("5<"))
        self.assertIsNone(parse_label("-10-10"), (-10, 10))
        
        # Test con etichette non parsificabili in interi
        self.assertIsNone(parse_label("<a"))
            
        self.assertIsNone(parse_label(">a"))
            
        self.assertIsNone(parse_label("a-b"))


if __name__ == '__main__':
    unittest.main()