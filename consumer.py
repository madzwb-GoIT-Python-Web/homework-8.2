import configparser
# import datetime
# import faker
import os
import json
import pika
import random
import sys
import time

import connection
import models

from datetime import datetime
from multiprocessing import Pool


TASK_TIMEOUT = 0

config = configparser.ConfigParser()
config.read("data/config.ini")

def send_sms(mobile, message):
    time.sleep(random.randint(0, TASK_TIMEOUT))
    result = random.choice([True, False])
    return result

def send_email(email, message):
    time.sleep(random.randint(0, TASK_TIMEOUT))
    result = random.choice([True, False])
    return result

def send_voice(phone, message):
    time.sleep(random.randint(0, TASK_TIMEOUT))
    result = random.choice([True, False])
    return result

def main(name: str = "Email", function = send_email):
    if isinstance(function, str):
        funcation = eval(function)
    rabbitmq_host = config.get("RABBITMQ", "host")
    rabbitmq_port = config.get("RABBITMQ", "port")
    rabbitmq_user = config.get("RABBITMQ", "user")
    rabbitmq_password = config.get("RABBITMQ", "user")
    queue_durable = config.get("RABBITMQ", "durable")
    queue_ttl = config.get("RABBITMQ", "x-message-ttl")
    prefetch_count = config.get("RABBITMQ", "prefetch_count")

    global TASK_TIMEOUT
    TASK_TIMEOUT = int(config.get("TASKS", "timeout"))

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=int(rabbitmq_port),
            credentials=credentials
        )
    )
    channel = connection.channel()
    
    channel.queue_declare(
        queue = name.lower(),
        durable = bool(queue_durable),
        arguments = {"x-message-ttl": int(queue_ttl)}
    )
    channel.basic_qos(prefetch_count = int(prefetch_count))

    def callback(channel, method, properties, body):
        data = json.loads(body.decode())
        message = models.Message(**data)
        print(f"[{datetime.now()}] Queue: '{name.lower()}'. Received {message}")
        contact = models.Contact.objects(pk = message.contact_id, processed = None).first()
        if contact:
            result = False
            methods =   [
                            m for m in contact.methods  \
                            if      m._cls == name      \
                                and m.result    is None \
                                and m.processed is None
                        ]
            db_method = None
            for _method in methods:
                tries = 0
                db_method = _method
                while tries < 3:
                    print(f"[{datetime.now()}] Queue: '{name.lower()}' .Sending message:'{message}' to {_method.value}...")
                    result = function(_method.value, message.message)
                    info = f"[{datetime.now()}] Queue: '{name.lower()}' .Sending message:'{message}' to {_method.value}..."
                    info += "done." if result else "fail."
                    print(info)
                    if result:
                        break
                    tries += 1
            else:
                processed = datetime.now()
                if db_method is not None:
                    if result:
                        contact.processed = processed
                        contact.result = result
                    db_method.processed = processed
                    db_method.result = result
                if not result:
                    methods =   [
                                    m for m in contact.methods  \
                                    if      m.result    is None \
                                        and m.processed is None
                                ]
                    if not methods:
                        contact.processed = processed
                        contact.result = result
                contact.save()
        channel.basic_ack(delivery_tag = method.delivery_tag)

    channel.basic_consume(queue = name.lower(), on_message_callback=callback)#, auto_ack=True

    print(f"[{datetime.now()}] Queue: '{name.lower()}'. Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    queues = json.loads(config.get("RABBITMQ", "queues"))
    if len(queues) > 1:
        with Pool(len(queues)) as pool:
            pool.map(main, queues)
    else:
        try:
            if queues:
                for name, function in queues.items():
                    main(name, eval(function))
            else:
                main()
        except KeyboardInterrupt:
            print("Interrupted")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)