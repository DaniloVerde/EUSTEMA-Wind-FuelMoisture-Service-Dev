import subprocess
import logging

logger = logging.getLogger(__name__)

def run_windninja(config_file, working_dir=None, output_dir=None, timeout=None):
    """
    Runs WindNinja with the specified configuration file.
    
    Args:
        config_file (str): Path to the configuration file
        working_dir (str, optional): Working directory for execution
        timeout (int, optional): Timeout in seconds for execution
        
    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    logger.info(f"Starting WindNinja with config_file: {config_file}")
    
    try:
        if output_dir:
            command = ["WindNinja_cli", "--output_path", output_dir, "--config_file", config_file]
        else:
            command = ["WindNinja_cli", "--config_file", config_file]
        
        # Execute WindNinja_cli command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=working_dir
        )
        
        # Wait for completion with optional timeout
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        
        if exit_code == 0:
            logger.info("WindNinja executed successfully")
        else:
            logger.error(f"WindNinja failed with exit code {exit_code}")
            logger.error(f"Stderr: {stderr}")
        
        return exit_code, stdout, stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout expired ({timeout}s) during WindNinja execution")
        process.kill()
        return -1, "", "Timeout expired"
    
    except Exception as e:
        logger.error(f"Error during WindNinja execution: {str(e)}")
        return -1, "", str(e)