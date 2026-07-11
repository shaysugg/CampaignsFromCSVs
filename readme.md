This is a sample project designed to become more familiar with backend background tasks. It demonstrates scheduling campaigns, importing recipients from CSV files, and sending emails to each recipient when a campaign is started. It has:

* CRUD operations for campaigns
* Import recipients from CSV files into the database for campaigns. Handles large CSV files efficiently using Celery tasks
* Track the number of sent emails for each campaign to later mark it as complete
* Schedule Celery tasks for checking which campaigns need to be started and which ones are finished
* Containerized with Docker. Simply run docker compose up -d

**Tech Stack:**
* [PostgreSQL](https://www.postgresql.org/docs/) for the database
* [FastAPI](https://fastapi.tiangolo.com/) as the server
* [Celery](https://docs.celeryq.dev/en/stable/userguide/index.html) for background tasks
* [Redis](https://redis.io/docs/latest/develop/clients/redis-py/) for Celery task storage and campaign sent email count tracking
* [RabbitMQ](https://www.rabbitmq.com/tutorials/tutorial-four-python) for the Celery broker
