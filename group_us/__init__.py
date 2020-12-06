from math import log
import os.path
from os import path
from flask import Flask
import logging
app = Flask(__name__)

dataDir = path.join( path.expanduser('~'),"GroupUsData","")
logger= logging.getLogger()
logger.setLevel(logging.DEBUG) # or whatever
handler = logging.FileHandler(path.join(dataDir,"log.log"), 'w', 'utf-8') # or whatever
handler.setFormatter(logging.Formatter('%(name)s %(message)s')) # or whatever
logger.addHandler(handler)

import group_us.views

@app.route("/")
def main():
    return "TODO"

if __name__ == "__main__":
    if not os.path.exists(dataDir):
            os.makedirs(dataDir)
    
    if not os.path.exists(path.join(dataDir,"complete","")):
            os.makedirs(path.join(dataDir,"complete",""))
    app.run() 
    logger.debug("Started")
