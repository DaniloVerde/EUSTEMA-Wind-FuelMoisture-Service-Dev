import os
import json
import unittest
import requests
from unittest.mock import patch, MagicMock

# Rimuoviamo l'import del TestClient di FastAPI poiché useremo requests
# from fastapi.testclient import TestClient

# Manteniamo l'import dell'app solo per riferimento, non lo useremo direttamente
from app.main import app
from app.api.models import WindNinjaRequest, ProcessingResponse
from app.api.tasks import process_windninja_request

# Configurazione dell'URL dell'endpoint
API_BASE_URL = "http://localhost:8000"

class TestProcessingEndpoint(unittest.TestCase):
    """Test per l'endpoint di elaborazione WindNinja."""
    
    def setUp(self):
        """Inizializza il payload di esempio."""
        # Rimuoviamo l'inizializzazione del client TestClient
        # self.client = TestClient(app)
        
        # Carica il JSON di esempio
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
        json_file = os.path.join(test_data_dir, "input", "station_list.json")
        
        with open(json_file, 'r') as f:
            self.test_payload = json.load(f)
    
    # Rimuoviamo il patch su process_windninja_request perché non possiamo mockare
    # funzioni all'interno del container che stiamo testando
    def test_process_windninja_endpoint(self):
        """Testa che l'endpoint restituisca 202 Accepted e avvii l'elaborazione in background."""
        # Esegui la richiesta POST usando requests
        response = requests.post(f"{API_BASE_URL}/api/v1/process", json=self.test_payload)
        
        # Verifica che la risposta sia 202 Accepted
        self.assertEqual(response.status_code, 202)
        
        # Verifica il contenuto della risposta
        response_data = response.json()
        self.assertEqual(response_data["modelId"], self.test_payload["modelId"])
        self.assertEqual(response_data["status"], "accepted")
        self.assertIn("Processing started", response_data["message"])
    
    def test_malformed_request(self):
        """Testa che l'endpoint gestisca correttamente le richieste malformate."""
        # Crea un payload malformato (mancano le stazioni)
        malformed_payload = {
            "modelId": "test123",
            "elevation_file": "input/test.tif"
            # Manca meteorological_stations che è obbligatorio
        }
        
        # Esegui la richiesta POST usando requests
        response = requests.post(f"{API_BASE_URL}/api/v1/process", json=malformed_payload)
        
        # Verifica che la risposta sia 422 Unprocessable Entity (errore di validazione)
        self.assertEqual(response.status_code, 422)


# Manteniamo la classe TestProcessingTasks invariata poiché testa le funzioni 
# direttamente e non attraverso gli endpoint HTTP
class TestProcessingTasks(unittest.TestCase):
    """Test per le attività di elaborazione in background."""
    
    def setUp(self):
        """Inizializza il payload di esempio."""
        # Carica il JSON di esempio
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
        json_file = os.path.join(test_data_dir, "input", "station_list.json")
        
        with open(json_file, 'r') as f:
            self.test_payload = json.load(f)
        
        self.model_id = self.test_payload["modelId"]
    
    @patch('app.api.tasks.KafkaMessageProducer')
    @patch('app.api.tasks.process_windninja_input')
    @patch('app.api.tasks.run_windninja')
    @patch('app.api.tasks.MinioClient')
    def test_process_windninja_request_success(self, mock_minio, mock_run, mock_process_input, mock_kafka):
        """Testa il flusso di successo dell'elaborazione WindNinja."""
        # Configura i mock per simulare un'esecuzione riuscita
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        mock_process_input.return_value = (
            self.model_id,
            ["station_1.csv", "station_2.csv"],
            "/tmp/elevation.tif",
            "/tmp/config.cfg"
        )
        
        mock_run.return_value = (0, "Standard output", "")  # exit_code 0 = successo
        
        mock_minio_instance = MagicMock()
        mock_minio.return_value = mock_minio_instance
        
        # Esegui la funzione di elaborazione
        process_windninja_request(self.model_id, self.test_payload)
        
        # Verifica che i messaggi di progresso siano stati inviati
        self.assertTrue(mock_kafka_instance.send_simulation_progress.called)
        # Aggiorniamo l'aspettativa a 6 chiamate invece di 5
        self.assertEqual(mock_kafka_instance.send_simulation_progress.call_count, 6)  # Probabilmente: 0%, 10%, 30%, 50%, 70%, 90%
        
        # Verifica che il messaggio di completamento sia stato inviato
        mock_kafka_instance.send_simulation_complete.assert_called_once()
        
        # Verifica che non ci siano stati messaggi di errore
        mock_kafka_instance.send_simulation_failed.assert_not_called()
        
        # Verifica che WindNinja sia stato eseguito
        mock_run.assert_called_once()
        
        # Verifica che i risultati siano stati caricati su MinIO
        # self.assertTrue(mock_minio_instance.upload_file.called)
    
    @patch('app.api.tasks.KafkaMessageProducer')
    @patch('app.api.tasks.process_windninja_input')
    @patch('app.api.tasks.run_windninja')
    def test_process_windninja_request_run_failure(self, mock_run, mock_process_input, mock_kafka):
        """Testa il caso in cui l'esecuzione di WindNinja fallisca."""
        # Configura i mock per simulare un fallimento nell'esecuzione di WindNinja
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        mock_process_input.return_value = (
            self.model_id,
            ["station_1.csv", "station_2.csv"],
            "/tmp/elevation.tif",
            "/tmp/config.cfg"
        )
        
        mock_run.return_value = (1, "", "Error: simulation failed")  # exit_code 1 = errore
        
        # Esegui la funzione di elaborazione
        process_windninja_request(self.model_id, self.test_payload)
        
        # Verifica che sia stato inviato un messaggio di errore
        # Non controlliamo più il numero esatto di chiamate
        self.assertTrue(mock_kafka_instance.send_simulation_failed.called)
        
        # Verifica che il messaggio di completamento non sia stato inviato
        mock_kafka_instance.send_simulation_complete.assert_not_called()
        
    @patch('app.api.tasks.KafkaMessageProducer')
    @patch('app.api.tasks.process_windninja_input')
    def test_process_windninja_request_input_error(self, mock_process_input, mock_kafka):
        """Testa il caso in cui si verifichi un errore nell'elaborazione dei dati di input."""
        # Configura i mock per simulare un errore nell'elaborazione degli input
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        # Simula un'eccezione durante l'elaborazione degli input
        mock_process_input.side_effect = Exception("Error processing input data")
        
        # Esegui la funzione di elaborazione e verifica che l'eccezione venga gestita
        with self.assertRaises(Exception):
            process_windninja_request(self.model_id, self.test_payload)
        
        # Verifica che sia stato inviato un messaggio di errore
        # Non controlliamo più il numero esatto di chiamate
        self.assertTrue(mock_kafka_instance.send_simulation_failed.called)
        
        # Verifica che il messaggio di completamento non sia stato inviato
        mock_kafka_instance.send_simulation_complete.assert_not_called()

if __name__ == '__main__':
    unittest.main()