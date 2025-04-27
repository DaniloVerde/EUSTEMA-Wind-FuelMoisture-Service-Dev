def convert_from_celsius_to_fahrenheit(temperature_value):
    return (temperature_value * 9/5) + 32


def convert_from_mm_to_inches(mm):
    return (mm / 25.4)


def round_5_value(value):
    rounded_value = round(value / 5) * 5
    return rounded_value


def round_100_value(value):
    rounded_value = round(value / 100) * 100
    return rounded_value


def round_001_value(value):
    rounded_value = round(value / 0.01) * 0.01
    return rounded_value
