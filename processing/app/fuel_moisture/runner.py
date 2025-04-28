import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from .utils import (
    convert_from_celsius_to_fahrenheit,
    convert_from_mm_to_inches,
)
from .processing import (
    get_surface_temperature,
    get_equilibrium_moisture_content,
    get_rainfall_moisture_factor,
    get_evaporation_correction_factor,
    get_moisture_correction_factor,
)


def calculate_fuel_moisture_content(
    temperature: float,
    humidity: float,
    solar_radiation: float,
    precipitation_previous_hour: float,
    previous_moisture: Optional[float] = None
) -> Optional[float]:
    """
    Calculate the fuel moisture content based on weather parameters and previous moisture.
    
    This function implements the full fuel moisture calculation process by:
    1. Converting temperature and precipitation to required units
    2. Calculating surface temperature based on air temperature and solar radiation
    3. Determining equilibrium moisture content
    4. Calculating rainfall moisture factor
    5. Calculating evaporation correction factor
    6. Calculating moisture correction factor
    7. Combining all factors to determine the final fuel moisture content
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity in percent (0-100)
        solar_radiation: Solar radiation in W/m²
        precipitation_previous_hour: Precipitation from the previous hour in mm
        previous_moisture: Previously calculated moisture value (optional)
        
    Returns:
        Calculated fuel moisture value or None if calculation fails
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"Starting fuel moisture calculation with parameters: "
                     f"temperature={temperature}°C, humidity={humidity}%, "
                     f"solar_radiation={solar_radiation}W/m², "
                     f"precipitation_previous_hour={precipitation_previous_hour}mm, "
                     f"previous_moisture={previous_moisture}")
        
        # Convert units
        temperature_f = convert_from_celsius_to_fahrenheit(temperature)
        if temperature_f is None:
            logger.error("Failed to convert temperature to Fahrenheit")
            return None
            
        precipitation_in_inches = convert_from_mm_to_inches(precipitation_previous_hour)
        if precipitation_in_inches is None:
            logger.error("Failed to convert precipitation to inches")
            return None
        
        logger.debug(f"Converted units: temperature_f={temperature_f}°F, precipitation_in_inches={precipitation_in_inches}in")
        
        # Calculate surface temperature
        surface_temperature = get_surface_temperature(
            temperature=temperature_f,
            solar_radiation=solar_radiation,
        )
        if surface_temperature is None:
            logger.error("Failed to calculate surface temperature")
            return None
        
        logger.debug(f"Calculated surface temperature: {surface_temperature}°F")
        
        # Calculate equilibrium moisture content
        eqmc = get_equilibrium_moisture_content(
            surface_temperature=surface_temperature,
            humidity=humidity,
        )
        if eqmc is None:
            logger.error("Failed to calculate equilibrium moisture content")
            return None
            
        logger.debug(f"Calculated equilibrium moisture content: {eqmc}")
        
        # Use EQMC as previous moisture if not provided
        if previous_moisture is None:
            previous_moisture = eqmc
            logger.debug(f"No previous moisture provided, using EQMC: {previous_moisture}")
        
        # Calculate rainfall moisture factor
        rmf = get_rainfall_moisture_factor(
            precipitation=precipitation_in_inches,
        )
        if rmf is None:
            logger.error("Failed to calculate rainfall moisture factor")
            return None
            
        logger.debug(f"Calculated rainfall moisture factor: {rmf}")
        
        # Calculate evaporation correction factor
        ecf = get_evaporation_correction_factor(
            surface_temperature=surface_temperature,
            previous_fuel_moisture=previous_moisture,
        )
        if ecf is None:
            logger.error("Failed to calculate evaporation correction factor")
            return None
            
        logger.debug(f"Calculated evaporation correction factor: {ecf}")
        
        # Calculate moisture correction factor
        mcf = get_moisture_correction_factor(
            surface_temperature=surface_temperature,
            humidity=humidity,
            eqmc=eqmc,
            previous_fuel_moisture=previous_moisture,
            precipitation=precipitation_in_inches,
        )
        if mcf is None:
            logger.error("Failed to calculate moisture correction factor")
            return None
            
        logger.debug(f"Calculated moisture correction factor: {mcf}")
        
        # Calculate final fuel moisture content
        fuel_moisture_content = previous_moisture + rmf + ecf + mcf
        logger.debug(f"Final fuel moisture calculation: {previous_moisture} + {rmf} + {ecf} + {mcf} = {fuel_moisture_content}")
        
        # Cap the maximum value at 60%
        if fuel_moisture_content > 60.0:
            logger.debug(f"Capping fuel moisture content from {fuel_moisture_content} to 60.0")
            fuel_moisture_content = 60.0
        
        logger.info(f"Successfully calculated fuel moisture content: {fuel_moisture_content}")
        return fuel_moisture_content
        
    except Exception as e:
        logger.exception(f"Error calculating fuel moisture content: {str(e)}")
        return None


def sort_observations_by_datetime(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort observations from oldest to newest.

    Args:
        observations: List of observation dictionaries

    Returns:
        Sorted list of observations
    """
    return sorted(
        observations,
        key=lambda obs: datetime.fromisoformat(obs["date_time"])
    )


def process_station_data(station: Dict[str, Any]) -> Tuple[str, float]:
    """
    Process a single station's data to calculate final fuel moisture.

    Args:
        station: Station data dictionary

    Returns:
        Tuple of (station_name, final_moisture_value)
    """
    station_name = station["station_name"]
    sorted_observations = sort_observations_by_datetime(
        station["observations"])

    previous_moisture = None
    previous_precipitation = 0.0  # Initial value for the first calculation

    for i, obs in enumerate(sorted_observations):
        measurement = obs["measurement"]
        temperature = measurement["temperature"]
        humidity = measurement["humidity"]
        solar_radiation = measurement["solar_radiation"]

        # Use the previous hour's precipitation
        if i > 0:
            previous_precipitation = sorted_observations[i -
                                                         1]["measurement"]["precipitation"]

        # Calculate moisture using current weather data and previous moisture value
        moisture = calculate_fuel_moisture_content(
            temperature=temperature,
            humidity=humidity,
            solar_radiation=solar_radiation,
            precipitation_previous_hour=previous_precipitation,
            previous_moisture=previous_moisture
        )

        # Update previous_moisture for next iteration
        previous_moisture = moisture

    # Return final moisture value after processing all observations
    return station_name, previous_moisture


def process_fuel_moisture_data(json_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Process fuel moisture data for all stations.

    Args:
        json_data: JSON data structure containing station information and observations

    Returns:
        Dictionary mapping station names to calculated fuel moisture values
    """
    results = {}

    for station in json_data["meteorological_stations"]:
        station_name, final_moisture = process_station_data(station)
        results[station_name] = final_moisture

    return results


def run_fuel_moisture_calculation(input_file_path: str) -> Dict[str, float]:
    """
    Run fuel moisture calculation based on JSON input file.

    Args:
        input_file_path: Path to the input JSON file

    Returns:
        Dictionary mapping station names to calculated fuel moisture values
    """
    with open(input_file_path, 'r') as f:
        input_data = json.load(f)

    return process_fuel_moisture_data(input_data)


if __name__ == "__main__":
    # Example usage
    input_path = "d:/Projects/MASE/src/CU6.7/processing/app/test_data/input/fuel_moisture_station_list.json"
    result = run_fuel_moisture_calculation(input_path)
    print("Calculated fuel moisture values by station:")
    for station, moisture in result.items():
        print(f"Station {station}: {moisture:.2f}%")
