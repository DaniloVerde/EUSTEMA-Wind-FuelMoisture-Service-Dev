from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class MeteorologicalStation(BaseModel):
    """Model for a meteorological station data."""
    station_name: str
    coord_sys: str = "GEOGCS"
    datum: str = "WGS84"
    lat_ycoord: str
    lon_xcoord: str
    height: str
    height_units: str = "meters"
    speed: str
    speed_units: str = "mps"
    direction: str
    temperature: str
    temperature_units: str = "C"
    cloud_cover: str = "0"
    date_time: str

class WindNinjaRequest(BaseModel):
    """Model for the WindNinja processing request."""
    modelId: str
    elevation_file: str
    output_wind_height: Optional[str] = "10"
    units_output_wind_height: Optional[str] = "m"
    vegetation: Optional[str] = "trees"
    meteorological_stations: List[MeteorologicalStation]
    
class ProcessingResponse(BaseModel):
    """Response model for processing requests."""
    modelId: str
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

class Measurement(BaseModel):
    """Model for meteorological measurements."""
    temperature: float
    humidity: float
    precipitation: float
    solar_radiation: float

class Observation(BaseModel):
    """Model for a single observation with datetime and measurements."""
    datetime: str
    measurement: Measurement

class FuelMoistureStation(BaseModel):
    """Model for a meteorological station with observations for fuel moisture calculation."""
    station_name: str
    lat: str
    lon: str
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
    input_wind_height: Optional[str] = "10"
    units_input_wind_height: Optional[str] = "m"
    output_wind_height: Optional[str] = "10"
    units_output_wind_height: Optional[str] = "m"
    vegetation: Optional[str] = "trees"
    wind_direction_file: str
    wind_speed_file: str
    input_speed_units: str = "mps"
    uni_air_temp: str
    uni_cloud_cover: str = "0"
    simulation_time: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%dT%H:%M"))