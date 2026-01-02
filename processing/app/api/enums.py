from enum import Enum

class CoordinateSystem(str, Enum):
    """Enum for coordinate systems."""
    GEOGCS = "GEOGCS"
    PROJCS = "PROJCS"

class Datum(str, Enum):
    """Enum for datums."""
    WGS84 = "WGS84"
    NAD83 = "NAD83"
    NAD27 = "NAD27"

class HeightUnits(str, Enum):
    """Enum for height units."""
    METERS = "meters"
    FEET = "feet"

class SpeedUnits(str, Enum):
    """Enum for speed units."""
    MPS = "mps"
    KPH = "kph"
    MPH = "mph"
    KTS = "kts"

class TemperatureUnits(str, Enum):
    """Enum for temperature units."""
    CELSIUS = "C"
    FAHRENHEIT = "F"

class VegetationType(str, Enum):
    """Enum for vegetation types."""
    TREES = "trees"
    BRUSH = "brush"
    GRASS = "grass"
class WindHeightUnits(str, Enum):
    """Enum for wind height units."""
    METERS = "m"
    FEET = "ft"

class ResourceProviderType(str, Enum):
    """Enum for resource providers. Used for kafka topics result messaging."""
    v6_8 = "v6-8"
    v6_7 = "v6-7"