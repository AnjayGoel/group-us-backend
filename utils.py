from email.mime.text import MIMEText
import smtplib
import time
import sys
import os


class EmailClient:
    def __init__(self):
        self.server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self.server_ssl.login(os.getenv("SRG_EMAIL"),
                              os.getenv("SRG_PASSWORD"))

    def send_email(self, recipient, subject, body):
        times = time.time()
        msg = MIMEText(body, 'html')
        msg["From"] = "GroupUs"
        msg["To"] = ", ".join(recipient if isinstance(
            recipient, list) else [recipient])
        msg["Subject"] = subject
        try:
            self.server_ssl.sendmail(msg["From"], msg["To"], msg.as_string())
            #print("successfully sent the mail")
        except:
            print("failed to send mail")
            e = sys.exc_info()[0]
            print(e)
        print(time.time()-times)

    def close(self):
        self.server_ssl.close()


BASE_URL = "http://127.0.0.1:3000/"
