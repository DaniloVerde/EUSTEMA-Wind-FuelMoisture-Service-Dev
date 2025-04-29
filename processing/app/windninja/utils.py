import os
import json
import csv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def json_to_station_csv(json_data, output_dir, model_id=None):
    """
    Converts JSON data with a list of weather stations into individual CSV files.
    
    Args:
        json_data (dict): JSON data containing the list of weather stations
        output_dir (str): Path to the output directory for CSV files
        model_id (str, optional): Model ID, if not provided it will use the one in the JSON
        
    Returns:
        tuple: (list of csv files created, path to the list file)
    """
    # Use modelId from JSON if not specified
    if model_id is None:
        model_id = json_data.get('modelId')
    
    if not model_id:
        raise ValueError("modelId not found in JSON and not specified as parameter")
    
    # Create output directory if it doesn't exist
    model_dir = os.path.join(output_dir, model_id)
    input_dir = os.path.join(model_dir, "input")
    os.makedirs(input_dir, exist_ok=True)
    
    # Current date for filename
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H%M')
    
    # List of created files
    csv_files = []
    
    # Process each station
    for station in json_data.get('meteorological_stations', []):
        # Create filename
        station_name = station.get('station_name', 'unknown')
        csv_filename = f"{station_name}-{current_datetime}-0.csv"
        csv_filepath = os.path.join(input_dir, csv_filename)
        
        # Create CSV file
        with open(csv_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Header
            writer.writerow([
                "Station_Name", "Coord_Sys(PROJCS,GEOGCS)", "Datum(WGS84,NAD83,NAD27)",
                "Lat/YCoord", "Lon/XCoord", "Height", "Height_Units(meters,feet)",
                "Speed", "Speed_Units(mph,kph,mps,kts)", "Direction(degrees)",
                "Temperature", "Temperature_Units(F,C)", "Cloud_Cover(%)",
                "Radius_of_Influence", "Radius_of_Influence_Units(miles,feet,meters,km)",
                "date_time"
            ])
            
            # Station data
            writer.writerow([
                station.get('station_name', ''),
                station.get('coord_sys', 'GEOGCS'),
                station.get('datum', 'WGS84'),
                station.get('lat_ycoord', ''),
                station.get('lon_xcoord', ''),
                station.get('height', ''),
                station.get('height_units', 'meters'),
                station.get('speed', ''),
                station.get('speed_units', 'mps'),
                station.get('direction', ''),
                station.get('temperature', ''),
                station.get('temperature_units', 'C'),
                station.get('cloud_cover', '0'),
                "-1",  # Default value for radius_of_influence
                "km",  # Default unit for radius_of_influence
                # station.get('date_time', '')
            ])
        
        logger.info(f"Created CSV file for station {station_name}: {csv_filepath}")
        csv_files.append(csv_filename)
    
    # Create list file
    list_filename = f"stations_list_{current_datetime}.csv"
    list_filepath = os.path.join(input_dir, list_filename)
    
    with open(list_filepath, 'w', newline='') as listfile:
        writer = csv.writer(listfile)
        writer.writerow(["Recent_Station_File_List", ""])
        for csv_file in csv_files:
            writer.writerow([csv_file])
    
    logger.info(f"Created stations list file: {list_filepath}")
    
    return csv_files, list_filepath


def create_station_csv_from_json_file(json_filepath, output_dir, model_id=None):
    """
    Reads a JSON file with a list of weather stations and creates CSV files.
    
    Args:
        json_filepath (str): Path to the JSON file
        output_dir (str): Path to the output directory for CSV files
        model_id (str, optional): Model ID, if not provided it will use the one in the JSON
        
    Returns:
        tuple: (list of csv files created, path to the list file)
    """
    try:
        with open(json_filepath, 'r') as jsonfile:
            json_data = json.load(jsonfile)
        
        return json_to_station_csv(json_data, output_dir, model_id)
    
    except Exception as e:
        logger.error(f"Error converting JSON file to CSV: {str(e)}")
        raise