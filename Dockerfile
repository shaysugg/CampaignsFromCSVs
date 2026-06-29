FROM python:3.14
WORKDIR /app

COPY req.txt .
RUN pip install -r req.txt

EXPOSE 8000

COPY app ./app