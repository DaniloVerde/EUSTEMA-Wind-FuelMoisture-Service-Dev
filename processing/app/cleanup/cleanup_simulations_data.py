from pathlib import Path
from typing import List
import logging
import shutil

logger = logging.getLogger(__name__)


class CleanupSimulationsData:

    def __init__(self, output_dir: str, keep_recent: int = 3):
        self.output_dir = Path(output_dir).resolve()
        self.keep_recent = keep_recent

        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory {self.output_dir} does not exist.")
        
    def list_simulations(self) -> List[Path]:
        """
        List all simulation directories in the output directory.
        Returns directories sorted by modification date (newest first).
        """
        directories = [d for d in self.output_dir.iterdir() if d.is_dir()]
        return sorted(directories, key=lambda d: d.stat().st_mtime, reverse=True)
    
    def remove_old_simulations(self) -> bool:
        """
        Remove old simulation directories, keeping only the most recent ones.
        Returns True if operation was successful, False otherwise.
        """
        try:
            simulations = self.list_simulations()
            if len(simulations) <= self.keep_recent:
                logger.info("No old simulations to remove.")
                return True
            
            # Keep only the most recent simulations
            simulations_to_remove = simulations[self.keep_recent:]
            
            for sim in simulations_to_remove:
                try:
                    logger.info(f"Removing old simulation: {sim}")
                    shutil.rmtree(sim)
                    logger.info(f"Successfully removed simulation: {sim}")
                except PermissionError as e:
                    logger.error(f"Permission denied when removing simulation {sim}: {e}")
                    return False
                except OSError as e:
                    logger.error(f"OS error when removing simulation {sim}: {e}")
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error when removing simulation {sim}: {e}")
                    return False
            
            logger.info(f"Successfully removed {len(simulations_to_remove)} old simulations")
            return True
            
        except Exception as e:
            logger.error(f"Error during cleanup operation: {e}")
            return False