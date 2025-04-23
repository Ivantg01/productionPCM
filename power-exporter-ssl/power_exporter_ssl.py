import time
from datetime import datetime
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server
import json
from kafka import KafkaConsumer
import os

HTTP_PORT = int(os.getenv('EXPORTER_PORT', 9101))
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'PowerProd')
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-0:29092,kafka-1:29093,kafka-2:29094")
#Datos reportados por el exporter: { {"IP", registro_power_consumption}, }
POWER_DB = {}

#---- Class CustomCollector
class CustomCollector(object):
    def __init__(self):
        pass

    def collect(self):
        # Para cada direccion IP reportada, exponer las métricas como Gauge
        for ip, data in POWER_DB.items():
            print ("HTTP exporter request data-> RET %s, %s" % (ip, data), flush = True)
            lat = data.get('ne-latitude', '0');
            lon = data.get('ne-longitude', '0');

            # Métrica para current-power
            g_current_power = GaugeMetricFamily(
                "custom_current_power",
                "Current power consumption in watts",
                labels=['ne_ip_address','ne_name','lat','lon']
            )
            g_current_power.add_metric([ip, data['ne-name'], lat, lon], data['current-power'])
            yield g_current_power

            # Métrica para energy-consumption
            g_energy_consumption = GaugeMetricFamily(
                "custom_energy_consumption",
                "Total energy consumption in watt-hours",
                labels=['ne_ip_address','ne_name','lat','lon']
            )
            g_energy_consumption.add_metric([ip, data['ne-name'], lat, lon], data['energy-consumption'])
            yield g_energy_consumption

            # Métrica para onu-number
            g_onu_number = GaugeMetricFamily(
                "custom_onu_number",
                "Number of ONUs connected",
                labels=['ne_ip_address','ne_name','lat','lon']
            )
            g_onu_number.add_metric([ip, data['ne-name'], lat, lon], data['onu-number'])
            yield g_onu_number

            # Métrica para per-onu-energy-consumption
            g_per_onu_energy_consumption = GaugeMetricFamily(
                "custom_per_onu_energy_consumption",
                "Energy consumption per ONU in watt-hours",
                labels=['ne_ip_address','ne_name','lat','lon']
            )
            g_per_onu_energy_consumption.add_metric([ip, data['ne-name'], lat, lon], data['per-onu-energy-consumption'])
            yield g_per_onu_energy_consumption

#---- Function update_data_from_kafka_bus
def update_data_from_kafka_bus():
    # Getting the data as JSON

    # Consumidor para el topic kafka
    try:
        consumer = KafkaConsumer(KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
            security_protocol="SSL",
                    ssl_check_hostname=False,
                    ssl_cafile="./pem/ca-root.pem",
                    ssl_certfile="./pem/client-certificate.pem",
                    ssl_keyfile="./pem/client-private-key.pem",
                    value_deserializer=lambda m: json.loads(m.decode('ascii')))
    except Exception as e:
        print(f"Error al conectar con Kafka: {e}")
        return

    # Procesar los mensajes recibidos
    for message in consumer:
        new_data = message.value  # Obtener el mensaje completo como diccionario

        # Adaptamos de miliwatts a watts
        new_data['current-power'] = str(round(float(new_data['current-power']) / 1000.0,3))
        new_data['energy-consumption'] = str(round(float(new_data['energy-consumption']) / 1000.0,3))
        new_data['per-onu-energy-consumption'] = str(round(float(new_data['per-onu-energy-consumption']) / 1000.0,3))

        # Extraer los campos requeridos
        time_collected = new_data['time-collected']
        ne_name = new_data['ne-name']
        ne_ip_address = new_data['ne-ip-address']
        current_power = new_data['current-power']
        energy_consumption = new_data['energy-consumption']
        onu_number = new_data['onu-number']
        per_onu_energy_consumption = new_data['per-onu-energy-consumption']


        #si la IP esta ya registrada, actualizamos, en otro caso, añadimos
        operation = ""
        if ne_ip_address in POWER_DB:
            new_time_collected = datetime.strptime(new_data["time-collected"], "%Y-%m-%dT%H:%M:%S.%fZ")
            existing_time_collected = datetime.strptime(POWER_DB[ne_ip_address]["time-collected"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if new_time_collected > existing_time_collected:
                POWER_DB[ne_ip_address] = new_data
                operation = "UPD"
        else:
            POWER_DB[ne_ip_address] = new_data
            operation = "ADD"

        # Mostrar los datos extraídos
        if (operation):
            print("[%s] %s %s (%s), %s W, %s Wh, %s ONUs, %s W/onu" %
                  (time_collected, operation, ne_ip_address, ne_name, current_power, energy_consumption, onu_number, per_onu_energy_consumption), flush = True)

#---- function main
if __name__ == '__main__':
    # Iniciar el servidor HTTP en el puerto indicado
    start_http_server(HTTP_PORT)
    print ("HTTP server running in port " + str(HTTP_PORT))

    # Registrar el colector personalizado
    REGISTRY.register(CustomCollector())
    print ("Consumer attached to kafka topic %s @%s" % (KAFKA_TOPIC, KAFKA_BOOTSTRAP_SERVERS), flush = True)

    # Mantener el script en ejecución
    #while True:
    #    time.sleep(1)
    update_data_from_kafka_bus()
