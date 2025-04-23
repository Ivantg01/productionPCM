#!/usr/bin/env bash

set -eu

CN="/C=ES/ST=Madrid/L=Madrid/O=IvanTorrijos/CN=grafana"
VALIDITY_IN_DAYS=3650
CA_WORKING_DIRECTORY="certificate-authority"
CA_KEY_FILE="grafana.key"
CA_CERT_FILE="grafana.crt"

rm -rf $CA_WORKING_DIRECTORY && mkdir $CA_WORKING_DIRECTORY

openssl req -new -x509 -newkey rsa:2048 -days $VALIDITY_IN_DAYS -subj $CN \
     -keyout $CA_WORKING_DIRECTORY/$CA_KEY_FILE  -out $CA_WORKING_DIRECTORY/$CA_CERT_FILE -nodes

#cambiamos el propietario al usuario grafana con el que funciona dentro del contenedor para que pueda leerlo
chown 472 $CA_WORKING_DIRECTORY/$CA_KEY_FILE $CA_WORKING_DIRECTORY/$CA_CERT_FILE

