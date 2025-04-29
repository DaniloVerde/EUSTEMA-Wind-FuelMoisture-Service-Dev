import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.windninja.utils import json_to_station_csv
from app.windninja.input_generator import generate_station_files_from_json, generate_windninja_config, process_windninja_input, download_elevation_file_from_minio

class TestWindNinjaInputGenerator(unittest.TestCase):
    """Test for the WindNinja input generator."""
    
    def setUp(self):
        """Initialize variables for tests."""
        # Temporary directory for tests
        self.test_dir = tempfile.mkdtemp()
        
        # Path to the example JSON file
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        self.json_file = self.test_data_dir / "input" / "station_list.json"
        
        # Load the example JSON
        with open(self.json_file, 'r') as f:
            self.json_data = json.load(f)
        
        # Model ID 
        self.model_id = self.json_data.get('modelId')
        
    def tearDown(self):
        """Clean up temporary directories created during tests."""
        shutil.rmtree(self.test_dir)
    
    def test_json_to_station_csv(self):
        """Test conversion from JSON to CSV."""
        # Run the conversion function
        csv_files, list_filepath = json_to_station_csv(self.json_data, self.test_dir)
        
        # Verify that CSV files were created
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        self.assertTrue(os.path.exists(input_dir))
        
        # Verify that all CSV files were created
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        
        # Verify that the list file exists
        self.assertTrue(os.path.exists(list_filepath))
        
        # Verify the content of the list file
        with open(list_filepath, 'r') as f:
            content = f.read()
            # Verify that it contains the correct first line
            self.assertIn("Recent_Station_File_List,", content)
            # Verify that it contains all the names of the created CSV files
            for csv_file in csv_files:
                self.assertIn(csv_file, content)
    
    def test_generate_station_files_from_json(self):
        """Test the main file generation function."""
        # Run the generation function
        model_id, csv_files, list_filepath = generate_station_files_from_json(
            self.json_file, self.test_dir
        )
        
        # Verify that the model_id is correct
        self.assertEqual(model_id, self.model_id)
        
        # Verify that CSV files were created
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        self.assertTrue(os.path.exists(input_dir))
        
        # Verify that all CSV files were created
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        
        # Verify that the list file exists
        self.assertTrue(os.path.exists(list_filepath))
        
    def test_csv_format(self):
        """Verify that the format of the generated CSVs is correct."""
        # Run the conversion function
        csv_files, list_filepath = json_to_station_csv(self.json_data, self.test_dir)
        
        # Path to the input directory
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        
        # Verify the format of the first CSV file
        for csv_file in csv_files:
            csv_path = os.path.join(input_dir, csv_file)
            self.assertTrue(os.path.exists(csv_path))
            
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                
                # Verify that there are two lines (header and data)
                self.assertEqual(len(lines), 2)
                
                # Verify the header
                header = lines[0].strip()
                self.assertIn("Station_Name", header)
                self.assertIn("Coord_Sys(PROJCS,GEOGCS)", header)
                self.assertIn("Lat/YCoord", header)
                self.assertIn("Speed", header)
                self.assertIn("Direction(degrees)", header)
                
                # Verify the data
                data = lines[1].strip()
                # Verify that the data is not empty
                self.assertTrue(len(data) > 0)
    
    @patch('app.windninja.input_generator.MinioClient')
    def test_download_elevation_file(self, mock_minio_client):
        """Test downloading the elevation file from MinIO."""
        # Configure the MinIO client mock
        mock_client_instance = MagicMock()
        mock_minio_client.return_value = mock_client_instance
        
        # Path to the elevation file
        elevation_file_path = "input/w46575_s10.tif"
        output_dir = os.path.join(self.test_dir, "input")
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a dummy file as result of the download
        local_file_path = os.path.join(output_dir, "w46575_s10.tif")
        with open(local_file_path, 'w') as f:
            f.write("Test elevation file content")
        
        # Configure the mock to simulate the download
        def side_effect(object_name, file_path):
            # Avoid SameFileError by checking if the source and destination are the same
            if local_file_path != file_path:
                shutil.copy(local_file_path, file_path)
            
        mock_client_instance.download_file.side_effect = side_effect
        
        # Run the download function
        result = download_elevation_file_from_minio(elevation_file_path, output_dir)
        
        # Verify that the MinIO client was called correctly
        mock_client_instance.download_file.assert_called_once_with(elevation_file_path, local_file_path)
        
        # Verify that the returned path is correct
        self.assertEqual(result, local_file_path)
        
        # Verify that the file exists
        self.assertTrue(os.path.exists(local_file_path))
    
    def test_generate_windninja_config(self):
        """Test generating the WindNinja configuration file."""
        # Create a test elevation file
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
        elevation_file = os.path.join(input_dir, "w46575_s10.tif")
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
        
        # Create a test stations list file
        stations_list_file = os.path.join(input_dir, "stations_list.txt")
        with open(stations_list_file, 'w') as f:
            f.write("Recent_Station_File_List, 6\nstation_1.csv\nstation_2.csv\nstation_3.csv\nstation_4.csv\nstation_5.csv\nstation_6.csv")
        
        # Run the configuration file generation function
        config_file = generate_windninja_config(
            self.json_data,
            self.test_dir,
            self.model_id,
            elevation_file,
            stations_list_file
        )
        
        # Verify that the configuration file was created
        self.assertTrue(os.path.exists(config_file))
        
        # Verify the content of the configuration file
        with open(config_file, 'r') as f:
            content = f.read()
            
            # Verify that it contains the correct parameters
            self.assertIn(f"elevation_file           = {elevation_file}", content)
            self.assertIn("initialization_method    = pointInitialization", content)
            self.assertIn(f"wx_station_filename      = {stations_list_file}", content)
            
            # Verify the optional parameters from JSON
            self.assertIn(f"output_wind_height       = {self.json_data['output_wind_height']}", content)
            self.assertIn(f"units_output_wind_height = {self.json_data['units_output_wind_height']}", content)
            self.assertIn(f"vegetation               = {self.json_data['vegetation']}", content)
            
            # Verify the default output settings
            self.assertIn("mesh_resolution          = 500.0", content)
            self.assertIn("write_goog_output        = true", content)
            self.assertIn("write_ascii_output       = true", content)
    
    @patch('app.windninja.input_generator.download_elevation_file_from_minio')
    @patch('app.windninja.input_generator.generate_station_files_from_json')
    def test_process_windninja_input(self, mock_generate_stations, mock_download):
        """Test the complete WindNinja data processing process."""
        # Configure the mocks for the called functions
        stations_list_file = os.path.join(self.test_dir, self.model_id, "input", "stations_list.txt")
        csv_files = ["station_1.csv", "station_2.csv"]
        mock_generate_stations.return_value = (self.model_id, csv_files, stations_list_file)
    
        elevation_file = os.path.join(self.test_dir, self.model_id, "input", "w46575_s10.tif")
        mock_download.return_value = elevation_file
    
        # Create necessary directories
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
    
        # Create test files
        with open(stations_list_file, 'w') as f:
            f.write("Test stations list content")
    
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
    
        # Run the processing function
        model_id, csv_files_result, elevation_file_result, config_file = process_windninja_input(
            self.json_data,
            self.test_dir
        )
    
        # Verify that the model_id is correct
        self.assertEqual(model_id, self.model_id)
    
        # Verify that the mock functions were called correctly
        mock_generate_stations.assert_called_once()
        mock_download.assert_called_once_with(self.json_data['elevation_file'], input_dir, self.model_id)
        
        # Verify that the correct paths were returned
        self.assertEqual(csv_files_result, csv_files)
        self.assertEqual(elevation_file_result, elevation_file)
        
        # Verify that the configuration file was created
        self.assertTrue(os.path.exists(config_file))
    
    @patch('app.windninja.input_generator.MinioClient')
    def test_end_to_end_process(self, mock_minio_client):
        """Test the entire process from start to finish."""
        # Configure the MinIO client mock
        mock_client_instance = MagicMock()
        mock_minio_client.return_value = mock_client_instance
        
        # Prepare the path to the elevation file
        elevation_file_name = "w46575_s10.tif"
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
        elevation_file = os.path.join(input_dir, elevation_file_name)
        
        # Create a dummy file as result of the download
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
        
        # Configure the mock to simulate the download
        def side_effect(object_name, file_path):
            # Avoid SameFileError by checking if the source and destination are the same
            if elevation_file != file_path:
                shutil.copy(elevation_file, file_path)
            
        mock_client_instance.download_file.side_effect = side_effect
        
        # Run the entire process
        model_id, csv_files, elevation_file_result, config_file = process_windninja_input(
            self.json_data,
            self.test_dir
        )
        
        # Verify that the model_id is correct
        self.assertEqual(model_id, self.model_id)
        
        # Verify that CSV files were created
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        for csv_file in csv_files:
            csv_path = os.path.join(input_dir, csv_file)
            self.assertTrue(os.path.exists(csv_path))
        
        # Verify that the elevation file was downloaded
        self.assertTrue(os.path.exists(elevation_file_result))
        
        # Verify that the configuration file was created
        self.assertTrue(os.path.exists(config_file))
        
        # Verify the content of the configuration file
        with open(config_file, 'r') as f:
            content = f.read()
            self.assertIn(f"elevation_file           = {elevation_file}", content)
            self.assertIn("initialization_method    = pointInitialization", content)
            self.assertIn(f"output_wind_height       = {self.json_data['output_wind_height']}", content)

if __name__ == '__main__':
    unittest.main()