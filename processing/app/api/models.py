from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

from .enums import (
    CoordinateSystem,
    Datum,
    HeightUnits,
    SpeedUnits,
    TemperatureUnits,
    VegetationType,
    WindHeightUnits
)


class MeteorologicalStation(BaseModel):
    """Model for a meteorological station data."""
    station_name: str
    coord_sys: CoordinateSystem = CoordinateSystem.GEOGCS
    datum: Datum = Datum.WGS84
    lat_ycoord: float
    lon_xcoord: float
    height: float = Field(..., ge=0.0)
    height_units: HeightUnits = HeightUnits.METERS
    speed: float = Field(..., ge=0.0)
    speed_units: SpeedUnits = SpeedUnits.MPS
    direction: float = Field(..., ge=0.0, le=360.0)
    temperature: float = Field(..., ge=-30.0, le=60.0)
    temperature_units: TemperatureUnits = TemperatureUnits.CELSIUS
    cloud_cover: float = Field(default=0.0, ge=0.0, le=100.0)
    date_time: datetime = Field(default_factory=datetime.now)


class WindNinjaRequest(BaseModel):
    """Model for the WindNinja processing request."""
    modelId: str
    elevation_file: str
    output_wind_height: Optional[float] = Field(default=10.0, ge=0.0)
    units_output_wind_height: Optional[WindHeightUnits] = WindHeightUnits.METERS
    vegetation: VegetationType = VegetationType.SHRUBS
    meteorological_stations: List[MeteorologicalStation]

    @field_validator('elevation_file')
    @classmethod
    def validate_extension_file(cls, v: str) -> str:
        """Validate the file extensions."""
        allowed_extensions = ['.tif', '.asc']
        if Path(v).suffix.lower() not in allowed_extensions:
            raise ValueError(
                f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
        return v


class ProcessingResponse(BaseModel):
    """Response model for processing requests."""
    modelId: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Measurement(BaseModel):
    """Model for meteorological measurements."""
    temperature: float = Field(..., ge=-30.0, le=60.0)
    humidity: float = Field(..., ge=0.0, le=100.0)
    precipitation: float = Field(..., ge=0.0)
    solar_radiation: float = Field(..., ge=0.0)


class Observation(BaseModel):
    """Model for a single observation with datetime and measurements."""
    date_time: datetime = Field(default_factory=datetime.now)
    measurement: Measurement


class FuelMoistureStation(BaseModel):
    """Model for a meteorological station with observations for fuel moisture calculation."""
    station_name: str
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    observations: List[Observation]


class FuelMoistureStationResult(FuelMoistureStation):
    """Model for a meteorological station with calculated fuel moisture value."""
    fuel_moisture: Optional[float] = None


class FuelMoistureRequest(BaseModel):
    """Model for the Fuel Moisture processing request."""
    modelId: str
    meteorological_stations: List[FuelMoistureStation]


class FuelMoistureResponse(BaseModel):
    """Response model for fuel moisture processing."""
    modelId: str
    meteorological_stations: List[FuelMoistureStationResult]


class WindNinjaForecastRequest(BaseModel):
    """Model for the WindNinja forecast processing request."""
    modelId: str
    elevation_file: str
    input_wind_height: Optional[float] = Field(default=10.0, ge=0.0)
    units_input_wind_height: Optional[WindHeightUnits] = WindHeightUnits.METERS
    output_wind_height: Optional[float] = Field(default=10.0, ge=0.0)
    units_output_wind_height: Optional[WindHeightUnits] = WindHeightUnits.METERS
    vegetation: VegetationType = VegetationType.SHRUBS
    tiff_file: str
    u_band: int
    v_band: int
    input_speed_units: SpeedUnits = SpeedUnits.MPS
    uni_air_temp: float = Field(..., ge=-30.0, le=60.0)
    uni_cloud_cover: float = Field(default=0.0, ge=0.0, le=100.0)
    simulation_time: datetime = Field(default_factory=datetime.now)

    @field_validator('elevation_file', 'tiff_file', )
    @classmethod
    def validate_extension_file(cls, v: str) -> str:
        """Validate the file extensions."""
        allowed_extensions = ['.tif', '.tiff', '.asc']
        if Path(v).suffix.lower() not in allowed_extensions:
            raise ValueError(
                f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
        return v
