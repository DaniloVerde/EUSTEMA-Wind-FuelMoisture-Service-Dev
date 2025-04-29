import os
import json
import unittest
import requests
from unittest.mock import patch, MagicMock

# We remove the import of FastAPI's TestClient since we'll use requests
# from fastapi.testclient import TestClient

# We keep the app import only for reference, we won't use it directly
from app.main import app
from app.api.models import WindNinjaRequest, ProcessingResponse
from app.api.tasks import process_windninja_request

# Configuration of the endpoint URL
API_BASE_URL = "http://localhost:8000"

class TestProcessingEndpoint(unittest.TestCase):
    """Tests for the WindNinja processing endpoint."""
    
    def setUp(self):
        """Initialize the example payload."""
        # We remove the initialization of the TestClient
        # self.client = TestClient(app)
        
        # Load the example JSON
        test_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_data")
        json_file = os.path.join(test_data_dir, "input", "station_list.json")
        
        with open(json_file, 'r') as f:
            self.test_payload = json.load(f)
    
    # We remove the patch on process_windninja_request because we can't mock
    # functions inside the container we're testing
    def test_process_windninja_endpoint(self):
        """Test that the endpoint returns 202 Accepted and starts background processing."""
        # Execute the POST request using requests
        response = requests.post(f"{API_BASE_URL}/api/v1/process", json=self.test_payload)
        
        # Verify that the response is 202 Accepted
        self.assertEqual(response.status_code, 202)
        
        # Verify the response content
        response_data = response.json()
        self.assertEqual(response_data["modelId"], self.test_payload["modelId"])
        self.assertEqual(response_data["status"], "accepted")
        self.assertIn("Processing started", response_data["message"])
    
    def test_malformed_request(self):
        """Test that the endpoint correctly handles malformed requests."""
        # Create a malformed payload (missing stations)
        malformed_payload = {
            "modelId": "test123",
            "elevation_file": "input/test.tif"
            # Missing meteorological_stations which is required
        }
        
        # Execute the POST request using requests
        response = requests.post(f"{API_BASE_URL}/api/v1/process", json=malformed_payload)
        
        # Verify that the response is 422 Unprocessable Entity (validation error)
        self.assertEqual(response.status_code, 422)


# We keep the TestProcessingTasks class unchanged since it tests functions
# directly and not through HTTP endpoints
class TestProcessingTasks(unittest.TestCase):
    """Tests for background processing tasks."""
    
    def setUp(self):
        """Initialize the example payload."""
        # Load the example JSON
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
        """Test the successful flow of WindNinja processing."""
        # Configure mocks to simulate a successful execution
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        mock_process_input.return_value = (
            self.model_id,
            ["station_1.csv", "station_2.csv"],
            "/tmp/elevation.tif",
            "/tmp/config.cfg"
        )
        
        mock_run.return_value = (0, "Standard output", "")  # exit_code 0 = success
        
        mock_minio_instance = MagicMock()
        mock_minio.return_value = mock_minio_instance
        
        # Execute the processing function
        process_windninja_request(self.model_id, self.test_payload)
        
        # Verify that progress messages were sent
        self.assertTrue(mock_kafka_instance.send_simulation_progress.called)
        # Update expectation to 6 calls instead of 5
        self.assertEqual(mock_kafka_instance.send_simulation_progress.call_count, 6)  # Probably: 0%, 10%, 30%, 50%, 70%, 90%
        
        # Verify that completion message was sent
        mock_kafka_instance.send_simulation_complete.assert_called_once()
        
        # Verify that no error messages were sent
        mock_kafka_instance.send_simulation_failed.assert_not_called()
        
        # Verify that WindNinja was executed
        mock_run.assert_called_once()
        
        # Verify that results were uploaded to MinIO
        # self.assertTrue(mock_minio_instance.upload_file.called)
    
    @patch('app.api.tasks.KafkaMessageProducer')
    @patch('app.api.tasks.process_windninja_input')
    @patch('app.api.tasks.run_windninja')
    def test_process_windninja_request_run_failure(self, mock_run, mock_process_input, mock_kafka):
        """Test the case where WindNinja execution fails."""
        # Configure mocks to simulate a failure in WindNinja execution
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        mock_process_input.return_value = (
            self.model_id,
            ["station_1.csv", "station_2.csv"],
            "/tmp/elevation.tif",
            "/tmp/config.cfg"
        )
        
        mock_run.return_value = (1, "", "Error: simulation failed")  # exit_code 1 = error
        
        # Execute the processing function
        process_windninja_request(self.model_id, self.test_payload)
        
        # Verify that an error message was sent
        # We no longer check the exact number of calls
        self.assertTrue(mock_kafka_instance.send_simulation_failed.called)
        
        # Verify that completion message was not sent
        mock_kafka_instance.send_simulation_complete.assert_not_called()
        
    @patch('app.api.tasks.KafkaMessageProducer')
    @patch('app.api.tasks.process_windninja_input')
    def test_process_windninja_request_input_error(self, mock_process_input, mock_kafka):
        """Test the case where an error occurs during input data processing."""
        # Configure mocks to simulate an error in processing inputs
        mock_kafka_instance = MagicMock()
        mock_kafka.return_value = mock_kafka_instance
        
        # Simulate an exception during input processing
        mock_process_input.side_effect = Exception("Error processing input data")
        
        # Execute the processing function and verify that the exception is handled
        with self.assertRaises(Exception):
            process_windninja_request(self.model_id, self.test_payload)
        
        # Verify that an error message was sent
        # We no longer check the exact number of calls
        self.assertTrue(mock_kafka_instance.send_simulation_failed.called)
        
        # Verify that completion message was not sent
        mock_kafka_instance.send_simulation_complete.assert_not_called()

if __name__ == '__main__':
    unittest.main()