import os
import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
from pathlib import Path

from app.fuel_moisture.processing import (
    get_surface_temperature,
    get_equilibrium_moisture_content,
    get_rainfall_moisture_factor,
    get_evaporation_correction_factor,
    get_moisture_correction_factor
)


class TestFuelMoistureProcessing(unittest.TestCase):
    """Test unitari per le funzioni di processing del modulo fuel_moisture."""
    
    def setUp(self):
        """Setup per i test, creazione dei mock e dei dati di test."""
        
        parent_dir = Path(__file__).resolve().parent.parent
        tables_path = parent_dir / "fuel_moisture" / "tables"
        
        self.surface_temp_df = pd.read_csv(tables_path  / "surface_temperature.csv", delimiter=";", index_col=0)
                
        self.eqmc_df = pd.read_csv(tables_path  / "eqmc.csv", delimiter=";", index_col=0)
        
        self.rmf_df = pd.read_csv(tables_path  / "rainfall_moisture_factor.csv", delimiter=";", index_col=0)
        
        self.ecf_df = pd.read_csv(tables_path  / "ecf.csv", delimiter=";", index_col=0)

        # Mock per le tabelle di desorption/absorption
        # self.des_1p_data = {
        #     "range": ["<5", "5-10", "10-15"],
        #     "<5": [1, 2, 3],
        #     "5-10": [4, 5, 6],
        #     "10-15": [7, 8, 9]
        # }
        # self.des_1p_df = pd.DataFrame(self.des_1p_data)

        self.des_11p_df = pd.read_csv(tables_path  / "desorption" / "DES_11P.csv", delimiter=";", index_col=0)

        # self.abs_1p_data = {
        #     "range": ["<5", "5-10", "10-15"],
        #     "<5": [1, 2, 3],
        #     "5-10": [4, 5, 6],
        #     "10-15": [7, 8, 9]
        # }
        # self.abs_1p_df = pd.DataFrame(self.abs_1p_data)

        self.abs_10p_df = pd.read_csv(tables_path  / "absorption" / "ABS_10P.csv", delimiter=";", index_col=0)

    @patch('app.fuel_moisture.processing.pd.read_csv')
    @patch('app.fuel_moisture.processing.round_5_value')
    @patch('app.fuel_moisture.processing.round_100_value')
    def test_get_surface_temperature(self, mock_round_100, mock_round_5, mock_read_csv):
        """Testa la funzione get_surface_temperature."""
        # Configura i mock
        mock_read_csv.return_value = self.surface_temp_df
        mock_round_5.return_value = 5
        mock_round_100.return_value = 100
        
        # Test con valori normali
        result = get_surface_temperature(5, 100)
        
        # Verifica che la funzione round_5_value sia stata chiamata correttamente
        mock_round_5.assert_called_once_with(5)
        
        # Verifica che la funzione round_100_value sia stata chiamata correttamente
        mock_round_100.assert_called_once_with(100)
        
        # Verifica che la funzione read_csv sia stata chiamata
        mock_read_csv.assert_called_once()
        
        # Verifica il risultato
        self.assertEqual(result, 34)
        
        # Reset i mock per un nuovo test
        mock_round_5.reset_mock()
        mock_round_100.reset_mock()
        mock_read_csv.reset_mock()
        
        # Test con temperatura fuori range (< 15)
        mock_round_5.return_value = 10
        mock_round_100.return_value = 100
        result = get_surface_temperature(10, 100)
        self.assertEqual(result, 34)
        
        # Reset i mock per un nuovo test
        mock_round_5.reset_mock()
        mock_round_100.reset_mock()
        mock_read_csv.reset_mock()
        
        # Test con temperatura fuori range (> 120)
        mock_round_5.return_value = 125
        mock_round_100.return_value = 100
        mock_read_csv.return_value = self.surface_temp_df
        result = get_surface_temperature(125, 100)
        self.assertEqual(result, 133)
        
        # Reset i mock per un nuovo test
        mock_round_5.reset_mock()
        mock_round_100.reset_mock()
        mock_read_csv.reset_mock()
        
        # Test con radiazione solare fuori range (< 100)
        mock_round_5.return_value = 5
        mock_round_100.return_value = 0
        mock_read_csv.return_value = self.surface_temp_df
        result = get_surface_temperature(5, 50)
        self.assertEqual(result, 32)
        
        # Reset i mock per un nuovo test
        mock_round_5.reset_mock()
        mock_round_100.reset_mock()
        mock_read_csv.reset_mock()
        
        # Test con radiazione solare fuori range (> 1300)
        mock_round_5.return_value = 5
        mock_round_100.return_value = 9999
        mock_read_csv.return_value = self.surface_temp_df
        result = get_surface_temperature(5, 1400)
        self.assertEqual(result, 60)
        
        # Test con valori che non si trovano nella tabella
        mock_round_5.return_value = 999
        mock_round_100.return_value = 999
        mock_read_csv.return_value = self.surface_temp_df
        result = get_surface_temperature(999, 999)
        self.assertIsNone(result)

    @patch('app.fuel_moisture.processing.pd.read_csv')
    @patch('app.fuel_moisture.processing.round_5_value')
    def test_get_equilibrium_moisture_content(self, mock_round_5, mock_read_csv):
        """Testa la funzione get_equilibrium_moisture_content."""
        # Configura i mock
        mock_read_csv.return_value = self.eqmc_df
        
        # Test con valori normali
        mock_round_5.return_value = 5
        result = get_equilibrium_moisture_content(5, 5)
        self.assertEqual(result, 5)
        
        # Test con umidità <= 2.5
        mock_round_5.return_value = 5
        result = get_equilibrium_moisture_content(5, 2)
        self.assertEqual(result, 3)
        
        # Test con umidità >= 97.5
        mock_round_5.return_value = 5
        mock_read_csv.return_value = self.eqmc_df
        result = get_equilibrium_moisture_content(5, 98)
        self.assertEqual(result, 34)
        
        mock_round_5.return_value = 999
        mock_read_csv.return_value = self.eqmc_df
        result = get_equilibrium_moisture_content(999, 5)
        self.assertIsNone(result)

    @patch('app.fuel_moisture.processing.pd.read_csv')
    @patch('app.fuel_moisture.processing.round_001_value')
    def test_get_rainfall_moisture_factor(self, mock_round_001, mock_read_csv):
        """Testa la funzione get_rainfall_moisture_factor."""
        # Configura i mock
        mock_read_csv.return_value = self.rmf_df
        
        # Test con precipitazione <= 0
        result = get_rainfall_moisture_factor(0)
        self.assertEqual(result, 0)
        
        # Test con precipitazione normale
        mock_round_001.return_value = 0.02
        result = get_rainfall_moisture_factor(0.02)
        self.assertEqual(result, 15)
        
        # Test con precipitazione > 0.33
        mock_round_001.return_value = 0.5
        result = get_rainfall_moisture_factor(0.5)
        self.assertEqual(result, 31)
        
        # Test con valori negativi
        mock_round_001.return_value = -0.15
        result = get_rainfall_moisture_factor(0.15)
        self.assertIsNone(result)

    @patch('app.fuel_moisture.processing.pd.read_csv')
    @patch('app.fuel_moisture.processing.round_5_value')
    def test_get_evaporation_correction_factor(self, mock_round_5, mock_read_csv):
        """Testa la funzione get_evaporation_correction_factor."""
        # Configura i mock
        mock_read_csv.return_value = self.ecf_df
        
        # Test con previous_fuel_moisture <= 30
        result = get_evaporation_correction_factor(35, 25)
        self.assertEqual(result, 0)
        
        # Test con temperatura di superficie < 30
        mock_round_5.return_value = 25
        result = get_evaporation_correction_factor(25, 31)
        self.assertEqual(result, -2)
        
        # Test con temperatura di superficie > 145
        mock_round_5.return_value = 150
        result = get_evaporation_correction_factor(150, 31)
        self.assertEqual(result, -9)
        
        # Test con valori normali
        mock_round_5.return_value = 35
        result = get_evaporation_correction_factor(35, 31)
        self.assertEqual(result, -3)
        
        # Test con valori che non si trovano nella tabella
        mock_round_5.return_value = 150
        result = get_evaporation_correction_factor(150, 31)
        self.assertEqual(result, -9)

    @patch('app.fuel_moisture.processing.pd.read_csv')
    @patch('app.fuel_moisture.processing.parse_label')
    def test_get_moisture_correction_factor(self, mock_parse_label, mock_read_csv):
        """Testa la funzione get_moisture_correction_factor."""
        
        # Configura il mock per parse_label
        def parse_label_side_effect(label):
            if label == "<5":
                return (-900, 5)
            elif label == "5-10":
                return (5, 10)
            elif label == "10-15":
                return (10, 15)
        
        mock_parse_label.side_effect = parse_label_side_effect
        
        # Test con precipitazione > 0
        result = get_moisture_correction_factor(25, 60, 10, 15, 0.1)
        self.assertEqual(result, 0)
        
        # Test con previous_fuel_moisture >= 30
        result = get_moisture_correction_factor(25, 60, 10, 30, 0)
        self.assertEqual(result, 0)
        
        # Test con desorption (previous_fuel_moisture > eqmc)
        mock_read_csv.reset_mock()
        mock_read_csv.return_value = self.des_11p_df
        result = get_moisture_correction_factor(7, 7, 10, 11, 0)
        self.assertEqual(result, -3)
        
        # Test con absorption (previous_fuel_moisture < eqmc)
        mock_read_csv.reset_mock()
        mock_read_csv.return_value = self.abs_10p_df
        result = get_moisture_correction_factor(7, 7, 11, 10, 0)
        self.assertEqual(result, -4)
        
        # Test con umidità non valida
        result = get_moisture_correction_factor(25, -10, 10, 15, 0)
        self.assertIsNone(result)
        
        # Test con valori che non si trovano nella tabella
        mock_parse_label.side_effect = lambda x: (20, 25) if x == "20-25" else None
        result = get_moisture_correction_factor(22, 60, 10, 11, 0)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()