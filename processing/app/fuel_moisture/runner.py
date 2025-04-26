import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

def calculate_fuel_moisture_mock(
    temperature: float,
    humidity: float,
    solar_radiation: float,
    precipitation_previous_hour: float,
    previous_moisture: Optional[float] = None
) -> float:
    """
    Mock function to calculate fuel moisture based on weather parameters.
    
    Args:
        temperature: Temperature in Celsius
        humidity: Relative humidity in percent
        solar_radiation: Solar radiation in W/m²
        precipitation_previous_hour: Precipitation from the previous hour in mm
        previous_moisture: Previously calculated moisture value (optional)
    
    Returns:
        Calculated fuel moisture value
    """
    # This is a simplified mock calculation - replace with actual algorithm
    base_moisture = humidity / 2.0
    temp_factor = 30.0 - temperature if temperature < 30.0 else 0.0
    solar_factor = -0.01 * solar_radiation
    precip_factor = precipitation_previous_hour * 2.0
    
    # If we have a previous moisture value, use it as a base and adjust
    if previous_moisture is not None:
        moisture = (previous_moisture + base_moisture + temp_factor + solar_factor + precip_factor) / 2.0
    else:
        moisture = base_moisture + temp_factor + solar_factor + precip_factor
    
    # Ensure moisture is within reasonable bounds
    return max(0.0, min(100.0, moisture))

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
        key=lambda obs: datetime.fromisoformat(obs["datetime"])
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
    sorted_observations = sort_observations_by_datetime(station["observations"])
    
    previous_moisture = None
    previous_precipitation = 0.0  # Initial value for the first calculation
    
    for i, obs in enumerate(sorted_observations):
        measurement = obs["measurement"]
        temperature = measurement["temperature"]
        humidity = measurement["humidity"]
        solar_radiation = measurement["solar_radiation"]
        
        # Use the previous hour's precipitation
        if i > 0:
            previous_precipitation = sorted_observations[i-1]["measurement"]["precipitation"]
        
        # Calculate moisture using current weather data and previous moisture value
        moisture = calculate_fuel_moisture_mock(
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
