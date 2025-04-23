from kafka import KafkaConsumer
import json
import time

def print_info(msg: dict):
    for t, v in msg.items():
        for r in v:
            print(json.dumps(r.value, indent=4)) # Mostrar los datos

consumer = KafkaConsumer(
    'PowerProd',
    bootstrap_servers=['kafka-0:29092','kafka-1:29093','kafka-2:29094'],
    security_protocol="SSL",
    ssl_check_hostname=False,
    ssl_cafile="../kafka-cluster-ssl/pem/ca-root.pem",
    ssl_certfile="../kafka-cluster-ssl/pem/client-certificate.pem",
    ssl_keyfile="../kafka-cluster-ssl/pem/client-private-key.pem",
#    consumer_timeout_ms = 2000,
    value_deserializer=lambda m: json.loads(m.decode('ascii')),
)

# Procesar los mensajes recibidos
try:
    while True:
        msg = consumer.poll(timeout_ms=1000)
        if msg is None:
            continue
        print_info(msg)
        time.sleep(1)
except KafkaError as error:
    print(error)



