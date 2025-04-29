import json
import time
import logging
import argparse
from datetime import datetime
from kafka import KafkaConsumer
from colorama import Fore, Style, init

# Initialize colorama for color support on Windows
init()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("kafka_consumer")

class KafkaMessageConsumer:
    """Kafka Consumer to monitor WindNinja processing messages."""
    
    def __init__(self, bootstrap_servers, topic, group_id=None, simulation_id=None):
        """
        Initialize the Kafka consumer.
        
        Args:
            bootstrap_servers: List of Kafka bootstrap servers
            topic: Kafka topic to consume messages from
            group_id: Group ID for the consumer, if None a new group is created
            simulation_id: If specified, filter only messages for this simulation
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id or f"windninja-monitor-{int(time.time())}"
        self.simulation_id = simulation_id
        self.active = True
        self.last_progress = {}  # To store the last progress of each simulation
        
        logger.info(f"Initializing Kafka consumer with bootstrap servers: {bootstrap_servers}")
        logger.info(f"Topic: {topic}, Group ID: {self.group_id}")
        if simulation_id:
            logger.info(f"Filtering messages for simulation_id: {simulation_id}")
    
    def initialize_consumer(self):
        """Initialize the Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info("Kafka consumer successfully initialized")
            return True
        except Exception as e:
            logger.error(f"Error initializing Kafka consumer: {str(e)}")
            return False
    
    def start_consuming(self):
        """Start consuming messages from the topic."""
        if not hasattr(self, 'consumer'):
            if not self.initialize_consumer():
                logger.error("Unable to start consuming: consumer not initialized")
                return
        
        logger.info(f"Starting message consumption from topic {self.topic}")
        print(f"\n{Fore.CYAN}===== WindNinja Messages Monitoring =====")
        print(f"Topic: {self.topic}")
        if self.simulation_id:
            print(f"Filtering by Simulation ID: {self.simulation_id}{Style.RESET_ALL}\n")
        else:
            print(f"Monitoring all simulations{Style.RESET_ALL}\n")
        
        try:
            for message in self.consumer:
                if not self.active:
                    break
                
                value = message.value
                
                # Filter by simulation_id if specified
                if self.simulation_id and value.get('simulation_id') != self.simulation_id:
                    continue
                
                self.process_message(value)
        except KeyboardInterrupt:
            logger.info("Keyboard interruption, stopping consumer")
            print(f"\n{Fore.YELLOW}Monitoring interrupted by user{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Error while consuming messages: {str(e)}")
            print(f"\n{Fore.RED}Error during monitoring: {str(e)}{Style.RESET_ALL}")
        finally:
            self.close()
    
    def process_message(self, message):
        """
        Process a message received from Kafka.
        
        Args:
            message: The deserialized message received from Kafka
        """
        event_type = message.get('event_type')
        simulation_id = message.get('simulation_id', 'unknown')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        
        # Format date/time for display
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            formatted_time = timestamp
        
        if event_type == 'simulation_progress':
            progress = message.get('progress', 0)
            status = message.get('status', '')
            
            # Store the last progress for this simulation
            self.last_progress[simulation_id] = progress
            
            # Format the progress bar
            progress_bar = self.format_progress_bar(progress)
            
            print(f"{Fore.BLUE}[{formatted_time}] {Fore.GREEN}Simulation {simulation_id}: {progress}% {progress_bar}")
            print(f"{Fore.CYAN}    {status}{Style.RESET_ALL}")
            
        elif event_type == 'simulation_complete':
            status = message.get('status', 'completed')
            results_url = message.get('results_url', '')
            
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.GREEN}Simulation {simulation_id}: {Fore.YELLOW}COMPLETED")
            print(f"{Fore.GREEN}    Status: {status}")
            print(f"{Fore.GREEN}    Results available at: {Fore.CYAN}{results_url}{Style.RESET_ALL}")
            
        elif event_type == 'simulation_failed':
            error = message.get('error', 'Unknown error')
            
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.RED}Simulation {simulation_id}: FAILED")
            print(f"{Fore.RED}    Error: {error}{Style.RESET_ALL}")
            
        else:
            # Unknown message types
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.YELLOW}Unknown message for simulation {simulation_id}:")
            print(f"{Fore.YELLOW}    Type: {event_type}")
            print(f"{Fore.YELLOW}    Content: {json.dumps(message, indent=2)}{Style.RESET_ALL}")
    
    def format_progress_bar(self, progress, width=30):
        """
        Format a text progress bar.
        
        Args:
            progress: Completion percentage (0-100)
            width: Width of the progress bar in characters
            
        Returns:
            String with the progress bar
        """
        try:
            progress = float(progress)
            # Ensure progress is between 0 and 100
            progress = max(0, min(100, progress))
            
            # Calculate how many "filled" characters to show
            completed = int(width * progress / 100)
            
            # Build the progress bar
            bar = '█' * completed + '░' * (width - completed)
            
            return f"[{bar}]"
        except (ValueError, TypeError):
            return f"[{'?' * width}]"
    
    def close(self):
        """Close the consumer."""
        if hasattr(self, 'consumer'):
            self.consumer.close()
            logger.info("Kafka consumer closed")
        self.active = False


def main():
    """Main function for running the consumer from command line."""
    parser = argparse.ArgumentParser(description='Kafka Consumer to monitor WindNinja processing messages')
    
    parser.add_argument('--bootstrap-servers', type=str, default='localhost:9092',
                        help='List of Kafka bootstrap servers (default: localhost:9092)')
    parser.add_argument('--topic', type=str, default='windninja-events',
                        help='Kafka topic to consume messages from (default: windninja-events)')
    parser.add_argument('--group-id', type=str, default=None,
                        help='Group ID for the Kafka consumer (default: automatically generated)')
    parser.add_argument('--simulation-id', type=str, default=None,
                        help='Filter messages for a specific simulation ID')
    
    args = parser.parse_args()
    
    # Create and start the consumer
    consumer = KafkaMessageConsumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group_id,
        simulation_id=args.simulation_id
    )
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("\nClosing consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()