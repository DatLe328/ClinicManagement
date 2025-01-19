from datetime import datetime

from flask import render_template, request
import dao, utils
from app import app, controllers
from app import admin
from flask_login import current_user

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/introduce")
def introduce():
    return render_template("introduce.html")


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/nurse")
def nurse_process():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template("nurse.html", current_date=current_date)

if __name__ == '__main__':
    app.run(debug=True)
