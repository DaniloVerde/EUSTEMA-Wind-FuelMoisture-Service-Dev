# Wind and Fuel Moisture Service API

## Descrizione

Il **Wind and Fuel Moisture Service** è un'applicazione FastAPI per l'elaborazione di modelli di vento e calcolo dell'umidità del combustibile. Il servizio fornisce un'API REST per l'esecuzione di simulazioni WindNinja e calcoli di fuel moisture basati su dati meteorologici.

### Caratteristiche Principali

- **Simulazioni WindNinja**: Elaborazione di modelli di vento su terreni complessi
- **Calcolo Fuel Moisture**: Stima dell'umidità del combustibile per la valutazione del rischio incendi
- **Elaborazione Asincrona**: Processing in background con notifiche via Kafka
- **Storage MinIO**: Archiviazione automatica dei risultati
- **Health Check**: Endpoint per il monitoraggio dello stato del servizio
- **Documentazione API**: Swagger UI integrata

## Architettura del Sistema

Il servizio è composto da diversi moduli:

```
processing/app/
├── api/                    # API endpoints e modelli
│   ├── endpoints.py       # Route FastAPI
│   ├── models.py          # Modelli Pydantic
│   ├── enums.py           # Enumerazioni
│   └── tasks.py           # Tasks asincroni
├── config/                 # Configurazione
│   ├── settings.py        # Variabili di configurazione
│   └── logging_config.py  # Setup logging
├── windninja/             # Gestione WindNinja
├── windninja_forecast/    # Elaborazione previsioni
├── fuel_moisture/         # Calcolo fuel moisture
├── storage/               # Client MinIO
├── messaging/             # Client Kafka
├── cleanup/               # Pulizia dati obsoleti
└── main.py               # Entry point applicazione
```

## Deploy Docker

### Servizio Processing

Il servizio `processing` è containerizzato e può essere deployato indipendentemente dagli altri componenti dell'infrastruttura (Kafka, MinIO, ZooKeeper).

#### Build dell'Immagine

```bash
cd processing
docker build -t wind-fuel-moisture-service .
```

#### Esecuzione del Container

```bash
docker run -d \
  --name processing \
  -p 8000:8000 \
  -v ./data:/data \
  -e MINIO_ENDPOINT=minio-server:9000 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka-server:9092 \
  -e MINIO_ACCESS_KEY=your_access_key \
  -e MINIO_SECRET_KEY=your_secret_key \
  wind-fuel-moisture-service
```

#### Variabili d'Ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `ROOT_PATH` | Path radice dell'API | `/` |
| `DEBUG` | Modalità debug | `false` |
| `MINIO_ENDPOINT` | Endpoint del server MinIO | `minio:9000` |
| `MINIO_ACCESS_KEY` | Chiave di accesso MinIO | `minioadmin` |
| `MINIO_SECRET_KEY` | Chiave segreta MinIO | `minioadmin` |
| `MINIO_BUCKET` | Nome del bucket MinIO | `cu68` |
| `MINIO_FORECAST_BUCKET` | Nome del bucket MinIO per previsioni | `forecast-data` |
| `FEWS_MINIO_ENDPOINT` | Endpoint MinIO per FEWS (usato solo se `fews=true`) | (fallback: `MINIO_ENDPOINT`) |
| `FEWS_MINIO_ACCESS_KEY` | Access key MinIO per FEWS (solo se `fews=true`) |  |
| `FEWS_MINIO_SECRET_KEY` | Secret key MinIO per FEWS (solo se `fews=true`) |  |
| `FEWS_MINIO_USE_SSL` | Usa SSL per MinIO FEWS (solo se `fews=true`) | (fallback: `MINIO_USE_SSL`) |
| `FEWS_MINIO_BUCKET` | Bucket MinIO per input/output FEWS (solo se `fews=true`) |  |
| `FEWS_MINIO_FORECAST_BUCKET` | Bucket MinIO FEWS per forecast (solo se `fews=true`) |  |
| `KAFKA_BOOTSTRAP_SERVERS` | Server Kafka | `kafka:9092` |
| `KAFKA_TOPIC` | Topic per notifiche | `windninja-results` |
| `FEWS_KAFKA_BOOTSTRAP_SERVERS` | Server Kafka per FEWS (solo se `fews=true`) | (fallback: `KAFKA_BOOTSTRAP_SERVERS`) |
| `FEWS_KAFKA_SECURITY_PROTOCOL` | Security protocol Kafka FEWS (solo se `fews=true`) | (fallback: `KAFKA_SECURITY_PROTOCOL`) |
| `FEWS_KAFKA_SASL_MECHANISM` | SASL mechanism Kafka FEWS (solo se `fews=true`) | (fallback: `KAFKA_SASL_MECHANISM`) |
| `FEWS_KAFKA_USERNAME` | Username Kafka FEWS (solo se SASL e `fews=true`) |  |
| `FEWS_KAFKA_PASSWORD` | Password Kafka FEWS (solo se SASL e `fews=true`) |  |
| `FEWS_KAFKA_REQUEST_TIMEOUT_MS` | Request timeout Kafka FEWS (solo se `fews=true`) | (fallback: `KAFKA_REQUEST_TIMEOUT_MS`) |
| `FEWS_KAFKA_TOPIC_RESULTS` | Topic Kafka FEWS per notifiche risultati (solo se `fews=true`) | `fews-windninja-results` |
| `LOG_LEVEL` | Livello di logging | `INFO` |
| `LOG_FILE` | Percorso del file di log WindNinja | `/app/logs/windninja.log` |
| `LOG_TAIL_DEFAULT_LINES` | Numero righe di default per l’endpoint log | `50` |

Note FEWS:
- Il parametro di request `fews` (default `false`) abilita l'uso di bucket/credenziali MinIO e configurazione Kafka dedicate.
- Se `fews=false`, il comportamento rimane invariato e vengono usate le variabili standard `MINIO_*` e `KAFKA_*`.

### Deploy con Docker Compose (Completo)

Per un deploy completo dell'ambiente di sviluppo:

```bash
# Clone del repository
git clone <repository-url>
cd EUSTEMA-Wind-FuelMoisture-Service

# Avvio dell'ambiente completo
docker-compose up -d

# Solo il servizio processing
docker-compose up -d processing
```

Il servizio sarà disponibile su:
- API: http://localhost:8000
- Documentazione: http://localhost:8000/api-docs
- Health Check: http://localhost:8000/health

## API Endpoints

### 1. Health Check

**GET** `/health`

Verifica lo stato del servizio.

**Risposta:**
```json
{
  "status": "online",
  "service": "Wind and Fuel Moisture service API",
  "version": "1.0.0",
  "uptime": "0d 2h 15m 30s"
}
```

### 2. Elaborazione WindNinja con Stazioni Meteorologiche

**POST** `/process`

Avvia un'elaborazione WindNinja utilizzando dati di stazioni meteorologiche.

**Content-Type:** `application/json`

**Parametri Input:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `modelId` | string | Sì | Identificativo univoco del modello |
| `elevation_file` | string | Sì | Percorso del file di elevazione (formato .tif/.asc) |
| `fews` | boolean | No | Se `true` usa configurazione FEWS (bucket/credenziali MinIO e Kafka dedicati). Default `false` |
| `output_wind_height` | float | No | Altezza output del vento (default: 10.0) |
| `units_output_wind_height` | string | No | Unità altezza output ("m", "ft") |
| `vegetation` | string | No | Tipo di vegetazione ("trees", "brush", "grass") |
| `meteorological_stations` | array | Sì | Array di stazioni meteorologiche |

**Struttura Stazione Meteorologica:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `station_name` | string | Sì | Nome della stazione |
| `coord_sys` | string | No | Sistema di coordinate ("GEOGCS") |
| `datum` | string | No | Datum ("WGS84") |
| `lat_ycoord` | float | Sì | Latitudine |
| `lon_xcoord` | float | Sì | Longitudine |
| `height` | float | Sì | Altezza di misurazione |
| `height_units` | string | No | Unità altezza ("meters", "feet") |
| `speed` | float | Sì | Velocità del vento |
| `speed_units` | string | No | Unità velocità ("mps", "kph", "mph", "kts") |
| `direction` | float | Sì | Direzione del vento (0-360°) |
| `temperature` | float | Sì | Temperatura (-30 a 60°C) |
| `temperature_units` | string | No | Unità temperatura ("C", "F") |
| `cloud_cover` | float | No | Copertura nuvolosa (0-100%) |
| `date_time` | datetime | No | Data e ora della misurazione |
| `dict_metadata` | object | No | Metadati addizionali |

**Esempio Payload:**
```json
{
  "modelId": "20250331080030",
  "elevation_file": "input/w46575_s10.tif",
  "fews": false,
  "output_wind_height": 10,
  "units_output_wind_height": "m",
  "vegetation": "trees",
  "meteorological_stations": [
    {
      "station_name": "1",
      "coord_sys": "GEOGCS",
      "datum": "WGS84",
      "lat_ycoord": 42.197217162329451,
      "lon_xcoord": 12.163408697089425,
      "height": 10,
      "height_units": "meters",
      "speed": 5,
      "speed_units": "mps",
      "direction": 80,
      "temperature": 24,
      "temperature_units": "C",
      "cloud_cover": 0,
      "date_time": "2025-03-31T08:00"
    }
  ],
  "dict_metadata": {
    "author": "Mario Rossi",
    "project": "WindNinja",
    "x-amz-meta-custom": "valore_custom",
    "description": "File generato da WindNinja"
  }
}
```

**Risposta (202 Accepted):**
```json
{
  "modelId": "20250331080030",
  "status": "accepted",
  "message": "Processing started, you will be notified via Kafka when complete",
  "timestamp": "2025-07-11T10:30:00"
}
```

### 3. Elaborazione WindNinja con Dati di Previsione

**POST** `/forecast`

Avvia un'elaborazione WindNinja utilizzando dati di previsione su griglia.

**Content-Type:** `application/json`

**Parametri Input:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `modelId` | string | Sì | Identificativo univoco del modello |
| `elevation_file` | string | Sì | Percorso del file di elevazione |
| `fews` | boolean | No | Se `true` usa configurazione FEWS (bucket/credenziali MinIO e Kafka dedicati). Default `false` |
| `input_wind_height` | float | No | Altezza input del vento (default: 10.0) |
| `units_input_wind_height` | string | No | Unità altezza input ("m", "ft") |
| `output_wind_height` | float | No | Altezza output del vento (default: 10.0) |
| `units_output_wind_height` | string | No | Unità altezza output ("m", "ft") |
| `vegetation` | string | No | Tipo di vegetazione |
| `wind_file` | string | Sì | File griglia previsioni con componenti del vento |
| `u_band` | integer | No | Banda componente U nel file griglia (default: 1) |
| `v_band` | integer | No | Banda componente V nel file griglia (default: 2) |
| `input_speed_units` | string | No | Unità velocità input ("mps", "kph", "mph", "kts") |
| `uni_air_temp` | float | Sì | Temperatura uniforme dell'aria |
| `uni_cloud_cover` | float | No | Copertura nuvolosa uniforme |
| `simulation_time` | datetime | No | Tempo di simulazione |
| `dict_metadata` | object | No | Metadati addizionali |

**Esempio Payload:**
```json
{
  "modelId": "20250331080030",
  "elevation_file": "input/w46575_s10.tif",
  "fews": false,
  "input_wind_height": 10,
  "units_input_wind_height": "m",
  "output_wind_height": 10,
  "units_output_wind_height": "m",
  "vegetation": "trees",
  "wind_file": "input/cog_ICON_2I_SURFACE_PRESSURE_LEVELS202507180000.tiff",
  "u_band": 1,
  "v_band": 2,
  "input_speed_units": "mps",
  "uni_air_temp": 24,
  "uni_cloud_cover": 0,
  "simulation_time": "2025-03-31T12:00",
  "dict_metadata": {
    "author": "Mario Rossi",
    "project": "WindNinja",
    "x-amz-meta-custom": "valore_custom",
    "description": "File generato da WindNinja"
  }
}
```

**Risposta (202 Accepted):**
```json
{
  "modelId": "20250331080030",
  "status": "accepted",
  "message": "Processing started, you will be notified via Kafka when complete",
  "timestamp": "2025-07-11T10:30:00"
}
```

### 4. Calcolo Fuel Moisture

**POST** `/fuel-moisture`

Calcola l'umidità del combustibile basata su osservazioni meteorologiche.

**Content-Type:** `application/json`

**Parametri Input:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `modelId` | string | Sì | Identificativo univoco del modello |
| `meteorological_stations` | array | Sì | Array di stazioni con osservazioni |

**Struttura Stazione Fuel Moisture:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `station_name` | string | Sì | Nome della stazione |
| `lat` | float | Sì | Latitudine (-90 a 90) |
| `lon` | float | Sì | Longitudine (-180 a 180) |
| `observations` | array | Sì | Array di osservazioni temporali |

**Struttura Osservazione:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `datetime` | datetime | Sì | Data e ora dell'osservazione |
| `measurement` | object | Sì | Misurazioni meteorologiche |

**Struttura Misurazione:**

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|--------------|-------------|
| `temperature` | float | Sì | Temperatura (-30 a 60°C) |
| `humidity` | float | Sì | Umidità relativa (0-100%) |
| `precipitation` | float | Sì | Precipitazioni (≥0 mm) |
| `solar_radiation` | float | Sì | Radiazione solare (≥0 W/m²) |

**Esempio Payload:**
```json
{
  "modelId": "20250331080030",
  "meteorological_stations": [
    {
      "station_name": "1",
      "lat": 42.197217162329451,
      "lon": 12.163408697089425,
      "observations": [
        {
          "datetime": "2025-03-01T18:00:00",
          "measurement": {
            "temperature": 24.0,
            "humidity": 50.0,
            "precipitation": 5.0,
            "solar_radiation": 1000.0
          }
        },
        {
          "datetime": "2025-03-01T17:00:00",
          "measurement": {
            "temperature": 25.2,
            "humidity": 48.5,
            "precipitation": 3.0,
            "solar_radiation": 1200.0
          }
        }
      ]
    }
  ]
}
```

**Risposta (200 OK):**
```json
{
  "modelId": "20250331080030",
  "meteorological_stations": [
    {
      "station_name": "1",
      "lat": 42.197217162329451,
      "lon": 12.163408697089425,
      "observations": [
        {
          "datetime": "2025-03-01T18:00:00",
          "measurement": {
            "temperature": 24.0,
            "humidity": 50.0,
            "precipitation": 5.0,
            "solar_radiation": 1000.0
          }
        }
      ],
      "fuel_moisture": 12.5
    }
  ]
}
```

### 5. Lettura/Download Log WindNinja

**GET** `/logs/windninja`

Permette di ottenere le ultime *N* righe del file di log `windninja.log` oppure scaricare l’intero file.

**Query parameters:**

| Parametro | Tipo | Default | Descrizione |
|----------|------|---------|-------------|
| `lines` | integer | `LOG_TAIL_DEFAULT_LINES` (50) | Numero di righe finali da restituire (usato solo se `download=false`) |
| `download` | boolean | `false` | Se `true`, restituisce il file completo come download |

**Esempi:**

```bash
# Ultime 50 righe (default)
curl -s "http://localhost:8000/logs/windninja"

# Ultime 200 righe
curl -s "http://localhost:8000/logs/windninja?lines=200"

# Download file intero
curl -L -o windninja.log "http://localhost:8000/logs/windninja?download=true"
```

## Modelli di Dati

### Enumerazioni Supportate

| Enum | Valori Possibili | Descrizione |
|------|------------------|-------------|
| `CoordinateSystem` | GEOGCS, PROJCS | Sistema di coordinate |
| `Datum` | WGS84, NAD83, NAD27 | Sistema di riferimento |
| `HeightUnits` | meters, feet | Unità di altezza |
| `SpeedUnits` | mps, kph, mph, kts | Unità di velocità |
| `TemperatureUnits` | C, F | Unità di temperatura |
| `VegetationType` | trees, brush, grass | Tipo di vegetazione |
| `WindHeightUnits` | m, ft | Unità altezza vento |

### Validazioni

- **Coordinate**: Latitudine [-90, 90], Longitudine [-180, 180]
- **Temperatura**: Range [-30, 60] °C
- **Direzione vento**: Range [0, 360] gradi
- **Velocità vento**: Valori ≥ 0
- **Umidità**: Range [0, 100] %
- **Copertura nuvolosa**: Range [0, 100] %
- **File extensions**: Solo .tif e .asc supportati

## Logging e Monitoraggio

### Configurazione Logging

Il servizio utilizza un sistema di logging configurabile:

- **Livelli**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Output**: File rotativo e console
- **Formato**: Timestamp, nome modulo, livello, messaggio
- **Rotazione**: 10MB per file, 5 backup

### Metriche di Sistema

- **Uptime**: Tempo di attività del servizio
- **Health status**: Stato online/offline
- **Processing status**: Monitoraggio tramite Kafka

## Gestione Errori

### Codici di Stato HTTP

| Codice | Descrizione |
|--------|-------------|
| 200 | Successo (fuel-moisture) |
| 202 | Richiesta accettata (process, forecast) |
| 400 | Errore di validazione input |
| 500 | Errore interno del server |

### Formato Errori

```json
{
  "detail": "Descrizione dell'errore",
  "status_code": 400
}
```

## Sviluppo e Testing

### Requisiti di Sistema

- Python 3.8+
- Docker 20.10+
- WindNinja CLI
- Accesso a MinIO e Kafka

### Setup Ambiente di Sviluppo

```bash
# Clone del repository
git clone <repository-url>
cd EUSTEMA-Wind-FuelMoisture-Service/processing

# Installazione dipendenze
pip install -r requirements.txt

# Avvio in modalità debug
python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m fastapi run app/main.py
```

### Testing

```bash
# Esecuzione test
cd processing
python -m pytest app/tests/

# Coverage report
python -m pytest --cov=app app/tests/
```

### Struttura Test

```
app/tests/
├── test_api_endpoints.py          # Test endpoints API
├── test_fuel_moisture_processing.py # Test calcolo fuel moisture
├── test_integration.py            # Test di integrazione
└── test_windninja_*.py           # Test componenti WindNinja
```

## Dipendenze Principali

| Libreria | Versione | Scopo |
|----------|----------|-------|
| FastAPI | 0.115.12 | Framework web API |
| Pydantic | 2.10.6 | Validazione dati |
| kafka-python | 2.1.5 | Client Kafka |
| minio | 7.2.10 | Client MinIO |
| rasterio | 1.3.11 | Gestione dati geospaziali |
| pandas | 2.0.3 | Elaborazione dati |
| numpy | 1.24.4 | Calcoli numerici |

## Sicurezza

### Best Practices Implementate

- Validazione input rigorosa
- Gestione errori centralizzata
- Logging sicuro (no password in log)
- Configurazione tramite variabili d'ambiente
- Limitazione CORS (configurabile)

### Raccomandazioni per Produzione

- Configurare CORS restrittivo
- Utilizzare HTTPS
- Implementare autenticazione/autorizzazione
- Configurare rate limiting
- Monitoraggio sicurezza e audit logs

## Licenza

Questo progetto è distribuito sotto licenza [inserire licenza].

## Contributi

Per contribuire al progetto:

1. Fork del repository
2. Creare branch feature (`git checkout -b feature/nuova-funzionalita`)
3. Commit delle modifiche (`git commit -am 'Aggiunta nuova funzionalità'`)
4. Push del branch (`git push origin feature/nuova-funzionalita`)
5. Aprire una Pull Request

## Supporto

Per supporto tecnico e segnalazioni bug:

- Email: info@innovazioniperlaterra.org

---

**Nota**: Questo servizio è progettato per funzionare in un ambiente containerizzato con accesso a servizi Kafka e MinIO esterni per la gestione di messaggi e storage.
