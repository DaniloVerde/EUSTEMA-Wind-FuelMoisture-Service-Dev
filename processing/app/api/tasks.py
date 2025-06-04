import os
import logging
import traceback
from functools import wraps

from app.config.settings import DATA_DIR
from app.windninja.input_generator import process_windninja_input
from app.windninja.runner import run_windninja
from app.windninja_forecast.input_generator import process_windninja_input as process_forecast_input
from app.windninja_forecast.runner import run_windninja as run_forecast_windninja
from app.messaging.kafka_producer import KafkaMessageProducer
from app.storage.minio_client import MinioClient

# Get module logger
logger = logging.getLogger(__name__)

def with_error_handling(func):
    """Decorator to handle errors in background tasks and send Kafka messages."""
    @wraps(func)
    def wrapper(model_id, *args, **kwargs):
        kafka_producer = KafkaMessageProducer()
        try:
            return func(model_id, *args, **kwargs)
        except Exception as e:
            error_message = f"Error processing WindNinja for model {model_id}: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Send error message to Kafka
            kafka_producer.send_simulation_failed(model_id, error_message)
            raise
    return wrapper

@with_error_handling
def process_windninja_request(model_id, json_data):
    """
    Process a WindNinja request in the background.
    
    Args:
        model_id: ID of the model to process
        json_data: JSON data with the request parameters
    """
    logger.info(f"Starting background processing for model {model_id}")
    
    # Initialize Kafka producer
    kafka_producer = KafkaMessageProducer()
    
    try:
        # Send progress message: Starting
        # kafka_producer.send_simulation_progress(model_id, 0, "Starting WindNinja processing")
        
        # Process input data
        logger.info(f"Processing input data for model {model_id}")
        # kafka_producer.send_simulation_progress(model_id, 10, "Processing input data")
        
        _, csv_files, elevation_file, config_file = process_windninja_input(json_data, DATA_DIR)
        
        # Get input and output directories
        input_dir = os.path.join(DATA_DIR, model_id, "input")
        output_dir = os.path.join(DATA_DIR, model_id, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Send progress message: Input processed
        # kafka_producer.send_simulation_progress(model_id, 30, "Input data processed, running WindNinja")
        
        # Run WindNinja with the generated configuration
        logger.info(f"Running WindNinja for model {model_id}")
        exit_code, stdout, stderr = run_windninja(config_file, working_dir=input_dir, output_dir=output_dir)
        
        if exit_code != 0:
            logger.error(f"WindNinja failed with exit code {exit_code}")
            logger.error(f"Stderr: {stderr}")
            error_message = f"WindNinja execution failed with exit code {exit_code}: {stderr}"
            kafka_producer.send_simulation_failed(model_id, error_message)
            return
        
        # Send progress message: WindNinja completed
        # kafka_producer.send_simulation_progress(model_id, 70, "WindNinja processing completed, uploading results")
        
        # Initialize MinIO client
        minio_client = MinioClient()
        
        # Derive the MinIO path from the elevation file path
        elevation_file_path = json_data.get('elevation_file')
        minio_base_path = os.path.dirname(os.path.dirname(elevation_file_path))
        results_path = f"{minio_base_path}/output"
        
        # Upload results to MinIO
        logger.info(f"Uploading results to MinIO at {results_path}")
        
        uploaded_files = []
        for root, _, files in os.walk(output_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_file_path, output_dir)
                minio_object_name = f"{results_path}/{rel_path}"
                
                # Upload the file
                minio_client.upload_file(local_file_path, minio_object_name)
                uploaded_files.append(minio_object_name)
        
        # Send progress message: Results uploaded
        # kafka_producer.send_simulation_progress(model_id, 90, "Results uploaded to storage")
        
        # Send completion message
        logger.info(f"Processing completed for model {model_id}")
        results_url = f"{results_path}"
        kafka_producer.send_simulation_complete(model_id, "completed", results_url)
        
        # Send progress message: Processing completed
        # kafka_producer.send_simulation_progress(model_id, 100, "Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in background processing for model {model_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Send error message to Kafka
        error_message = f"Error in WindNinja processing: {str(e)}"
        kafka_producer.send_simulation_failed(model_id, error_message)
        raise


@with_error_handling
def process_windninja_forecast_request(model_id, json_data):
    """
    Process a WindNinja forecast request in the background.
    
    Args:
        model_id: ID of the model to process
        json_data: JSON data with the request parameters
    """
    logger.info(f"Starting background processing for model {model_id}")
    
    # Initialize Kafka producer
    kafka_producer = KafkaMessageProducer()
    
    try:
        # Send progress message: Starting
        # kafka_producer.send_simulation_progress(model_id, 0, "Starting WindNinja forecast processing")
        
        # Process input data
        logger.info(f"Processing input data for model {model_id}")
        # kafka_producer.send_simulation_progress(model_id, 10, "Processing input data")
        
        _, elevation_file, wind_speed_file, wind_direction_file, config_file = process_forecast_input(json_data, DATA_DIR)
        
        # Get input and output directories
        input_dir = os.path.join(DATA_DIR, model_id, "input")
        output_dir = os.path.join(DATA_DIR, model_id, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Send progress message: Input processed
        # kafka_producer.send_simulation_progress(model_id, 30, "Input data processed, running WindNinja")
        
        # Run WindNinja with the generated configuration
        logger.info(f"Running WindNinja for model {model_id}")
        exit_code, stdout, stderr = run_forecast_windninja(config_file, working_dir=input_dir, output_dir=output_dir)
        
        if exit_code != 0:
            logger.error(f"WindNinja failed with exit code {exit_code}")
            logger.error(f"Stderr: {stderr}")
            error_message = f"WindNinja execution failed with exit code {exit_code}: {stderr}"
            kafka_producer.send_simulation_failed(model_id, error_message)
            return
        
        # Send progress message: WindNinja completed
        # kafka_producer.send_simulation_progress(model_id, 70, "WindNinja processing completed, uploading results")
        
        # Initialize MinIO client
        minio_client = MinioClient()
        
        # Derive the MinIO path from the elevation file path
        elevation_file_path = json_data.get('elevation_file')
        minio_base_path = os.path.dirname(os.path.dirname(elevation_file_path))
        results_path = f"{minio_base_path}/output"
        
        # Upload results to MinIO
        logger.info(f"Uploading results to MinIO at {results_path}")
        
        uploaded_files = []
        for root, _, files in os.walk(output_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(local_file_path, output_dir)
                minio_object_name = f"{results_path}/{rel_path}"
                
                # Upload the file
                minio_client.upload_file(local_file_path, minio_object_name)
                uploaded_files.append(minio_object_name)
        
        # Send progress message: Results uploaded
        # kafka_producer.send_simulation_progress(model_id, 90, "Results uploaded to storage")
        
        # Send completion message
        logger.info(f"Processing completed for model {model_id}")
        results_url = f"{results_path}"
        kafka_producer.send_simulation_complete(model_id, "completed", results_url)
        
        # Send progress message: Processing completed
        # kafka_producer.send_simulation_progress(model_id, 100, "Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in background processing for model {model_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Send error message to Kafka
        error_message = f"Error in WindNinja processing: {str(e)}"
        kafka_producer.send_simulation_failed(model_id, error_message)
        raise