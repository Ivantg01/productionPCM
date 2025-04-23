from kafka import KafkaProducer
from time import sleep
import json
from datetime import datetime, timezone, timedelta
import time
import random
import hashlib
import csv
import os
from multiprocessing import Process, Lock

def get_hash_number_from_site(site_name):
    # Hash using SHA-256
    hash_object = hashlib.sha256(site_name.encode())
    # Convert hash to a number
    hash_int = int(hash_object.hexdigest(), 16)
    return hash_int

def read_file_csv(ruta_archivo):
    try:
        with open(ruta_archivo, 'r', newline='') as archivo:
            # Crear un lector CSV
            lector_csv = csv.reader(archivo, delimiter=';')
            
            # Leer todas las filas
            datos = list(lector_csv)
            
            # Verificar si el archivo está vacío
            if not datos:
                print("El archivo está vacío.")
                return None
            
            # Convertir los datos a un formato más manejable (lista de diccionarios)
            encabezados = datos[0]
            datos_formateados = [dict(zip(encabezados, fila)) for fila in datos[1:]]
            return datos_formateados
    except FileNotFoundError:
        print("El archivo no existe.")
        return None
    except csv.Error:
        print("Error al parsear el archivo.")
        return None


# Function to simulate power consumption based on current time
def simulate_power_metric(site):
    #Power distribution depending on time of the day
    distribution = [1.0, 0.9, 0.8, 0.7, 0.6, 0.8, 0.9, 1.0, 1.2, 1.3, 1.4, 1.6
                   ,1.6, 1.5, 1.7, 1.7, 1.6, 1.5, 1.4, 1.3, 1.5, 1.4, 1.3, 1.2]
    current_time = datetime.now(timezone.utc)

    #power depending on weekday and time
    weekend_factor = 1.0 if current_time.weekday() < 5 else 0.6
    hours = current_time.hour
    minutes = current_time.minute

    # Theoretical power
    base_power = site['reference_power'] * distribution[hours] *  weekend_factor
    next_hour = (hours + 1) % 24
    next_base_power = site['reference_power'] * distribution[next_hour] * weekend_factor
    theoretical_power = base_power + (next_base_power - base_power) * (minutes / 60.0)

    # Past power values
    last_power = site.setdefault('last_power', theoretical_power)
    last_theoretical = site.setdefault('last_theoretical', theoretical_power)
    
    # Límites de variación permitida
    max_variation_2h = 0.40  # ±40% máximo en 2 horas
    max_step_variation = 0.05  # ±5% máximo entre mediciones
    
    # Cálculo de límites dinámicos
    upper_limit = min(theoretical_power * (1 + max_variation_2h), last_power * (1 + max_step_variation))
    lower_limit = max(theoretical_power * (1 - max_variation_2h), last_power * (1 - max_step_variation))
    
    # Factor de convergencia progresiva (ajusta este valor para mayor/menor velocidad de convergencia)
    convergence_factor = 0.3  # 30% de ajuste hacia el valor teórico
    
    # Efecto maximo consumo en el 1% de los casos
    if random.random() < 0.01:  # 1% de probabilidad
        # Determinar dirección hacia el máximo permitido
        current_deviation = (last_power - theoretical_power) / theoretical_power
        target_deviation = 0.40 if current_deviation < 0 else -0.40
        direction = 1 if (target_deviation - current_deviation) > 0 else -1
        
        random_variation = direction * max_step_variation
        print(f"Desviación máxima aplicada ({'↑' if direction > 0 else '↓'}5%) en {site['code']}")
    else:
        random_variation = random.uniform(-max_step_variation, max_step_variation)

    # Cálculo de nueva potencia con variabilidad controlada
    new_power = last_power * (1 + random_variation)
    
    # Aplicar convergencia hacia el valor teórico
    new_power = new_power * (1 - convergence_factor) + theoretical_power * convergence_factor
    
    # Asegurar límites
    new_power = max(lower_limit, min(upper_limit, new_power))
    
    # Actualizar valores históricos
    site['last_power'] = new_power
    site['last_theoretical'] = theoretical_power


    data = {
        "time-collected": current_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        "resource-id": "e805d8a1-4dc8-4eae-b686-" + str(site['site_hash'])[:10],
        "ne-name": "OLT-"+ str(site['code']) + "-01",
        "ne-ip-address": "10." + str(site['code'])[:2] + "." + str(site['code'])[2:4] + "." + str(site['code'])[4:7],
        "current-power": str(round(new_power, 2)),
        "energy-consumption": str(round(new_power / 4, 2)),
        "onu-number": str(20 + int((site['site_hash'] % 1500000) * 3000 / 1500000) + random.randint(-20, 20)),
        "ne-latitude": site['latitude'],
        "ne-longitude": site['longitude']
    }
    data["per-onu-energy-consumption"] = str(int(float(data["energy-consumption"]) / int(data["onu-number"])))

    return json.loads(json.dumps(data))

#Process to send kafka messages with metrics simulating multiple OLTs
def worker(lock, file_name, start_index, end_index, process_id, update_delta):
    # Configure kafka Producer
    topic = os.getenv("TOPIC_NAME", "PowerProd")
    bootstrap_servers=os.getenv("BOOTSTRAP_SERVERS", "kafka-0:29092,kafka-1:29093,kafka-2:29094").split(",")

    producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
        security_protocol="SSL",
        ssl_check_hostname=False,
        ssl_cafile="./pem/ca-root.pem",
        ssl_certfile="./pem/client-certificate.pem",
        ssl_keyfile="./pem/client-private-key.pem",
        value_serializer=lambda m: json.dumps(m).encode('ascii'))

    #read just the specific lines from csv to this process
    sites = read_file_csv(file_name)
    sites = sites[start_index:end_index]

    for site in sites:
        # Agregar un campo 'update' con fechas aleatorias
        site['update'] = datetime.now() + timedelta(seconds=random.randint(0, update_delta))
        site['counter'] = 0;
        site_hash = get_hash_number_from_site(site['site'])
        site['site_hash'] = site_hash
        site['reference_power'] = 200000 + (site_hash % 1500000) 

    print(f"[{datetime.now()}] Process: {process_id} ready")


    while True:
        for index, site in enumerate(sites):
            if datetime.now() >= site['update']:
                with lock:
                    print(f"[{datetime.now()}] Process: {process_id} Counter: {site['counter']} Row: {index:03d} Site: {site['code']}", end='', flush = True)
                    data_to_send = simulate_power_metric(site)
                    producer.send(topic, data_to_send)
                    print(" [ok]")

                    # Update time to the next report slot
                    site['update'] = datetime.now() + timedelta(seconds=update_delta)
                    site['counter'] += 1
        time.sleep(random.uniform(5, 10))  # Esperar some time before next check

# Example of JSON data sent by the OLT
# data = {
#     "time-collected": "2022-04-15T04:15:20.361Z",
#     "resource-id": "e805d8a1-4dc8-4eae-b686-22975c9ac6b7",
#     "ne-name": "baa_ne_1",
#     "ne-ip-address": "192.168.0.1",
#     "current-power": "500000",
#     "energy-consumption": "125000",
#     "onu-number": "10",
#     "per-onu-energy-consumption": "890"
# }
# Convert JSON data to a Python dictionary
# data_dict = json.loads(json.dumps(data))

def main():

    #load csv with format site;province;city;code;lat;lon
    file_name = 'sites.csv'
    sites = read_file_csv(file_name)

    # Crear un lock para sincronizar el acceso a la impresión
    lock = Lock()

    # Divide the metric generation among several process
    num_processes = 1   # number of parallel process that will generate metric reports
    update_delta = 900;  # reporting seconds between 2 consecutive metric reports for each node
    chunk_size = len(sites) // num_processes

    # Create processes
    processes = []
    for i in range(num_processes):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size if i < num_processes - 1 else len(sites)
        p = Process(target=worker, args=(lock, file_name, start_index, end_index, i+1, update_delta))
        processes.append(p)
        p.start()

    # Wait to all the process to finish
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()

