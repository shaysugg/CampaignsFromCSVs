FROM python:3.14-slim
WORKDIR /app

COPY req.txt .
RUN pip install -r req.txt

EXPOSE 8000

COPY app ./app