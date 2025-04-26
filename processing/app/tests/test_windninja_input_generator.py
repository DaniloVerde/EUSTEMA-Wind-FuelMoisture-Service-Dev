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
    """Test per il generatore di file di input per WindNinja."""
    
    def setUp(self):
        """Inizializza le variabili per i test."""
        # Directory temporanea per i test
        self.test_dir = tempfile.mkdtemp()
        
        # Percorso al file JSON di esempio
        self.test_data_dir = Path(__file__).parent.parent / "test_data"
        self.json_file = self.test_data_dir / "input" / "station_list.json"
        
        # Carica il JSON di esempio
        with open(self.json_file, 'r') as f:
            self.json_data = json.load(f)
        
        # Model ID 
        self.model_id = self.json_data.get('modelId')
        
    def tearDown(self):
        """Pulisce le directory temporanee create durante i test."""
        shutil.rmtree(self.test_dir)
    
    def test_json_to_station_csv(self):
        """Testa la conversione da JSON a CSV."""
        # Esegui la funzione di conversione
        csv_files, list_filepath = json_to_station_csv(self.json_data, self.test_dir)
        
        # Verifica che siano stati creati i file CSV
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        self.assertTrue(os.path.exists(input_dir))
        
        # Verifica che siano stati creati tutti i file CSV
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        
        # Verifica che esista il file di elenco
        self.assertTrue(os.path.exists(list_filepath))
        
        # Verifica il contenuto del file di elenco
        with open(list_filepath, 'r') as f:
            content = f.read()
            # Verifica che contenga la prima riga corretta
            self.assertIn("Recent_Station_File_List,", content)
            # Verifica che contenga tutti i nomi dei file CSV creati
            for csv_file in csv_files:
                self.assertIn(csv_file, content)
    
    def test_generate_station_files_from_json(self):
        """Testa la funzione principale di generazione dei file."""
        # Esegui la funzione di generazione
        model_id, csv_files, list_filepath = generate_station_files_from_json(
            self.json_file, self.test_dir
        )
        
        # Verifica che il model_id sia corretto
        self.assertEqual(model_id, self.model_id)
        
        # Verifica che siano stati creati i file CSV
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        self.assertTrue(os.path.exists(input_dir))
        
        # Verifica che siano stati creati tutti i file CSV
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        
        # Verifica che esista il file di elenco
        self.assertTrue(os.path.exists(list_filepath))
        
    def test_csv_format(self):
        """Verifica che il formato dei CSV generati sia corretto."""
        # Esegui la funzione di conversione
        csv_files, list_filepath = json_to_station_csv(self.json_data, self.test_dir)
        
        # Percorso della directory di input
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        
        # Verifica il formato del primo file CSV
        for csv_file in csv_files:
            csv_path = os.path.join(input_dir, csv_file)
            self.assertTrue(os.path.exists(csv_path))
            
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                
                # Verifica che ci siano due righe (intestazione e dati)
                self.assertEqual(len(lines), 2)
                
                # Verifica l'intestazione
                header = lines[0].strip()
                self.assertIn("Station_Name", header)
                self.assertIn("Coord_Sys(PROJCS,GEOGCS)", header)
                self.assertIn("Lat/YCoord", header)
                self.assertIn("Speed", header)
                self.assertIn("Direction(degrees)", header)
                
                # Verifica i dati
                data = lines[1].strip()
                # Verifica che i dati non siano vuoti
                self.assertTrue(len(data) > 0)
    
    @patch('app.windninja.input_generator.MinioClient')
    def test_download_elevation_file(self, mock_minio_client):
        """Testa il download del file di elevazione da MinIO."""
        # Configura il mock del client MinIO
        mock_client_instance = MagicMock()
        mock_minio_client.return_value = mock_client_instance
        
        # Percorso del file di elevazione
        elevation_file_path = "input/w46575_s10.tif"
        output_dir = os.path.join(self.test_dir, "input")
        os.makedirs(output_dir, exist_ok=True)
        
        # Crea un file fittizio come risultato del download
        local_file_path = os.path.join(output_dir, "w46575_s10.tif")
        with open(local_file_path, 'w') as f:
            f.write("Test elevation file content")
        
        # Configura il mock per simulare il download
        def side_effect(object_name, file_path):
            # Avoid SameFileError by checking if the source and destination are the same
            if local_file_path != file_path:
                shutil.copy(local_file_path, file_path)
            
        mock_client_instance.download_file.side_effect = side_effect
        
        # Esegui la funzione di download
        result = download_elevation_file_from_minio(elevation_file_path, output_dir)
        
        # Verifica che il client MinIO sia stato chiamato correttamente
        mock_client_instance.download_file.assert_called_once_with(elevation_file_path, local_file_path)
        
        # Verifica che il percorso restituito sia corretto
        self.assertEqual(result, local_file_path)
        
        # Verifica che il file esista
        self.assertTrue(os.path.exists(local_file_path))
    
    def test_generate_windninja_config(self):
        """Testa la generazione del file di configurazione WindNinja."""
        # Crea un file di elevazione di test
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
        elevation_file = os.path.join(input_dir, "w46575_s10.tif")
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
        
        # Crea un file di elenco stazioni di test
        stations_list_file = os.path.join(input_dir, "stations_list.txt")
        with open(stations_list_file, 'w') as f:
            f.write("Recent_Station_File_List, 6\nstation_1.csv\nstation_2.csv\nstation_3.csv\nstation_4.csv\nstation_5.csv\nstation_6.csv")
        
        # Esegui la funzione di generazione del file di configurazione
        config_file = generate_windninja_config(
            self.json_data,
            self.test_dir,
            self.model_id,
            elevation_file,
            stations_list_file
        )
        
        # Verifica che il file di configurazione sia stato creato
        self.assertTrue(os.path.exists(config_file))
        
        # Verifica il contenuto del file di configurazione
        with open(config_file, 'r') as f:
            content = f.read()
            
            # Verifica che contenga i parametri corretti
            self.assertIn(f"elevation_file           = {elevation_file}", content)
            self.assertIn("initialization_method    = pointInitialization", content)
            self.assertIn(f"wx_station_filename      = {stations_list_file}", content)
            
            # Verifica i parametri opzionali dal JSON
            self.assertIn(f"output_wind_height       = {self.json_data['output_wind_height']}", content)
            self.assertIn(f"units_output_wind_height = {self.json_data['units_output_wind_height']}", content)
            self.assertIn(f"vegetation               = {self.json_data['vegetation']}", content)
            
            # Verifica le impostazioni di output predefinite
            self.assertIn("mesh_resolution          = 500.0", content)
            self.assertIn("write_goog_output        = true", content)
            self.assertIn("write_ascii_output       = true", content)
    
    @patch('app.windninja.input_generator.download_elevation_file_from_minio')
    @patch('app.windninja.input_generator.generate_station_files_from_json')
    def test_process_windninja_input(self, mock_generate_stations, mock_download):
        """Testa il processo completo di elaborazione dati WindNinja."""
        # Configura i mock per le funzioni chiamate
        stations_list_file = os.path.join(self.test_dir, self.model_id, "input", "stations_list.txt")
        csv_files = ["station_1.csv", "station_2.csv"]
        mock_generate_stations.return_value = (self.model_id, csv_files, stations_list_file)
    
        elevation_file = os.path.join(self.test_dir, self.model_id, "input", "w46575_s10.tif")
        mock_download.return_value = elevation_file
    
        # Crea le directory necessarie
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
    
        # Crea i file di test
        with open(stations_list_file, 'w') as f:
            f.write("Test stations list content")
    
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
    
        # Esegui la funzione di elaborazione
        model_id, csv_files_result, elevation_file_result, config_file = process_windninja_input(
            self.json_data,
            self.test_dir
        )
    
        # Verifica che il model_id sia corretto
        self.assertEqual(model_id, self.model_id)
    
        # Verifica che le funzioni mock siano state chiamate correttamente
        mock_generate_stations.assert_called_once()
        mock_download.assert_called_once_with(self.json_data['elevation_file'], input_dir, self.model_id)
        
        # Verifica che siano stati restituiti i percorsi corretti
        self.assertEqual(csv_files_result, csv_files)
        self.assertEqual(elevation_file_result, elevation_file)
        
        # Verifica che il file di configurazione sia stato creato
        self.assertTrue(os.path.exists(config_file))
    
    @patch('app.windninja.input_generator.MinioClient')
    def test_end_to_end_process(self, mock_minio_client):
        """Testa l'intero processo dall'inizio alla fine."""
        # Configura il mock del client MinIO
        mock_client_instance = MagicMock()
        mock_minio_client.return_value = mock_client_instance
        
        # Prepara il percorso del file di elevazione
        elevation_file_name = "w46575_s10.tif"
        input_dir = os.path.join(self.test_dir, self.model_id, "input")
        os.makedirs(input_dir, exist_ok=True)
        elevation_file = os.path.join(input_dir, elevation_file_name)
        
        # Crea un file fittizio come risultato del download
        with open(elevation_file, 'w') as f:
            f.write("Test elevation file content")
        
        # Configura il mock per simulare il download
        def side_effect(object_name, file_path):
            # Avoid SameFileError by checking if the source and destination are the same
            if elevation_file != file_path:
                shutil.copy(elevation_file, file_path)
            
        mock_client_instance.download_file.side_effect = side_effect
        
        # Esegui l'intero processo
        model_id, csv_files, elevation_file_result, config_file = process_windninja_input(
            self.json_data,
            self.test_dir
        )
        
        # Verifica che il model_id sia corretto
        self.assertEqual(model_id, self.model_id)
        
        # Verifica che i file CSV siano stati creati
        self.assertEqual(len(csv_files), len(self.json_data.get('meteorological_stations', [])))
        for csv_file in csv_files:
            csv_path = os.path.join(input_dir, csv_file)
            self.assertTrue(os.path.exists(csv_path))
        
        # Verifica che il file di elevazione sia stato scaricato
        self.assertTrue(os.path.exists(elevation_file_result))
        
        # Verifica che il file di configurazione sia stato creato
        self.assertTrue(os.path.exists(config_file))
        
        # Verifica il contenuto del file di configurazione
        with open(config_file, 'r') as f:
            content = f.read()
            self.assertIn(f"elevation_file           = {elevation_file}", content)
            self.assertIn("initialization_method    = pointInitialization", content)
            self.assertIn(f"output_wind_height       = {self.json_data['output_wind_height']}", content)

if __name__ == '__main__':
    unittest.main()