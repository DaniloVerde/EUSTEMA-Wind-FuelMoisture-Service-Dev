from pydantic import BaseModel, Field
from typing import List, Optional
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