FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && apt-get install -y  && rm -rf /var/lib/apt/lists/*

COPY . /app

CMD ["python", "app/bot.py"]