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
    if not os.path.exists(dataDir):
            os.makedirs(dataDir)
    
    if not os.path.exists(path.join(dataDir,"complete","")):
            os.makedirs(path.join(dataDir,"complete",""))
    app.run() 
