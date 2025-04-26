import os
import time
import json

from kafka import KafkaProducer

KAFKA_BROKER = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

topic = "test-topic"

for i in range(10):
    message = {"number": i, "message": f"Message {i}"}
    producer.send(topic, message)
    print(f"Sent message {message}")
    time.sleep(1)

producer.flush()
producer.close()
