import json
import os
import smtplib
from email.mime.text import MIMEText
from threading import Thread

import dotenv
import pika

dotenv.load_dotenv()

BASE_URL = "https://anjaygoel.github.io/GroupUs/#"


class EmailProducer:
    __instance = None

    @staticmethod
    def get_instance():
        if EmailProducer.__instance is None:
            EmailProducer()
        return EmailProducer.__instance

    def __init__(self):
        if EmailProducer.__instance is not None:
            raise Exception("This class is a singleton!", "SINGLETON_INIT")
        else:
            EmailProducer.__instance = self

        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USERNAME"),
            os.getenv("RABBITMQ_PASSWORD")
        )
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                credentials=credentials)
        )

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)

        self.queue_state = self.channel.queue_declare(
            queue='email_queue',
            durable=True,
            auto_delete=False
        )

    def produce(self, recipient, subject, body):
        message_dict = {"recipient": recipient, "subject": subject, "body": body}
        print(f"sent to queue message: {message_dict}")
        message_str = json.dumps(message_dict)
        self.channel.basic_publish(
            exchange='',
            routing_key='email_queue',
            body=message_str.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))


class EmailConsumer:
    max_count = 4
    current_count = 0

    def __del__(self):
        EmailConsumer.current_count -= 1

    def __init__(self):
        self.server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self.server_ssl.login(
            os.getenv("SRG_EMAIL"),
            os.getenv("SRG_PASSWORD")
        )

        self.credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USERNAME"),
            os.getenv("RABBITMQ_PASSWORD")
        )
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                credentials=self.credentials)
        )

        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=1)
        queue_state = self.channel.queue_declare(
            queue='email_queue',
            durable=True,
            auto_delete=False
        )
        EmailConsumer.current_count += 1

    def callback(self, ch, method, properties, body):
        message_dict = json.loads(body.decode())
        print(f"got queue message: {message_dict}")
        msg = MIMEText(message_dict["body"], 'html')
        msg["From"] = "GroupUs"
        msg["To"] = ", ".join(message_dict["recipient"] if isinstance(
            message_dict["recipient"], list) else [message_dict["recipient"]])
        msg["Subject"] = message_dict["subject"]
        try:
            self.server_ssl.sendmail(msg["From"], msg["To"], message_dict["body"])
            ch.basic_ack(method.delivery_tag)
        except smtplib.SMTPServerDisconnected:
            ch.basic_nack(method.delivery_tag, True)
            self.server_ssl.login(
                os.getenv("SRG_EMAIL"),
                os.getenv("SRG_PASSWORD")
            )

    def start(self):
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue="email_queue", on_message_callback=self.callback)
        self.channel.start_consuming()

    @staticmethod
    def start_all():
        def start():
            e_c = EmailConsumer()
            e_c.start()

        for i in range(EmailConsumer.max_count - EmailConsumer.current_count):
            Thread(target=start).start()


if __name__ == "__main__":
    EmailConsumer.start_all()
