from kafka import KafkaProducer
from time import sleep
import json
from datetime import datetime, timezone
import time
import random

#Power distribution depending on time of the day
#distribution = [1.0, 0.9, 0.8, 0.7, 0.6, 0.8, 0.9, 1.0, 1.2, 1.3, 1.4, 1.6
#               ,1.6, 1.5, 1.7, 1.7, 1.6, 1.5, 1.4, 1.3, 1.5, 1.4, 1.3, 1.2]
distribution = [1.0, 0.9, 0.8, 0.7, 0.6, 0.8, 0.9, 1.0, 1.2, 1.3, 1.4, 1.6
               ,1.6, 1.5, 1.7, 1.7, 1.6, 1.5, 1.4, 1.3, 1.5, 1.4, 1.3, 1.2]

# Function to simulate power consumption based on current time
def simulate_power_consumption(data, reference_power):
    current_time = datetime.now(timezone.utc)

    #power depending on weekday
    if current_time.weekday() < 5:  # Weekdays
        weekend_factor = 1.0;
    else:  # Weekends
        weekend_factor = 0.6;

    #get current hour and minute
    hours = current_time.hour
    minutes = current_time.minute
    base_power = reference_power * distribution[hours] *  weekend_factor

    #get next hour
    next_hour = (hours + 1) % 24
    next_base_power = reference_power * distribution[next_hour] * weekend_factor

    power = base_power + (next_base_power - base_power) * (minutes / 60.0)

    node = random.randint(1, 5)
    data["time-collected"] = current_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    data["resource-id"] = "e805d8a1-4dc8-4eae-b686-22975c9ac6b" + str(node)
    data["ne-name"] = "node_" + str(node)
    data["ne-ip-address"] = "192.168.0." + str(node)
    data["current-power"] = str( round( float(power) + (node-1) * 200000, 2))
    data["energy-consumption"] = str( round( float(data["current-power"]) / 4, 2))
    data["onu-number"] = str(100 * node + random.randint(-20, 20))
    data["per-onu-energy-consumption"] = str(int(float(data["energy-consumption"]) / int(data["onu-number"])))

    return data


# Producing as JSON
producer = KafkaProducer(bootstrap_servers=['kafka-0:29092','kafka-1:29093','kafka-2:29094'],
            security_protocol="SSL",
            ssl_check_hostname=False,
            ssl_cafile="../kafka-cluster-ssl/pem/ca-root.pem",
            ssl_certfile="../kafka-cluster-ssl/pem/client-certificate.pem",
            ssl_keyfile="../kafka-cluster-ssl/pem/client-private-key.pem",
            value_serializer=lambda m: json.dumps(m).encode('ascii'),
)



# JSON data
data = {
    "time-collected": "2022-04-15T04:15:20.361Z",
    "resource-id": "e805d8a1-4dc8-4eae-b686-22975c9ac6b7",
    "ne-name": "baa_ne_1",
    "ne-ip-address": "192.168.0.1",
    "current-power": "500000",
    "energy-consumption": "125000",
    "onu-number": "10",
    "per-onu-energy-consumption": "890"
}

# Convert JSON data to a Python dictionary
data_dict = json.loads(json.dumps(data))
current_power =  int(data_dict["current-power"])

# Print the simulated power consumption data every minute
while True:
    updated_data = simulate_power_consumption(data_dict, current_power + current_power * random.randint(-2, 2)/100.0)
    print ("--------------------------Produce data:")
    print(json.dumps(updated_data, indent=4), flush=True)
    producer.send('PowerProd', updated_data)
    time.sleep(10)
