import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def convert_from_celsius_to_fahrenheit(temperature_value: float) -> Optional[float]:
    """
    Convert temperature from Celsius to Fahrenheit.
    
    Args:
        temperature_value: Temperature in Celsius degrees
        
    Returns:
        float: Temperature in Fahrenheit degrees or None in case of error
    """
    try:
        return (temperature_value * 9/5) + 32
    except Exception as e:
        logger.exception(f"Error converting from Celsius to Fahrenheit: {str(e)}")
        return None


def convert_from_mm_to_inches(mm: float) -> Optional[float]:
    """
    Convert millimeters to inches.
    
    Args:
        mm: Value in millimeters
        
    Returns:
        float: Value in inches or None in case of error
    """
    try:
        return (mm / 25.4)
    except Exception as e:
        logger.exception(f"Error converting from mm to inches: {str(e)}")
        return None


def round_5_value(value: float) -> Optional[float]:
    """
    Round a value to the nearest multiple of 5.
    
    Args:
        value: Value to round
        
    Returns:
        float: Rounded value or None in case of error
    """
    try:
        rounded_value = round(value / 5) * 5
        return rounded_value
    except Exception as e:
        logger.exception(f"Error rounding to nearest 5: {str(e)}")
        return None


def round_100_value(value: float) -> Optional[float]:
    """
    Round a value to the nearest multiple of 100.
    
    Args:
        value: Value to round
        
    Returns:
        float: Rounded value or None in case of error
    """
    try:
        rounded_value = round(value / 100) * 100
        return rounded_value
    except Exception as e:
        logger.exception(f"Error rounding to nearest 100: {str(e)}")
        return None


def round_001_value(value: float) -> Optional[float]:
    """
    Round a value to the nearest multiple of 0.01.
    
    Args:
        value: Value to round
        
    Returns:
        float: Rounded value or None in case of error
    """
    try:
        rounded_value = round(value / 0.01) * 0.01
        return rounded_value
    except Exception as e:
        logger.exception(f"Error rounding to nearest 0.01: {str(e)}")
        return None


def parse_label(label: str) -> Optional[Tuple[int, int]]:
    """
    Parse a label string into a tuple representing a range.
    
    Args:
        label: String label to parse (e.g. "<5", ">10", "5-10")
        
    Returns:
        tuple: A tuple of two integers representing the range or None in case of error
    """
    try:
        if "<" in label:
            return (int(-900), int(label[1:]))
        if ">" in label:
            return (int(label[1:]), int(900))
        if "-" in label:
            return tuple(map(int, label.split('-')))
        logger.error(f"Error parsing label: Format not recognized for '{label}'")
        return None
    except Exception as e:
        logger.exception(f"Error parsing label '{label}': {str(e)}")
        return None
