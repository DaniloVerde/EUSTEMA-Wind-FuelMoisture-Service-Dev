from pathlib import Path
import os
import time
import unittest
import shutil
import tempfile
from unittest.mock import Mock, patch, MagicMock

from ..cleanup.cleanup_simulations_data import CleanupSimulationsData


class TestCleanupSimulationsData(unittest.TestCase):

    def setUp(self):
        # Use temporary directory for safer testing
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = self.temp_dir
        self._create_test_folder_structure()

    def tearDown(self):
        # Clean up temporary directory after each test
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_folder_structure(self):
        """Create a test folder structure with simulation directories and files."""
        data_path = Path(self.data_dir)
        data_path.mkdir(exist_ok=True)
        
        # Create simulation directories with different modification times
        simulation_dirs = ["simulation_001", "simulation_002", "simulation_003", "simulation_004"]
        
        for i, sim_dir in enumerate(simulation_dirs):
            sim_path = data_path / sim_dir
            sim_path.mkdir(exist_ok=True)
            
            # Create some test files in each simulation directory
            (sim_path / "config.json").write_text('{"simulation": "test"}')
            (sim_path / "results.csv").write_text("timestamp,value\n2023-01-01,100\n")
            (sim_path / "logs.txt").write_text("Simulation started\nSimulation completed\n")
            
            # Create a subdirectory with files
            sub_dir = sim_path / "output"
            sub_dir.mkdir(exist_ok=True)
            (sub_dir / "data.bin").write_bytes(b"binary data")
            
            # Set different modification times (simulate different creation times)
            # Newer simulations have higher timestamps
            timestamp = time.time() - (len(simulation_dirs) - i) * 3600  # 1 hour apart
            os.utime(sim_path, (timestamp, timestamp))

    def test_list_simulations(self):
        cleanup = CleanupSimulationsData(output_dir=self.data_dir)
        simulations = cleanup.list_simulations()

        print("Simulations found:", [sim.name for sim in simulations])
        
        # Assert correct number of simulations
        assert len(simulations) == 4
        
        # Assert correct order (newest first)
        # simulation_004 should be first (newest), simulation_001 should be last (oldest)
        assert simulations[0].name == "simulation_004"
        assert simulations[1].name == "simulation_003"
        assert simulations[2].name == "simulation_002"
        assert simulations[3].name == "simulation_001"

    def test_init_with_valid_directory(self):
        """Test initialization with valid directory."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir)
        assert cleanup.output_dir == Path(self.data_dir).resolve()
        assert cleanup.keep_recent == 3  # default value

    def test_init_with_custom_keep_recent(self):
        """Test initialization with custom keep_recent value."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=5)
        assert cleanup.keep_recent == 5

    def test_init_with_nonexistent_directory(self):
        """Test initialization raises FileNotFoundError for non-existent directory."""
        with self.assertRaises(FileNotFoundError) as context:
            CleanupSimulationsData(output_dir="/nonexistent/path")
        self.assertIn("does not exist", str(context.exception))

    def test_list_simulations_empty_directory(self):
        """Test list_simulations with empty directory."""
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        
        cleanup = CleanupSimulationsData(output_dir=empty_dir)
        simulations = cleanup.list_simulations()
        
        assert len(simulations) == 0

    def test_list_simulations_with_files_only(self):
        """Test list_simulations ignores files and returns only directories."""
        test_dir = os.path.join(self.temp_dir, "files_test")
        os.makedirs(test_dir)
        
        # Create some files
        Path(test_dir).joinpath("file1.txt").write_text("test")
        Path(test_dir).joinpath("file2.csv").write_text("data")
        
        cleanup = CleanupSimulationsData(output_dir=test_dir)
        simulations = cleanup.list_simulations()
        
        assert len(simulations) == 0

    def test_remove_old_simulations_success(self):
        """Test successful removal of old simulations."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=2)
        
        # Verify initial state
        initial_simulations = cleanup.list_simulations()
        assert len(initial_simulations) == 4
        
        # Remove old simulations
        result = cleanup.remove_old_simulations()
        
        # Verify results
        assert result is True
        remaining_simulations = cleanup.list_simulations()
        assert len(remaining_simulations) == 2
        
        # Verify the correct simulations remain (newest ones)
        assert remaining_simulations[0].name == "simulation_004"
        assert remaining_simulations[1].name == "simulation_003"

    def test_remove_old_simulations_no_removal_needed(self):
        """Test remove_old_simulations when no removal is needed."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=5)
        
        with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
            result = cleanup.remove_old_simulations()
            
            assert result is True
            mock_logger.info.assert_called_with("No old simulations to remove.")

    def test_remove_old_simulations_permission_error(self):
        """Test remove_old_simulations handles permission errors."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=2)
        
        with patch('shutil.rmtree', side_effect=PermissionError("Access denied")):
            with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
                result = cleanup.remove_old_simulations()
                
                assert result is False
                mock_logger.error.assert_called()

    def test_remove_old_simulations_os_error(self):
        """Test remove_old_simulations handles OS errors."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=2)
        
        with patch('shutil.rmtree', side_effect=OSError("File system error")):
            with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
                result = cleanup.remove_old_simulations()
                
                assert result is False
                mock_logger.error.assert_called()

    def test_remove_old_simulations_unexpected_error(self):
        """Test remove_old_simulations handles unexpected errors."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=2)
        
        with patch('shutil.rmtree', side_effect=Exception("Unexpected error")):
            with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
                result = cleanup.remove_old_simulations()
                
                assert result is False
                mock_logger.error.assert_called()

    def test_remove_old_simulations_list_error(self):
        """Test remove_old_simulations handles errors in list_simulations."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=2)
        
        with patch.object(cleanup, 'list_simulations', side_effect=Exception("List error")):
            with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
                result = cleanup.remove_old_simulations()
                
                assert result is False
                mock_logger.error.assert_called_with("Error during cleanup operation: List error")

    def test_remove_old_simulations_partial_failure(self):
        """Test remove_old_simulations stops on first failure."""
        cleanup = CleanupSimulationsData(output_dir=self.data_dir, keep_recent=1)
        
        # Mock rmtree to fail on second call
        call_count = 0
        def mock_rmtree(path):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise PermissionError("Access denied")
        
        with patch('shutil.rmtree', side_effect=mock_rmtree):
            with patch('app.cleanup.cleanup_simulations_data.logger') as mock_logger:
                result = cleanup.remove_old_simulations()
                
                assert result is False
                # Should have attempted to remove first simulation successfully
                assert call_count == 2

if __name__ == "__main__":
    unittest.main()
