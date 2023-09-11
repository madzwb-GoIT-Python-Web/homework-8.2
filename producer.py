import configparser
import json
import os
import pika
import sys
import time

from datetime import datetime
from pika.exceptions import StreamLostError

import connection
import models
import seed

def process_contacts(channel):
    count = 0
    for contact in models.Contact.objects(processed = None):
        message = models.Message(
                    contact_id = str(contact.id),
                    message = "Hello! Dear, " + contact.name + '!'
        )
        # message = contact.to_json()
        dump = message.model_dump()
        data = json.dumps(dump)
        body = data.encode()
        methods =   [
                        m for m in contact.methods  \
                        if      m.result    is None \
                            and m.processed is None
                    ]
        if methods:
            queue = methods[0]._cls.lower()
            channel.basic_publish(
                exchange="",
                routing_key = queue,
                body = body,
                properties = pika.BasicProperties(
                    delivery_mode = pika.DeliveryMode.Persistent
                ),
            )
            print(f"[{datetime.now()}] Published message:'{data}' to queue:'{queue}'.", flush = True)
            count += 1
    print(f"[{datetime.now()}] {count} message(s) published.", flush = True)
    return count

def main():

    config = configparser.ConfigParser()
    config.read("data/config.ini")

    rabbitmq_host = config.get("RABBITMQ", "host")
    rabbitmq_port = config.get("RABBITMQ", "port")
    rabbitmq_user = config.get("RABBITMQ", "user")
    rabbitmq_password = config.get("RABBITMQ", "user")
    queue_durable = config.get("RABBITMQ", "durable")
    queue_ttl = config.get("RABBITMQ", "x-message-ttl")

    taks_timeout = int(config.get("TASKS", "timeout"))

    queues = json.loads(config.get("RABBITMQ", "queues"))

    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            port=int(rabbitmq_port),
            credentials=credentials
        )
    )
    channel = connection.channel()
    
    for name, function in queues.items():
        channel.queue_declare(
            queue = name.lower(),
            durable = bool(queue_durable),
            arguments = {"x-message-ttl": int(queue_ttl)}
        )
    total_published = 0
    # count = process_contacts(channel)
    published = 1
    count = 0
    while published or (count := process_contacts(channel)):
        published = 0
        total_published += count
        count = 0
        print(f"[{datetime.now()}] Status of queues:", flush = True)
        for name, function in queues.items():
            try:
                status = channel.queue_declare(
                    queue = name.lower(),
                    passive= True,
                )
                print(f"[{datetime.now()}]\tTo queue:'{name.lower()}' published {status.method.message_count} message(s).", flush = True)
                published += status.method.message_count
            except StreamLostError:
                main()
                return
        if published or count:
            # published += status.method.message_count
            seconds = min(int(queue_ttl) / 1000, (taks_timeout * 2) * max(published, count))
            print(f"[{datetime.now()}] Going to sleep for {seconds} second(s).", flush = True)
            time.sleep(seconds)
        # elif (count := process_contacts(channel)):
        #     total_published += count
        #     continue
        # else:
        #     break
    print(f"[{datetime.now()}] Total messages processed - {total_published}.",flush = True)
    connection.close()
    

if __name__ == "__main__":
    seed.seed()
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)