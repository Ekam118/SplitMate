import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = ("sqlite:///" + os.path.join(BASE_DIR, "instance", "splitmate.db"))

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Profile Image Upload

    UPLOAD_PROFILE = os.path.join( BASE_DIR, "static", "profile_images" )

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024


    # Gmail Configuration

    MAIL_SERVER = os.getenv("MAIL_SERVER")

    MAIL_PORT = os.getenv("MAIL_PORT ")

    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS") == "True"

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")

    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")
