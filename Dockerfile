FROM python:3.11-slim-bullseye
WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD python3 main.py