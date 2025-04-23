# Production PowerConsumptionMonitoring

This project is an example how to use Cloud and Virtualization technologies for system observability in a production environment

Integration of different tools to collect, process, store and display information regarding the power consumption of OLTs. An OLT is a Telecom network equipment used to deliver fiber to the home broadband services.

This repository is based on the PowerConsumptionMonitoring repository and adds security, data redundancy, load balancing and cloud mechanishms.

## Tools used:
![tools](https://skillicons.dev/icons?i=kafka,prometheus,grafana,docker,nginx) 
* Kafka+Zookeeper to send and receive power consumption metrics in JSON format  
* Prometheus to store the collected information as time series 
* Grafana to build and display multiple dashboard 
* Docker to run all components used
* Nignx as a load balancer
* SSL for Kafka producer and consumer clients
* HTTPS for Grafana access via internet

## Folder structure:
* ```kafka```: bus to send and consume power consumption metrics
  * ```docker-compose-kafka-kraft-sasl.yml```: YAML used by docker compose to create the kafka container.
  * ```kafka_server_jaas.conf```: Kafka configuration file for SASL credentials.
  * ```sasl_server.properties```: Main Kafka-Kraft configuration file with SASL.
 
* ```simulator```: metric generator
  * ```producer_sasl_energy.py```: Python program that emulates the generation of power consumption metrics from multiple elements.
  * ```example.json```: example of a power consumption metric in JSON format.

* ```prometheus```: docker definitions for Prometheus and Grafana
  * ```docker_compose.yml```: YAML used by docker compose to create Prometeus and Grafana containers.
  * ```prometheus.yml```: YAML used by Prometheus as its default configuration.

* ```exporter```: program to export metrics to Prometheus
  * ```power_exporter.py```: Python program to implement the specific Prometheus exporter to collect metric to Kafka and export them to Prometheus.
  * ```requirements.txt```: file with the Python libs used by power_exporter.py, basically Kafka and Prometheus client libs.
  * ```dockerfile```: file with the definition of the container for the Prometheus exporter used by Prometheus to collect metrics.
  * ```docker_compose.yml```: YAML used by docker to create the container of the Prometheus exporter.
   
## Grafana screenshots 
Grafana has been connected to Prometheus and different dashboards have been created: 

<img src="./screenshots/dashboard1.jpg" width="90%"></img>
<img src="./screenshots/dashboard3.jpg" width="45%"></img>
<img src="./screenshots/dashboard4.jpg" width="45%"></img>
<img src="./screenshots/dashboard2.jpg" width="45%"></img>
<img src="./screenshots/dashboard5.jpg" width="45%"></img>
<img src="./screenshots/dashboard6.jpg" width="45%"></img>
<img src="./screenshots/dashboard7.jpg" width="45%"></img>
