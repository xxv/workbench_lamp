from python:3

MAINTAINER steve@staticfree.info

COPY . /app
WORKDIR /app

RUN pip install pipenv

RUN pipenv install --system --deploy

CMD ["python", "redshift.py", "mqtt_config.json"]
