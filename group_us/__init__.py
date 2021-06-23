import logging

from dotenv import load_dotenv
from flask import Flask
from flask_mongoengine import MongoEngine

from group_us.email_utils import *

load_dotenv()

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGO_DB'),
    'host': f"mongodb+srv://{os.getenv('MONGO_USERNAME')}:{os.getenv('MONGO_PASSWORD')}"
            f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}?retryWrites=true&w=majority"
}

me = MongoEngine(app)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  # or whatever

EmailConsumer.start_all()

# handler = logging.FileHandler(path.join(dataDir,"log.log"), 'w', 'utf-8') # or whatever
# handler.setFormatter(logging.Formatter('%(name)s:%(asctime)s:%(message)s')) # or whatever
# logger.addHandler(handler)

import group_us.views


@app.route("/")
def main():
    return "TODO"


if __name__ == "__main__":
    EmailConsumer.start_all()
    app.run()
    logger.debug("Started")
