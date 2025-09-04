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
        
        stdout_lines = []
        stderr_lines = []

        # Lettura in tempo reale
        import threading

        def log_stream(stream, log_func, lines_list):
            for line in iter(stream.readline, ''):
                log_func(line.rstrip())
                lines_list.append(line)
            stream.close()

        stdout_thread = threading.Thread(target=log_stream, args=(process.stdout, logger.info, stdout_lines))
        stderr_thread = threading.Thread(target=log_stream, args=(process.stderr, logger.error, stderr_lines))
        stdout_thread.start()
        stderr_thread.start()
        stdout_thread.join(timeout)
        stderr_thread.join(timeout)

        exit_code = process.wait(timeout=timeout)

        return exit_code, ''.join(stdout_lines), ''.join(stderr_lines)
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout expired ({timeout}s) during WindNinja execution")
        process.kill()
        return -1, "", "Timeout expired"
    
    except Exception as e:
        logger.error(f"Error during WindNinja execution: {str(e)}")
        return -1, "", str(e)