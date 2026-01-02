import json
from datetime import datetime
from kafka import KafkaProducer
from ..config import get_logger
from ..config.settings import (
    KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_RESULTS, KAFKA_SECURITY_PROTOCOL,
    KAFKA_SASL_MECHANISM, KAFKA_USERNAME, KAFKA_PASSWORD,
    KAFKA_SESSION_TIMEOUT_MS, KAFKA_REQUEST_TIMEOUT_MS
)

# Get module logger
logger = get_logger(__name__)

class KafkaMessageProducer:
    def __init__(self, resource_provider: str):
        logger.info(f"Initializing Kafka producer with bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
        try:
            producer_config = {
                "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
                "value_serializer": lambda v: json.dumps(v).encode('utf-8'),
                "security_protocol": KAFKA_SECURITY_PROTOCOL,
                "request_timeout_ms": KAFKA_REQUEST_TIMEOUT_MS,
            }
            if KAFKA_SECURITY_PROTOCOL and KAFKA_SECURITY_PROTOCOL.startswith("SASL"):
                producer_config["sasl_mechanism"] = KAFKA_SASL_MECHANISM
                producer_config["sasl_plain_username"] = KAFKA_USERNAME
                producer_config["sasl_plain_password"] = KAFKA_PASSWORD

            self.producer = KafkaProducer(**producer_config)
            self.topic = KAFKA_TOPIC_RESULTS.format(cu=resource_provider)
            logger.info(f"Kafka producer initialized successfully with topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            raise
    
    def send_simulation_complete(self, simulation_id, status, results_url, file_names):
        """
        Send a message that a simulation has completed
        
        Args:
            simulation_id: Unique identifier for the simulation
            status: Status of the simulation (usually 'completed')
            results_url: URL where the results can be accessed
            file_names: produced file names as a list
        """
        try:
            message = {
                "event_type": "simulation_complete", # replace with OK
                "simulation_id": simulation_id,
                "status": "OK",
                "results_url": results_url,
                "file_names": file_names,
                "timestamp": datetime.now().isoformat(),
                "sender": "windninja"
            }
            
            logger.info(f"Sending simulation_complete message for simulation {simulation_id}")
            logger.debug(f"Message content: {message}")
            
            future = self.producer.send(self.topic, message)
            self.producer.flush()
            
            # Get the result to ensure the message was sent
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to {record_metadata.topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending simulation_complete message: {str(e)}")
            return False
    
    def send_simulation_failed(self, simulation_id, error_message):
        """
        Send a message that a simulation has failed
        
        Args:
            simulation_id: Unique identifier for the simulation
            error_message: Description of the error that occurred
        """
        try:
            # TODO: send the same structure of simulation_complete with "message" key for error message
            message = {
                "event_type": "simulation_failed", # replace with KO
                "simulation_id": simulation_id,
                "status": "KO",
                "message": error_message,
                "timestamp": datetime.now().isoformat(),
                "sender": "windninja"
            }
            
            logger.info(f"Sending simulation_failed message for simulation {simulation_id}")
            logger.debug(f"Message content: {message}")
            
            future = self.producer.send(self.topic, message)
            self.producer.flush()
            
            # Get the result to ensure the message was sent
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to {record_metadata.topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending simulation_failed message: {str(e)}")
            return False
    
    def send_simulation_progress(self, simulation_id, progress_percentage, status_message):
        """
        Send a message about the progress of a simulation
        
        Args:
            simulation_id: Unique identifier for the simulation
            progress_percentage: Integer percentage of completion (0-100)
            status_message: Description of the current status
        """
        try:
            message = {
                "event_type": "simulation_progress",
                "simulation_id": simulation_id,
                "progress": progress_percentage,
                "status": status_message,
                "timestamp": datetime.now().isoformat(),
                "sender": "windninja"
            }
            
            logger.info(f"Sending simulation_progress message for simulation {simulation_id}: {progress_percentage}% - {status_message}")
            
            future = self.producer.send(self.topic, message)
            self.producer.flush()
            
            # For progress messages, we can be less verbose in logging
            if progress_percentage % 20 == 0:  # Log only at 0%, 20%, 40%, 60%, 80%, 100%
                record_metadata = future.get(timeout=10)
                logger.debug(f"Progress message sent to {record_metadata.topic}, partition {record_metadata.partition}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending simulation_progress message: {str(e)}")
            return False
