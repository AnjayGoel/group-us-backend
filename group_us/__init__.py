import os.path
from os import path
from flask import Flask

app = Flask(__name__)
dataDir = path.join( path.expanduser('~'),"GroupUsData","")

import group_us.views


@app.route("/")
def main():
    return "TODO"

if __name__ == "__main__":
    if not os.path.exists("~/group_us_data/"):
            os.makedirs("~/group_us_data/")
    
    if not os.path.exists("~/group_us_data/complete"):
            os.makedirs("~/group_us_data/complete")
    app.run() 
