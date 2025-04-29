import os
import json
import logging
from pathlib import Path
from .utils import json_to_station_csv
from ..storage.minio_client import MinioClient

logger = logging.getLogger(__name__)

def generate_station_files_from_json(json_filepath, data_dir, model_id=None):
    """
    Generate CSV files for weather stations from a JSON file.
    
    Args:
        json_filepath (str): Path to the JSON file containing weather station data
        data_dir (str): Base directory for output data
        model_id (str, optional): Model ID to use, if not provided it will use the one in the JSON
        
    Returns:
        tuple: (model_id, csv_files, list_filepath)
    """
    logger.info(f"Generating station files from {json_filepath}")
    logger.debug(f"Received parameters: data_dir={data_dir}, model_id={model_id}")
    
    try:
        # Read the JSON if a filepath was provided, otherwise assume it's already loaded
        if isinstance(json_filepath, (str, Path)):
            logger.debug(f"Opening JSON file from path: {json_filepath}")
            with open(json_filepath, 'r') as jsonfile:
                json_data = json.load(jsonfile)
        else:
            logger.debug("Processing JSON data already loaded in memory")
            json_data = json_filepath
            json_filepath = "input JSON data"
        
        # Extract model_id from JSON if not specified
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID extracted from JSON: {model_id}")
            if not model_id:
                logger.error("Unable to find modelId in JSON")
                raise ValueError("modelId not found in JSON and not specified as parameter")
        
        # Generate CSV files for stations
        logger.debug(f"Starting CSV generation with model_id={model_id}")
        csv_files, list_filepath = json_to_station_csv(json_data, data_dir, model_id)
        logger.debug(f"CSV files generated: {len(csv_files)}")
        logger.debug(f"Station list file created: {list_filepath}")
        
        logger.info(f"Generation completed: {len(csv_files)} stations for model {model_id}")
        return model_id, csv_files, list_filepath
        
    except Exception as e:
        logger.error(f"Error generating station files from {json_filepath}: {str(e)}")
        raise

def download_elevation_file_from_minio(elevation_file_path, output_dir, model_id=None):
    """
    Download the elevation file from MinIO and save it to the specified directory
    
    Args:
        elevation_file_path (str): Path to the elevation file in MinIO
        output_dir (str): Directory where to save the file
        model_id (str, optional): Model ID, needed to send Kafka messages in case of error
        
    Returns:
        Path to the downloaded file
    """
    logger.debug(f"Starting download of elevation file from: {elevation_file_path}")
    logger.debug(f"Output directory: {output_dir}")
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Output directory verified: {output_dir}")
        
        # Get the filename from the path
        filename = os.path.basename(elevation_file_path)
        local_file_path = os.path.join(output_dir, filename)
        logger.debug(f"Local file path: {local_file_path}")
        
        # Initialize MinIO client and download the file
        logger.debug("Initializing MinIO client")
        minio_client = MinioClient()
        
        # Remove the file if it already exists to avoid conflicts
        # if os.path.exists(local_file_path):
        #     os.remove(local_file_path)
        
        # Download directly to the final path
        logger.debug("Starting file download...")
        minio_client.download_file(elevation_file_path, local_file_path)
        logger.debug(f"Download completed to: {local_file_path}")
        
        logger.info(f"Elevation file downloaded to {local_file_path}")
        return local_file_path
    except Exception as e:
        error_message = f"Error downloading elevation file '{elevation_file_path}' from MinIO: {str(e)}"
        logger.error(error_message)
        
        # If a model_id was provided, send a Kafka message
        if model_id:
            try:
                from ..messaging.kafka_producer import KafkaMessageProducer
                kafka_producer = KafkaMessageProducer()
                kafka_producer.send_simulation_failed(
                    simulation_id=model_id,
                    error_message=error_message
                )
                logger.info(f"Error message sent to Kafka for model {model_id}")
            except Exception as kafka_err:
                logger.error(f"Unable to send Kafka message: {str(kafka_err)}")
        
        # Re-raise the exception for higher-level handling
        raise ValueError(error_message) from e

def generate_windninja_config(json_data, data_dir, model_id=None, elevation_file=None, stations_list_file=None):
    """
    Generate a WindNinja configuration file from JSON data
    
    Args:
        json_data (dict): JSON data for configuration
        data_dir (str): Base directory for output data
        model_id (str, optional): Model ID, if not provided it will be taken from the JSON
        elevation_file (str, optional): Local path to the elevation file, if already downloaded
        stations_list_file (str, optional): Path to the station list file
        
    Returns:
        str: Path to the generated configuration file
    """
    logger.info("Generating WindNinja configuration file")
    logger.debug(f"Parameters: data_dir={data_dir}, model_id={model_id}, elevation_file={elevation_file}, stations_list_file={stations_list_file}")
    
    try:
        # Extract model_id from JSON if not specified
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID extracted from JSON: {model_id}")
            if not model_id:
                logger.error("Unable to find modelId in JSON")
                raise ValueError("modelId not found in JSON and not specified as parameter")
        
        # Create input and output directories
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Directories created: input={input_dir}, output={output_dir}")
        
        # If the stations file is not specified, use the one in input_dir
        if not stations_list_file:
            stations_list_file = os.path.join(input_dir, "stations_list.txt")
            logger.debug(f"Using default stations file: {stations_list_file}")
        
        # If the elevation file is not specified, download it from MinIO
        if not elevation_file and 'elevation_file' in json_data:
            elevation_file_path = json_data.get('elevation_file')
            logger.debug(f"Elevation file to download: {elevation_file_path}")
            elevation_file = download_elevation_file_from_minio(
                elevation_file_path, 
                input_dir, 
                model_id
            )
            logger.debug(f"Elevation file downloaded: {elevation_file}")
        elif not elevation_file:
            logger.error("Elevation file not specified and not present in JSON")
            raise ValueError("Elevation file not specified and not present in JSON")
            
        # Path to the configuration file to generate
        config_file_path = os.path.join(input_dir, f"{model_id}_windninja.cfg")
        logger.debug(f"Configuration file path: {config_file_path}")
        
        # Create the configuration file content
        logger.debug("Creating configuration file content")
        config_content = [
            "#",
            "#\tAutomatically generated WindNinja configuration file",
            "#",
            f"num_threads              = 1",
            f"elevation_file           = {elevation_file}",
            f"time_zone                = auto-detect",
            f"initialization_method    = pointInitialization",
            f"match_points             = true",
            f"wx_station_filename      = {stations_list_file}",
            f"write_wx_station_kml     = true"
        ]
        
        # Add optional parameters from JSON if present
        if 'output_wind_height' in json_data:
            logger.debug(f"Adding output_wind_height parameter: {json_data['output_wind_height']}")
            config_content.append(f"output_wind_height       = {json_data['output_wind_height']}")
        
        if 'units_output_wind_height' in json_data:
            logger.debug(f"Adding units_output_wind_height parameter: {json_data['units_output_wind_height']}")
            config_content.append(f"units_output_wind_height = {json_data['units_output_wind_height']}")
        
        if 'vegetation' in json_data:
            logger.debug(f"Adding vegetation parameter: {json_data['vegetation']}")
            config_content.append(f"vegetation               = {json_data['vegetation']}")
        
        # Add default output settings
        logger.debug("Adding default output parameters")
        config_content.extend([
            f"output_speed_units       = mps",
            f"mesh_resolution          = 500.0",
            f"units_mesh_resolution    = m",
            f"write_goog_output        = true",
            f"write_shapefile_output   = true",
            f"write_ascii_output       = true",
            f"write_farsite_atm        = false"
        ])
        
        # Write the configuration file
        logger.debug(f"Writing configuration file: {config_file_path}")
        with open(config_file_path, 'w') as config_file:
            config_file.write('\n'.join(config_content))
        
        logger.info(f"WindNinja configuration file generated: {config_file_path}")
        return config_file_path
        
    except Exception as e:
        logger.error(f"Error generating WindNinja configuration file: {str(e)}")
        raise

def process_windninja_input(json_filepath, data_dir, model_id=None):
    """
    Process input data for WindNinja: generate CSV station files,
    download the elevation file and create the configuration file
    
    Args:
        json_filepath (str or dict): Path to the JSON file or already loaded JSON dictionary
        data_dir (str): Base directory for output data
        model_id (str, optional): Model ID, if not provided it will be taken from the JSON
        
    Returns:
        tuple: (model_id, csv_files, elevation_file, config_file)
    """
    logger.info(f"Processing WindNinja input data from {json_filepath}")
    logger.debug(f"Parameters: data_dir={data_dir}, model_id={model_id}")
    
    try:
        # Read the JSON if a filepath was provided, otherwise assume it's already loaded
        if isinstance(json_filepath, (str, Path)):
            logger.debug(f"Opening JSON file from path: {json_filepath}")
            with open(json_filepath, 'r') as jsonfile:
                json_data = json.load(jsonfile)
        else:
            logger.debug("Processing JSON data already loaded in memory")
            json_data = json_filepath
            json_filepath = "input JSON data"
        
        # Extract model_id from JSON if not specified
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID extracted from JSON: {model_id}")
            if not model_id:
                logger.error("Unable to find modelId in JSON")
                raise ValueError("modelId not found in JSON and not specified as parameter")
        
        # Create input and output directories
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        logger.debug(f"Creating directories: input={input_dir}, output={output_dir}")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate CSV files for stations
        logger.debug("Starting station file generation")
        _, csv_files, stations_list_file = generate_station_files_from_json(json_data, data_dir, model_id)
        logger.debug(f"Station files generated: {len(csv_files)}")
        logger.debug(f"Station list file: {stations_list_file}")
        
        # Download the elevation file from MinIO
        elevation_file = None
        if 'elevation_file' in json_data:
            logger.debug(f"Starting elevation file download: {json_data['elevation_file']}")
            elevation_file = download_elevation_file_from_minio(
                json_data['elevation_file'], 
                input_dir,
                model_id  # Pass model_id to the download function
            )
            logger.debug(f"Elevation file downloaded: {elevation_file}")
        else:
            logger.debug("No elevation file specified in JSON")
        
        # Generate the WindNinja configuration file
        logger.debug("Starting WindNinja configuration file generation")
        config_file = generate_windninja_config(
            json_data, 
            data_dir, 
            model_id, 
            elevation_file, 
            stations_list_file
        )
        logger.debug(f"Configuration file generated: {config_file}")
        
        logger.info(f"Processing completed for model {model_id}")
        return model_id, csv_files, elevation_file, config_file
        
    except Exception as e:
        logger.error(f"Error processing WindNinja input data: {str(e)}")
        raise