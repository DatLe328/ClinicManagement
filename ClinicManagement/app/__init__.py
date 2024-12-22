from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote
from flask_login import LoginManager
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

app = Flask(__name__)
app.secret_key = 'SECRETKEY'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/test?charset=utf8mb4" % quote('1234')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 6
app.config['CART_KEY'] = 'cart'

db = SQLAlchemy(app)
login = LoginManager(app)


# Configuration
cloudinary.config(
    cloud_name = "dokzvxp8m",
    api_key = "712437327494933",
    api_secret = "mAhCr1YQc_NUGDuGHOoQ1Ohrk1M",
    secure=True
)
