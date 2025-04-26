import os
import subprocess
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_windninja(config_file, working_dir=None, output_dir=None, timeout=None):
    """
    Esegue WindNinja con il file di configurazione specificato.
    
    Args:
        config_file (str): Percorso del file di configurazione
        working_dir (str, optional): Directory di lavoro per l'esecuzione
        timeout (int, optional): Timeout in secondi per l'esecuzione
        
    Returns:
        tuple: (exit_code, stdout, stderr)
    """
    logger.info(f"Avvio WindNinja con config_file: {config_file}")
    
    try:
        if output_dir:
            command = ["WindNinja_cli", "--output_path", output_dir, "--config_file", config_file]
        else:
            command = ["WindNinja_cli", "--config_file", config_file]
        
        # Esegui il comando WindNinja_cli
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=working_dir
        )
        
        # Attendi il completamento con timeout opzionale
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        
        if exit_code == 0:
            logger.info("WindNinja eseguito con successo")
        else:
            logger.error(f"WindNinja fallito con exit code {exit_code}")
            logger.error(f"Stderr: {stderr}")
        
        return exit_code, stdout, stderr
    
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout scaduto ({timeout}s) durante l'esecuzione di WindNinja")
        process.kill()
        return -1, "", "Timeout expired"
    
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione di WindNinja: {str(e)}")
        return -1, "", str(e)