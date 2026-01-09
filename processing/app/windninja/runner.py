import subprocess
import logging
import threading
from typing import List, Optional, TextIO, Callable

logger = logging.getLogger(__name__)


def _stream_pipe(
    pipe: Optional[TextIO],
    log_func: Callable[[str], None],
    buffer: List[str],
    prefix: str,
):
    if pipe is None:
        return
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            line = line.rstrip("\r\n")
            if not line:
                continue
            log_func(f"{prefix}{line}")
            buffer.append(line)
    finally:
        try:
            pipe.close()
        except Exception:
            pass

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
    process = None
    
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
            bufsize=1,
            cwd=working_dir,
        )

        stdout_lines: List[str] = []
        stderr_lines: List[str] = []

        stdout_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stdout, logger.info, stdout_lines, "[WindNinja stdout] "),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_stream_pipe,
            args=(process.stderr, logger.warning, stderr_lines, "[WindNinja stderr] "),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()

        # Wait for completion with optional timeout
        process.wait(timeout=timeout)
        exit_code = process.returncode

        # Ensure reader threads flush remaining output
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        
        if exit_code == 0:
            logger.info("WindNinja executed successfully")
        else:
            logger.error(f"WindNinja failed with exit code {exit_code}")
            logger.error(f"Stderr: {stderr}")
        
        return exit_code, stdout, stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout expired ({timeout}s) during WindNinja execution")
        if process is not None:
            try:
                process.kill()
            except Exception:
                pass
        return -1, "", "Timeout expired"
    
    except Exception as e:
        logger.error(f"Error during WindNinja execution: {str(e)}")
        if process is not None:
            try:
                process.kill()
            except Exception:
                pass
        return -1, "", str(e)