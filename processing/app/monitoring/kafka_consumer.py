import json
import time
import logging
import argparse
from datetime import datetime
from kafka import KafkaConsumer
from colorama import Fore, Style, init

# Inizializza colorama per il supporto dei colori su Windows
init()

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("kafka_consumer")

class KafkaMessageConsumer:
    """Consumer Kafka per monitorare i messaggi di elaborazione WindNinja."""
    
    def __init__(self, bootstrap_servers, topic, group_id=None, simulation_id=None):
        """
        Inizializza il consumer Kafka.
        
        Args:
            bootstrap_servers: Lista di server bootstrap Kafka
            topic: Topic Kafka da cui consumare i messaggi
            group_id: Group ID per il consumer, se None viene creato un nuovo gruppo
            simulation_id: Se specificato, filtra solo i messaggi di questa simulazione
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id or f"windninja-monitor-{int(time.time())}"
        self.simulation_id = simulation_id
        self.active = True
        self.last_progress = {}  # Per memorizzare l'ultimo progresso di ogni simulazione
        
        logger.info(f"Inizializzazione consumer Kafka con bootstrap servers: {bootstrap_servers}")
        logger.info(f"Topic: {topic}, Group ID: {self.group_id}")
        if simulation_id:
            logger.info(f"Filtraggio messaggi per simulation_id: {simulation_id}")
    
    def initialize_consumer(self):
        """Inizializza il consumer Kafka."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info("Consumer Kafka inizializzato con successo")
            return True
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione del consumer Kafka: {str(e)}")
            return False
    
    def start_consuming(self):
        """Inizia a consumare messaggi dal topic."""
        if not hasattr(self, 'consumer'):
            if not self.initialize_consumer():
                logger.error("Impossibile iniziare a consumare: consumer non inizializzato")
                return
        
        logger.info(f"Inizio consumo messaggi da topic {self.topic}")
        print(f"\n{Fore.CYAN}===== Monitoraggio messaggi WindNinja =====")
        print(f"Topic: {self.topic}")
        if self.simulation_id:
            print(f"Filtraggio per Simulation ID: {self.simulation_id}{Style.RESET_ALL}\n")
        else:
            print(f"Monitoraggio tutte le simulazioni{Style.RESET_ALL}\n")
        
        try:
            for message in self.consumer:
                if not self.active:
                    break
                
                value = message.value
                
                # Filtra per simulation_id se specificato
                if self.simulation_id and value.get('simulation_id') != self.simulation_id:
                    continue
                
                self.process_message(value)
        except KeyboardInterrupt:
            logger.info("Interruzione da tastiera, arresto del consumer")
            print(f"\n{Fore.YELLOW}Monitoraggio interrotto dall'utente{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"Errore durante il consumo dei messaggi: {str(e)}")
            print(f"\n{Fore.RED}Errore durante il monitoraggio: {str(e)}{Style.RESET_ALL}")
        finally:
            self.close()
    
    def process_message(self, message):
        """
        Elabora un messaggio ricevuto da Kafka.
        
        Args:
            message: Il messaggio deserializzato ricevuto da Kafka
        """
        event_type = message.get('event_type')
        simulation_id = message.get('simulation_id', 'unknown')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        
        # Formatta la data/ora per la visualizzazione
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            formatted_time = timestamp
        
        if event_type == 'simulation_progress':
            progress = message.get('progress', 0)
            status = message.get('status', '')
            
            # Memorizza l'ultimo progresso per questa simulazione
            self.last_progress[simulation_id] = progress
            
            # Formatta la barra di progresso
            progress_bar = self.format_progress_bar(progress)
            
            print(f"{Fore.BLUE}[{formatted_time}] {Fore.GREEN}Simulazione {simulation_id}: {progress}% {progress_bar}")
            print(f"{Fore.CYAN}    {status}{Style.RESET_ALL}")
            
        elif event_type == 'simulation_complete':
            status = message.get('status', 'completed')
            results_url = message.get('results_url', '')
            
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.GREEN}Simulazione {simulation_id}: {Fore.YELLOW}COMPLETATA")
            print(f"{Fore.GREEN}    Stato: {status}")
            print(f"{Fore.GREEN}    Risultati disponibili in: {Fore.CYAN}{results_url}{Style.RESET_ALL}")
            
        elif event_type == 'simulation_failed':
            error = message.get('error', 'Unknown error')
            
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.RED}Simulazione {simulation_id}: FALLITA")
            print(f"{Fore.RED}    Errore: {error}{Style.RESET_ALL}")
            
        else:
            # Messaggi di tipo sconosciuto
            print(f"\n{Fore.BLUE}[{formatted_time}] {Fore.YELLOW}Messaggio sconosciuto per simulazione {simulation_id}:")
            print(f"{Fore.YELLOW}    Tipo: {event_type}")
            print(f"{Fore.YELLOW}    Contenuto: {json.dumps(message, indent=2)}{Style.RESET_ALL}")
    
    def format_progress_bar(self, progress, width=30):
        """
        Formatta una barra di progresso testuale.
        
        Args:
            progress: Percentuale di completamento (0-100)
            width: Larghezza della barra di progresso in caratteri
            
        Returns:
            Stringa con la barra di progresso
        """
        try:
            progress = float(progress)
            # Assicura che il progresso sia tra 0 e 100
            progress = max(0, min(100, progress))
            
            # Calcola quanti caratteri di "pieno" mostrare
            completed = int(width * progress / 100)
            
            # Costruisci la barra di progresso
            bar = '█' * completed + '░' * (width - completed)
            
            return f"[{bar}]"
        except (ValueError, TypeError):
            return f"[{'?' * width}]"
    
    def close(self):
        """Chiude il consumer."""
        if hasattr(self, 'consumer'):
            self.consumer.close()
            logger.info("Consumer Kafka chiuso")
        self.active = False


def main():
    """Funzione principale per l'esecuzione del consumer da linea di comando."""
    parser = argparse.ArgumentParser(description='Consumer Kafka per monitorare i messaggi di elaborazione WindNinja')
    
    parser.add_argument('--bootstrap-servers', type=str, default='localhost:9092',
                        help='Lista di server bootstrap Kafka (default: localhost:9092)')
    parser.add_argument('--topic', type=str, default='windninja-events',
                        help='Topic Kafka da cui consumare i messaggi (default: windninja-events)')
    parser.add_argument('--group-id', type=str, default=None,
                        help='Group ID per il consumer Kafka (default: generato automaticamente)')
    parser.add_argument('--simulation-id', type=str, default=None,
                        help='Filtra i messaggi per uno specifico ID di simulazione')
    
    args = parser.parse_args()
    
    # Crea e avvia il consumer
    consumer = KafkaMessageConsumer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        group_id=args.group_id,
        simulation_id=args.simulation_id
    )
    
    try:
        consumer.start_consuming()
    except KeyboardInterrupt:
        print("\nChiusura del consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()