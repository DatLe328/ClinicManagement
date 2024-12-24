from flask import render_template, request
import dao, utils
from app import app, controllers
from app import admin

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/doctor")
def doctor():
    kw = request.args.get('kw')
    info = dao.load_users_by_user_id(kw)
    patients = dao.load_users()

    return render_template("doctor.html", patients=patients, search_result=info)


@app.route("/introduce")
def introduce():
    return render_template("introduce.html")


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/nurse")
def nurse():
    return render_template("nurse.html")


@app.context_processor
def load_medicines():
    medicines = dao.load_medicines()
    return {
        'medicines': medicines
    }


@app.context_processor
def load_phieu_kham():
    phieu_kham = dao.get_prescriptions_for_today()
    return {
        'phieu_kham': phieu_kham
    }


if __name__ == '__main__':
    app.run(debug=True)
