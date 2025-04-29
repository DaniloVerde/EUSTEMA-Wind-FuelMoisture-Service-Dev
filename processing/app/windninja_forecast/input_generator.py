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
    logger.debug(
        f"Received parameters: data_dir={data_dir}, model_id={model_id}")

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
                raise ValueError(
                    "modelId not found in JSON and not specified as parameter")

        # Generate CSV files for stations
        logger.debug(f"Starting CSV generation with model_id={model_id}")
        csv_files, list_filepath = json_to_station_csv(
            json_data, data_dir, model_id)
        logger.debug(f"CSV files generated: {len(csv_files)}")
        logger.debug(f"Station list file created: {list_filepath}")

        logger.info(
            f"Generation completed: {len(csv_files)} stations for model {model_id}")
        return model_id, csv_files, list_filepath

    except Exception as e:
        logger.error(
            f"Error generating station files from {json_filepath}: {str(e)}")
        raise


def download_file_from_minio(file_path, output_dir, model_id=None, file_type="generic"):
    """
    Download a file from MinIO and save it to the specified directory

    Args:
        file_path (str): Path to the file in MinIO
        output_dir (str): Directory where to save the file
        model_id (str, optional): Model ID, needed to send Kafka messages in case of error
        file_type (str, optional): File type for log messages, default "generic"

    Returns:
        str: Path to the downloaded file
    """
    logger.debug(f"Starting download of {file_type} file from: {file_path}")
    logger.debug(f"Output directory: {output_dir}")

    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Output directory verified: {output_dir}")

        # Get the filename from the path
        filename = os.path.basename(file_path)
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
        minio_client.download_file(file_path, local_file_path)
        logger.debug(f"Download completed to: {local_file_path}")

        logger.info(f"{file_type.capitalize()} file downloaded to {local_file_path}")
        return local_file_path
    except Exception as e:
        error_message = f"Error downloading {file_type} file '{file_path}' from MinIO: {str(e)}"
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
                logger.info(
                    f"Error message sent to Kafka for model {model_id}")
            except Exception as kafka_err:
                logger.error(
                    f"Unable to send Kafka message: {str(kafka_err)}")

        # Re-raise the exception for higher-level handling
        raise ValueError(error_message) from e


def generate_windninja_config(json_data, data_dir, model_id=None, elevation_file=None, wind_speed_file=None, wind_direction_file=None):
    """
    Generate a WindNinja forecast configuration file from JSON data

    Args:
        json_data (dict): JSON data for configuration
        data_dir (str): Base directory for output data
        model_id (str, optional): Model ID, if not provided it will be taken from the JSON
        elevation_file (str, optional): Local path to the elevation file, if already downloaded
        wind_speed_file (str, optional): Local path to the wind speed file, if already downloaded
        wind_direction_file (str, optional): Local path to the wind direction file, if already downloaded

    Returns:
        str: Path to the generated configuration file
    """
    logger.info("Generating WindNinja forecast configuration file")
    logger.debug(
        f"Parameters: data_dir={data_dir}, model_id={model_id}, elevation_file={elevation_file}, wind_speed_file={wind_speed_file}, wind_direction_file={wind_direction_file}")

    try:
        # Extract model_id from JSON if not specified
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID extracted from JSON: {model_id}")
            if not model_id:
                logger.error("Unable to find modelId in JSON")
                raise ValueError(
                    "modelId not found in JSON and not specified as parameter")

        # Create input and output directories
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(
            f"Directories created: input={input_dir}, output={output_dir}")

        # If the elevation file is not specified, download it from MinIO
        if not elevation_file and 'elevation_file' in json_data:
            elevation_file_path = json_data.get('elevation_file')
            logger.debug(
                f"Elevation file to download: {elevation_file_path}")
            elevation_file = download_file_from_minio(
                elevation_file_path,
                input_dir,
                model_id
            )
            logger.debug(f"Elevation file downloaded: {elevation_file}")
        elif not elevation_file:
            logger.error(
                "Elevation file not specified and not present in JSON")
            raise ValueError(
                "Elevation file not specified and not present in JSON")

        # If the wind speed file is not specified, download it from MinIO
        if not wind_speed_file and 'wind_speed_file' in json_data:
            wind_speed_file_path = json_data.get('wind_speed_file')
            logger.debug(
                f"Wind speed file to download: {wind_speed_file_path}")
            wind_speed_file = download_file_from_minio(
                wind_speed_file_path,
                input_dir,
                model_id
            )
            logger.debug(f"Wind speed file downloaded: {wind_speed_file}")
        
        # If the wind direction file is not specified, download it from MinIO
        if not wind_direction_file and 'wind_direction_file' in json_data:
            wind_direction_file_path = json_data.get('wind_direction_file')
            logger.debug(
                f"Wind direction file to download: {wind_direction_file_path}")
            wind_direction_file = download_file_from_minio(
                wind_direction_file_path,
                input_dir,
                model_id
            )
            logger.debug(f"Wind direction file downloaded: {wind_direction_file}")

        # Path of the configuration file to generate
        config_file_path = os.path.join(input_dir, f"{model_id}_windninja_forecast.cfg")
        logger.debug(f"Configuration file path: {config_file_path}")

        # Extract and split simulation_time
        simulation_time = json_data.get('simulation_time', '')
        logger.debug(f"Simulation time: {simulation_time}")
        
        # Format as "2024-04-28T15:30"
        try:
            # Extract date and time components from ISO format
            from datetime import datetime
            dt = datetime.fromisoformat(simulation_time)
            year = dt.year
            month = dt.month
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            logger.debug(f"Time components extracted: year={year}, month={month}, day={day}, hour={hour}, minute={minute}")
        except Exception as e:
            logger.warning(f"Error parsing simulation_time date '{simulation_time}': {str(e)}")
            # Default values in case of error
            year = datetime.now().year
            month = datetime.now().month
            day = datetime.now().day
            hour = datetime.now().hour
            minute = datetime.now().minute
            logger.debug(f"Using default values: year={year}, month={month}, day={day}, hour={hour}, minute={minute}")

        # Create the configuration file content
        logger.debug("Creating configuration file content")
        config_content = [
            "#",
            "#\tAutomatically generated WindNinja forecast configuration file",
            "#",
            f"num_threads              = 4",
            f"elevation_file           = {elevation_file}",
            f"time_zone                = auto-detect",
            f"initialization_method    = griddedInitialization",
            f"match_points             = true",
            f"write_wx_station_kml     = true",
            f"input_speed_grid         = {wind_speed_file}",
            f"input_speed_units        = {json_data['input_speed_units']}",
            f"input_dir_grid           = {wind_direction_file}",
            f"input_wind_height        = {json_data['input_wind_height']}",
            f"units_input_wind_height  = {json_data['units_input_wind_height']}",
            f"diurnal_winds            = true",
            f"year                     = {year}",
            f"month                    = {month}",
            f"day                      = {day}",
            f"hour                     = {hour}",
            f"minute                   = {minute}",
            f"output_speed_units       = mps",
            f"output_wind_height       = {json_data['output_wind_height']}",
            f"units_output_wind_height = {json_data['units_output_wind_height']}",
            f"vegetation               = {json_data['vegetation']}",
            f"uni_air_temp             = {json_data['uni_air_temp']}",
            f"air_temp_units           = C",
            f"uni_cloud_cover          = {json_data['uni_cloud_cover']}",
            f"cloud_cover_units        = percent",
            f"mesh_resolution          = 500.0",
            f"units_mesh_resolution    = m",
            f"write_goog_output        = true",
            f"write_shapefile_output   = true",
            f"write_ascii_output       = true",
            f"write_farsite_atm        = false"
        ]

        # Write the configuration file
        logger.debug(f"Writing configuration file: {config_file_path}")
        with open(config_file_path, 'w') as config_file:
            config_file.write('\n'.join(config_content))

        logger.info(
            f"WindNinja configuration file generated: {config_file_path}")
        return config_file_path

    except Exception as e:
        logger.error(
            f"Error generating WindNinja configuration file: {str(e)}")
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
                raise ValueError(
                    "modelId not found in JSON and not specified as parameter")

        # Create input and output directories
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        logger.debug(
            f"Creating directories: input={input_dir}, output={output_dir}")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Download the elevation file from MinIO
        elevation_file = None
        if 'elevation_file' in json_data:
            logger.debug(
                f"Starting elevation file download: {json_data['elevation_file']}")
            elevation_file = download_file_from_minio(
                json_data['elevation_file'],
                input_dir,
                model_id,
                file_type="elevation",
            )
            logger.debug(f"Elevation file downloaded: {elevation_file}")
        else:
            logger.debug("No elevation file specified in JSON")

        wind_speed_file = None
        if 'wind_speed_file' in json_data:
            logger.debug(
                f"Starting wind speed file download: {json_data['wind_speed_file']}")
            wind_speed_file = download_file_from_minio(
                json_data['wind_speed_file'],
                input_dir,
                model_id,
                file_type="wind speed",
            )
            logger.debug(
                f"Wind speed file downloaded: {wind_speed_file}")
        else:
            logger.debug(
                "No wind speed file specified in JSON")

        wind_direction_file = None
        if 'wind_direction_file' in json_data:
            logger.debug(
                f"Starting wind direction file download: {json_data['wind_direction_file']}")
            wind_direction_file = download_file_from_minio(
                json_data['wind_direction_file'],
                input_dir,
                model_id,
                file_type="wind direction",
            )
            logger.debug(
                f"Wind direction file downloaded: {wind_direction_file}")
        else:
            logger.debug(
                "No wind direction file specified in JSON")

        # Generate the WindNinja configuration file
        logger.debug("Starting WindNinja configuration file generation")
        config_file = generate_windninja_config(
            json_data,
            data_dir,
            model_id,
            elevation_file=elevation_file,
            wind_speed_file=wind_speed_file,
            wind_direction_file=wind_direction_file
        )
        logger.debug(f"Configuration file generated: {config_file}")

        logger.info(f"Processing completed for model {model_id}")
        return model_id, elevation_file, wind_speed_file, wind_direction_file, config_file

    except Exception as e:
        logger.error(
            f"Error processing WindNinja input data: {str(e)}")
        raise
