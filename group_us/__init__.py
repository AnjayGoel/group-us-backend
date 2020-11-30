from flask import Flask
app = Flask(__name__)

import group_us.views

@app.route("/")
def main():
    return "TODO"

if __name__ == "__main__":
    app.run() 
