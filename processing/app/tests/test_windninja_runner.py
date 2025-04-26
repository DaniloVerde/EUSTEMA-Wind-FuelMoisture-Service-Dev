import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.windninja.runner import run_windninja

class TestWindNinjaRunner(unittest.TestCase):
    """Test per il runner di WindNinja."""
    
    def setUp(self):
        """Inizializza le variabili per i test."""
        self.test_config = "test_config.cfg"
        self.test_working_dir = "/tmp/test_dir"
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_success(self, mock_popen):
        """Testa l'esecuzione di WindNinja con successo."""
        # Configura il mock
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Output di successo", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        # Esegui la funzione
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir)
        
        # Verifica che subprocess.Popen sia stato chiamato correttamente
        mock_popen.assert_called_once_with(
            ["WindNinja_cli", "--config_file", self.test_config],
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            universal_newlines=True,
            cwd=self.test_working_dir
        )
        
        # Verifica l'output
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "Output di successo")
        self.assertEqual(stderr, "")
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_failure(self, mock_popen):
        """Testa l'esecuzione di WindNinja con fallimento."""
        # Configura il mock
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("", "Errore durante l'esecuzione")
        process_mock.returncode = 1
        mock_popen.return_value = process_mock
        
        # Esegui la funzione
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir)
        
        # Verifica l'output
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Errore durante l'esecuzione")
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_timeout(self, mock_popen):
        """Testa il timeout durante l'esecuzione di WindNinja."""
        # Configura il mock per generare un'eccezione di timeout
        process_mock = MagicMock()
        process_mock.communicate.side_effect = subprocess.TimeoutExpired(cmd="WindNinja_cli", timeout=10)
        process_mock.kill = MagicMock()
        mock_popen.return_value = process_mock
        
        # Esegui la funzione con un timeout
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir, timeout=10)
        
        # Verifica che il processo sia stato terminato
        process_mock.kill.assert_called_once()
        
        # Verifica l'output
        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Timeout expired")

if __name__ == '__main__':
    unittest.main()