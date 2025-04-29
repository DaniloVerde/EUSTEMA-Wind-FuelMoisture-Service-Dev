import os
import json

from kafka import KafkaConsumer

KAFKA_BROKER = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.environ.get("KAFKA_TOPIC", "windninja-results")
if not TOPIC:
    raise ValueError("KAFKA_TOPIC environment variable is not set.")

# KAFKA_BROKER = 'localhost:9092' if KAFKA_BROKER == 'kafka:9092' else KAFKA_BROKER

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
)

print("Waiting for messages...")

for message in consumer:
    print(f"Received message: {message.value}")
