FROM python:3.8-slim
LABEL maintainer="Alexander Zorkin"

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/src

CMD [ "python3", "bot.py" ]
