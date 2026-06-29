first make sure celery workers are running
`celery -A tasks worker -l INFO`
then run celery beat
`celery -A tasks beat -l Info`


celery setup
make user in rabbitmq
```shell
sudo rabbitmqctl add_user myuser mypassword

sudo rabbitmqctl add_vhost myvhost

sudo rabbitmqctl set_user_tags myuser mytag

sudo rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
```
setup
```python
c = Celery(
    "tasks",
    broker="amqp://shay:123@localhost:5672/myvhost",
    backend="redis://localhost:6379/0",
)
```