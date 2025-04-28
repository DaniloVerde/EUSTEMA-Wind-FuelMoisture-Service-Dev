import os
import json
import logging
import shutil
from pathlib import Path
from .utils import create_station_csv_from_json_file, json_to_station_csv
from ..storage.minio_client import MinioClient

logger = logging.getLogger(__name__)


def generate_station_files_from_json(json_filepath, data_dir, model_id=None):
    """
    Genera file CSV per stazioni meteo a partire da un file JSON.

    Args:
        json_filepath (str): Percorso del file JSON contenente i dati delle stazioni meteo
        data_dir (str): Directory base per i dati di output
        model_id (str, optional): ID del modello da utilizzare, se non fornito verrà utilizzato quello nel JSON

    Returns:
        tuple: (model_id, csv_files, list_filepath)
    """
    logger.info(f"Generazione file stazioni da {json_filepath}")
    logger.debug(
        f"Parametri ricevuti: data_dir={data_dir}, model_id={model_id}")

    try:
        # Leggi il JSON se è stato fornito un filepath, altrimenti assumiamo che sia già stato caricato
        if isinstance(json_filepath, (str, Path)):
            logger.debug(f"Apertura file JSON da percorso: {json_filepath}")
            with open(json_filepath, 'r') as jsonfile:
                json_data = json.load(jsonfile)
        else:
            logger.debug("Elaborazione dati JSON già caricati in memoria")
            json_data = json_filepath
            json_filepath = "input JSON data"

        # Estrai model_id dal JSON se non specificato
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID estratto dal JSON: {model_id}")
            if not model_id:
                logger.error("Impossibile trovare modelId nel JSON")
                raise ValueError(
                    "modelId non trovato nel JSON e non specificato come parametro")

        # Genera i file CSV per le stazioni
        logger.debug(f"Avvio generazione CSV con model_id={model_id}")
        csv_files, list_filepath = json_to_station_csv(
            json_data, data_dir, model_id)
        logger.debug(f"File CSV generati: {len(csv_files)}")
        logger.debug(f"File lista stazioni creato: {list_filepath}")

        logger.info(
            f"Generazione completata: {len(csv_files)} stazioni per il modello {model_id}")
        return model_id, csv_files, list_filepath

    except Exception as e:
        logger.error(
            f"Errore nella generazione dei file stazioni da {json_filepath}: {str(e)}")
        raise


def download_elevation_file_from_minio(elevation_file_path, output_dir, model_id=None):
    """
    Scarica il file di elevazione da MinIO e lo salva nella directory specificata

    Args:
        elevation_file_path (str): Percorso del file di elevazione in MinIO
        output_dir (str): Directory dove salvare il file
        model_id (str, optional): ID del modello, necessario per inviare messaggi Kafka in caso di errore

    Returns:
        Path to the downloaded file
    """
    logger.debug(f"Avvio download file elevazione da: {elevation_file_path}")
    logger.debug(f"Directory di output: {output_dir}")

    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Directory di output verificata: {output_dir}")

        # Get the filename from the path
        filename = os.path.basename(elevation_file_path)
        local_file_path = os.path.join(output_dir, filename)
        logger.debug(f"Percorso file locale: {local_file_path}")

        # Initialize MinIO client and download the file
        logger.debug("Inizializzazione client MinIO")
        minio_client = MinioClient()

        # Remove the file if it already exists to avoid conflicts
        # if os.path.exists(local_file_path):
        #     os.remove(local_file_path)

        # Download directly to the final path
        logger.debug("Avvio download file...")
        minio_client.download_file(elevation_file_path, local_file_path)
        logger.debug(f"Download completato in: {local_file_path}")

        logger.info(f"Elevation file downloaded to {local_file_path}")
        return local_file_path
    except Exception as e:
        error_message = f"Errore nel download del file di elevazione '{elevation_file_path}' da MinIO: {str(e)}"
        logger.error(error_message)

        # Se è stato fornito un model_id, invia un messaggio Kafka
        if model_id:
            try:
                from ..messaging.kafka_producer import KafkaMessageProducer
                kafka_producer = KafkaMessageProducer()
                kafka_producer.send_simulation_failed(
                    simulation_id=model_id,
                    error_message=error_message
                )
                logger.info(
                    f"Messaggio di errore inviato a Kafka per il modello {model_id}")
            except Exception as kafka_err:
                logger.error(
                    f"Impossibile inviare messaggio Kafka: {str(kafka_err)}")

        # Risolleva l'eccezione per la gestione a livello superiore
        raise ValueError(error_message) from e


def generate_windninja_config(json_data, data_dir, model_id=None, elevation_file=None, wind_speed_file=None, wind_direction_file=None):
    """
    Genera un file di configurazione WindNinja forecast a partire dai dati JSON

    Args:
        json_data (dict): Dati JSON per la configurazione
        data_dir (str): Directory base per i dati di output
        model_id (str, optional): ID del modello, se non fornito viene preso dal JSON
        elevation_file (str, optional): Percorso locale del file di elevazione, se già scaricato
        wind_speed_file (str, optional): Percorso locale del file di velocità del vento, se già scaricato
        wind_direction_file (str, optional): Percorso locale del file di direzione del vento, se già scaricato

    Returns:
        str: Percorso del file di configurazione generato
    """
    logger.info("Generazione file di configurazione WindNinja forecast")
    logger.debug(
        f"Parametri: data_dir={data_dir}, model_id={model_id}, elevation_file={elevation_file}, wind_speed_file={wind_speed_file}, wind_direction_file={wind_direction_file}")

    try:
        # Estrai model_id dal JSON se non specificato
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID estratto dal JSON: {model_id}")
            if not model_id:
                logger.error("Impossibile trovare modelId nel JSON")
                raise ValueError(
                    "modelId non trovato nel JSON e non specificato come parametro")

        # Crea le directory di input e output
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(
            f"Directory create: input={input_dir}, output={output_dir}")

        # Se non è stato specificato il file di elevazione, scaricalo da MinIO
        # if not elevation_file and 'elevation_file' in json_data:
        #     elevation_file_path = json_data.get('elevation_file')
        #     logger.debug(
        #         f"File elevazione da scaricare: {elevation_file_path}")
        #     elevation_file = download_elevation_file_from_minio(
        #         elevation_file_path,
        #         input_dir,
        #         model_id
        #     )
        #     logger.debug(f"File elevazione scaricato: {elevation_file}")
        # elif not elevation_file:
        #     logger.error(
        #         "File di elevazione non specificato e non presente nel JSON")
        #     raise ValueError(
        #         "File di elevazione non specificato e non presente nel JSON")

        # # Se non è stato specificato il file di velocità del vento, scaricalo da MinIO
        # if not wind_speed_file and 'wind_speed_file' in json_data:
        #     wind_speed_file_path = json_data.get('wind_speed_file')
        #     logger.debug(
        #         f"File velocità del vento da scaricare: {wind_speed_file_path}")
        #     wind_speed_file = download_elevation_file_from_minio(
        #         wind_speed_file_path,
        #         input_dir,
        #         model_id
        #     )
        #     logger.debug(f"File velocità del vento scaricato: {wind_speed_file}")
        
        # # Se non è stato specificato il file di direzione del vento, scaricalo da MinIO
        # if not wind_direction_file and 'wind_direction_file' in json_data:
        #     wind_direction_file_path = json_data.get('wind_direction_file')
        #     logger.debug(
        #         f"File direzione del vento da scaricare: {wind_direction_file_path}")
        #     wind_direction_file = download_elevation_file_from_minio(
        #         wind_direction_file_path,
        #         input_dir,
        #         model_id
        #     )
        #     logger.debug(f"File direzione del vento scaricato: {wind_direction_file}")

        # Percorso del file di configurazione da generare
        config_file_path = os.path.join(input_dir, f"{model_id}_windninja_forecast.cfg")
        logger.debug(f"Percorso file di configurazione: {config_file_path}")

        # Percorso del file di configurazione da generare
        config_file_path = os.path.join(input_dir, f"{model_id}_windninja_forecast.cfg")
        logger.debug(f"Percorso file di configurazione: {config_file_path}")

        # Estrai e splitta il simulation_time
        simulation_time = json_data.get('simulation_time', '')
        logger.debug(f"Simulation time: {simulation_time}")
        
        # Formatto come "2024-04-28T15:30"
        try:
            # Estrai le componenti della data e ora dal formato ISO
            from datetime import datetime
            dt = datetime.fromisoformat(simulation_time)
            year = dt.year
            month = dt.month
            day = dt.day
            hour = dt.hour
            minute = dt.minute
            logger.debug(f"Componenti temporali estratte: year={year}, month={month}, day={day}, hour={hour}, minute={minute}")
        except Exception as e:
            logger.warning(f"Errore nel parsing della data simulation_time '{simulation_time}': {str(e)}")
            # Valori di default in caso di errore
            year = datetime.now().year
            month = datetime.now().month
            day = datetime.now().day
            hour = datetime.now().hour
            minute = datetime.now().minute
            logger.debug(f"Utilizzando valori di default: year={year}, month={month}, day={day}, hour={hour}, minute={minute}")

        # Crea il contenuto del file di configurazione
        logger.debug("Creazione contenuto file di configurazione")
        config_content = [
            "#",
            "#\tFile di configurazione WindNinja forecast generato automaticamente",
            "#",
            f"num_threads              = 4",
            f"elevation_file           = {elevation_file}",
            f"time_zone                = auto-detect",
            f"initialization_method    = griddedInitialization",
            f"match_points             = true",
            f"write_wx_station_kml     = true",
            f"input_speed_grid         = {wind_speed_file}",
            f"input_speed_units        = {json_data['input_speed_units']}",
            f"input_dir_grid           = {wind_direction_file}",
            f"input_wind_height        = {json_data['input_wind_height']}",
            f"units_input_wind_height  = {json_data['units_input_wind_height']}",
            f"diurnal_winds            = true",
            f"year                     = {year}",
            f"month                    = {month}",
            f"day                      = {day}",
            f"hour                     = {hour}",
            f"minute                   = {minute}",
            f"output_speed_units       = mps",
            f"output_wind_height       = {json_data['output_wind_height']}",
            f"units_output_wind_height = {json_data['units_output_wind_height']}",
            f"vegetation               = {json_data['vegetation']}",
            f"uni_air_temp             = {json_data['uni_air_temp']}",
            f"uni_cloud_cover          = {json_data['uni_cloud_cover']}",
            f"cloud_cover_units        = percent",
            f"mesh_resolution          = 500.0",
            f"units_mesh_resolution    = m",
            f"write_goog_output        = true",
            f"write_shapefile_output   = true",
            f"write_ascii_output       = true",
            f"write_farsite_atm        = false"
        ]

        # Scrivi il file di configurazione
        logger.debug(f"Scrittura file di configurazione: {config_file_path}")
        with open(config_file_path, 'w') as config_file:
            config_file.write('\n'.join(config_content))

        logger.info(
            f"File di configurazione WindNinja generato: {config_file_path}")
        return config_file_path

    except Exception as e:
        logger.error(
            f"Errore nella generazione del file di configurazione WindNinja: {str(e)}")
        raise


def process_windninja_input(json_filepath, data_dir, model_id=None):
    """
    Elabora i dati di input per WindNinja: genera i file CSV delle stazioni,
    scarica il file di elevazione e crea il file di configurazione

    Args:
        json_filepath (str or dict): Percorso del file JSON o dizionario JSON già caricato
        data_dir (str): Directory base per i dati di output
        model_id (str, optional): ID del modello, se non fornito viene preso dal JSON

    Returns:
        tuple: (model_id, csv_files, elevation_file, config_file)
    """
    logger.info(f"Elaborazione dati di input WindNinja da {json_filepath}")
    logger.debug(f"Parametri: data_dir={data_dir}, model_id={model_id}")

    try:
        # Leggi il JSON se è stato fornito un filepath, altrimenti assumiamo che sia già stato caricato
        if isinstance(json_filepath, (str, Path)):
            logger.debug(f"Apertura file JSON da percorso: {json_filepath}")
            with open(json_filepath, 'r') as jsonfile:
                json_data = json.load(jsonfile)
        else:
            logger.debug("Elaborazione dati JSON già caricati in memoria")
            json_data = json_filepath
            json_filepath = "input JSON data"

        # Estrai model_id dal JSON se non specificato
        if model_id is None:
            model_id = json_data.get('modelId')
            logger.debug(f"Model ID estratto dal JSON: {model_id}")
            if not model_id:
                logger.error("Impossibile trovare modelId nel JSON")
                raise ValueError(
                    "modelId non trovato nel JSON e non specificato come parametro")

        # Crea le directory di input e output
        input_dir = os.path.join(data_dir, model_id, "input")
        output_dir = os.path.join(data_dir, model_id, "output")
        logger.debug(
            f"Creazione directory: input={input_dir}, output={output_dir}")
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        # Scarica il file di elevazione da MinIO
        elevation_file = None
        if 'elevation_file' in json_data:
            logger.debug(
                f"Avvio download file elevazione: {json_data['elevation_file']}")
            # elevation_file = download_elevation_file_from_minio(
            #     json_data['elevation_file'],
            #     input_dir,
            #     model_id  # Passa il model_id alla funzione di download
            # )

            # Simulazione del download per il test
            elevation_file = os.path.join(
                input_dir, os.path.basename(json_data['elevation_file']))
            logger.debug(f"File elevazione scaricato: {elevation_file}")
        else:
            logger.debug("Nessun file di elevazione specificato nel JSON")

        wind_speed_file = None
        if 'wind_speed_file' in json_data:
            logger.debug(
                f"Avvio download file velocità del vento: {json_data['wind_speed_file']}")
            # elevation_file = download_elevation_file_from_minio(
            #     json_data['elevation_file'],
            #     input_dir,
            #     model_id  # Passa il model_id alla funzione di download
            # )

            # Simulazione del download per il test
            wind_speed_file = os.path.join(
                input_dir, os.path.basename(json_data['wind_speed_file']))
            logger.debug(
                f"File velocità del vento scaricato: {elevation_file}")
        else:
            logger.debug(
                "Nessun file di velocità del vento specificato nel JSON")

        wind_direction_file = None
        if 'wind_direction_file' in json_data:
            logger.debug(
                f"Avvio download file direzione del vento: {json_data['wind_direction_file']}")
            # elevation_file = download_elevation_file_from_minio(
            #     json_data['elevation_file'],
            #     input_dir,
            #     model_id  # Passa il model_id alla funzione di download
            # )

            # Simulazione del download per il test
            wind_direction_file = os.path.join(
                input_dir, os.path.basename(json_data['wind_direction_file']))
            logger.debug(
                f"File direzione del vento scaricato: {elevation_file}")
        else:
            logger.debug(
                "Nessun file di direzione del vento specificato nel JSON")

        # Genera il file di configurazione WindNinja
        logger.debug("Avvio generazione file configurazione WindNinja")
        config_file = generate_windninja_config(
            json_data,
            data_dir,
            model_id,
            elevation_file=elevation_file,
            wind_speed_file=wind_speed_file,
            wind_direction_file=wind_direction_file
        )
        logger.debug(f"File configurazione generato: {config_file}")

        logger.info(f"Elaborazione completata per il modello {model_id}")
        return model_id, elevation_file, wind_speed_file, wind_direction_file, config_file

    except Exception as e:
        logger.error(
            f"Errore nell'elaborazione dei dati di input WindNinja: {str(e)}")
        raise
