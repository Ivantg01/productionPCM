FROM python:3.10-alpine

RUN mkdir /code
WORKDIR /code
COPY requirements.txt ./
COPY sites.csv ./
RUN pip install --no-cache-dir -r requirements.txt
COPY producer_energy_ssl.py ./

CMD ["python", "./producer_energy_ssl.py"]
