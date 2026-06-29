import os

rabbitmq_port = os.getenv("RABBITMQ_PORT")
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_user = os.getenv("RABBITMQ_USERNAME")
rabbitmq_pass = os.getenv("RABBITMQ_PASSWORD")
rabbitmq_vhost = os.getenv("RABBITMQ_VHOST")

redis_url = os.getenv("REDIS_URL")
redis_port = os.getenv("REDIS_PORT")
redis_db = os.getenv("REDIS_DB")

# broker_url = f"amqp://{rabbitmq_user}:{rabbitmq_pass}@{rabbitmq_host}:{rabbitmq_port}/{rabbitmq_vhost}"
broker_url = f"redis://{redis_url}:{redis_port}/{redis_db}"
result_backend = f"redis://{redis_url}:{redis_port}/{redis_db}"
accept_content = ["json"]
task_serializer = "json"
result_serializer = "json"
timezone = "UTC"
enable_utc = True
task_track_started = True
task_time_limit = 30 * 60
