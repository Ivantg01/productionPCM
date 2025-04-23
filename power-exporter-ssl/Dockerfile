FROM python:3.10-alpine

RUN mkdir /code
WORKDIR /code
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY power_exporter_ssl.py ./

CMD ["python", "./power_exporter_ssl.py"]
