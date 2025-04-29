import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.windninja.runner import run_windninja

class TestWindNinjaRunner(unittest.TestCase):
    """Test for the WindNinja runner."""
    
    def setUp(self):
        """Initialize variables for tests."""
        self.test_config = "test_config.cfg"
        self.test_working_dir = "/tmp/test_dir"
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_success(self, mock_popen):
        """Test the successful execution of WindNinja."""
        # Configure the mock
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Success output", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        # Execute the function
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir)
        
        # Verify that subprocess.Popen was called correctly
        mock_popen.assert_called_once_with(
            ["WindNinja_cli", "--config_file", self.test_config],
            stdout=unittest.mock.ANY,
            stderr=unittest.mock.ANY,
            universal_newlines=True,
            cwd=self.test_working_dir
        )
        
        # Verify the output
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "Success output")
        self.assertEqual(stderr, "")
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_failure(self, mock_popen):
        """Test the failure execution of WindNinja."""
        # Configure the mock
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("", "Error during execution")
        process_mock.returncode = 1
        mock_popen.return_value = process_mock
        
        # Execute the function
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir)
        
        # Verify the output
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error during execution")
    
    @patch('app.windninja.runner.subprocess.Popen')
    def test_run_windninja_timeout(self, mock_popen):
        """Test timeout during the execution of WindNinja."""
        # Configure the mock to generate a timeout exception
        process_mock = MagicMock()
        process_mock.communicate.side_effect = subprocess.TimeoutExpired(cmd="WindNinja_cli", timeout=10)
        process_mock.kill = MagicMock()
        mock_popen.return_value = process_mock
        
        # Execute the function with a timeout
        exit_code, stdout, stderr = run_windninja(self.test_config, self.test_working_dir, timeout=10)
        
        # Verify that the process was terminated
        process_mock.kill.assert_called_once()
        
        # Verify the output
        self.assertEqual(exit_code, -1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Timeout expired")

if __name__ == '__main__':
    unittest.main()