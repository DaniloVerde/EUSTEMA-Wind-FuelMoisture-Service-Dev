#!/usr/bin/env python
"""
Script per avviare il consumer Kafka per il monitoraggio dei messaggi WindNinja.

Uso:
    python monitor_windninja.py [--bootstrap-servers SERVERS] [--topic TOPIC] [--simulation-id ID]

Esempi:
    python monitor_windninja.py
    python monitor_windninja.py --simulation-id 20250331080030
    python monitor_windninja.py --bootstrap-servers kafka:9092 --topic windninja-events
"""

import sys
import os

# Assicura che la directory dell'applicazione sia nel path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_dir not in sys.path:
    sys.path.append(app_dir)

from app.monitoring.kafka_consumer import main

if __name__ == "__main__":
    main()