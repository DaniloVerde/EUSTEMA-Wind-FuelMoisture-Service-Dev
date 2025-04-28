import os
import json
import csv
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def json_to_station_csv(json_data, output_dir, model_id=None):
    """
    Converte i dati JSON con un elenco di stazioni meteo in singoli file CSV.
    
    Args:
        json_data (dict): Dati JSON contenenti l'elenco delle stazioni meteo
        output_dir (str): Percorso della directory di output per i file CSV
        model_id (str, optional): ID del modello, se non fornito verrà utilizzato quello nel JSON
        
    Returns:
        tuple: (list of csv files created, path to the list file)
    """
    # Usa il modelId dal JSON se non specificato
    if model_id is None:
        model_id = json_data.get('modelId')
    
    if not model_id:
        raise ValueError("modelId non trovato nel JSON e non specificato come parametro")
    
    # Crea la directory di output se non esiste
    model_dir = os.path.join(output_dir, model_id)
    input_dir = os.path.join(model_dir, "input")
    os.makedirs(input_dir, exist_ok=True)
    
    # Data corrente per il nome del file
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H%M')
    
    # Lista di file creati
    csv_files = []
    
    # Processa ogni stazione
    for station in json_data.get('meteorological_stations', []):
        # Crea il nome del file
        station_name = station.get('station_name', 'unknown')
        csv_filename = f"{station_name}-{current_datetime}-0.csv"
        csv_filepath = os.path.join(input_dir, csv_filename)
        
        # Crea il file CSV
        with open(csv_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Intestazione
            writer.writerow([
                "Station_Name", "Coord_Sys(PROJCS,GEOGCS)", "Datum(WGS84,NAD83,NAD27)",
                "Lat/YCoord", "Lon/XCoord", "Height", "Height_Units(meters,feet)",
                "Speed", "Speed_Units(mph,kph,mps,kts)", "Direction(degrees)",
                "Temperature", "Temperature_Units(F,C)", "Cloud_Cover(%)",
                "Radius_of_Influence", "Radius_of_Influence_Units(miles,feet,meters,km)",
                "date_time"
            ])
            
            # Dati della stazione
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
                "-1",  # Valore predefinito per radius_of_influence
                "km",  # Unità predefinita per radius_of_influence
                # station.get('date_time', '')
            ])
        
        logger.info(f"Creato file CSV per stazione {station_name}: {csv_filepath}")
        csv_files.append(csv_filename)
    
    # Crea il file di elenco
    list_filename = f"stations_list_{current_datetime}.csv"
    list_filepath = os.path.join(input_dir, list_filename)
    
    with open(list_filepath, 'w', newline='') as listfile:
        writer = csv.writer(listfile)
        writer.writerow(["Recent_Station_File_List", ""])
        for csv_file in csv_files:
            writer.writerow([csv_file])
    
    logger.info(f"Creato file elenco stazioni: {list_filepath}")
    
    return csv_files, list_filepath


def create_station_csv_from_json_file(json_filepath, output_dir, model_id=None):
    """
    Legge un file JSON con un elenco di stazioni meteo e crea i file CSV.
    
    Args:
        json_filepath (str): Percorso del file JSON
        output_dir (str): Percorso della directory di output per i file CSV
        model_id (str, optional): ID del modello, se non fornito verrà utilizzato quello nel JSON
        
    Returns:
        tuple: (list of csv files created, path to the list file)
    """
    try:
        with open(json_filepath, 'r') as jsonfile:
            json_data = json.load(jsonfile)
        
        return json_to_station_csv(json_data, output_dir, model_id)
    
    except Exception as e:
        logger.error(f"Errore nella conversione del file JSON in CSV: {str(e)}")
        raise