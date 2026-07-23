import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = "splitmate_secret_key"

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" +
        os.path.join(BASE_DIR, "instance", "splitmate.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # Profile Image Upload

    UPLOAD_PROFILE = os.path.join( BASE_DIR, "static", "profile_images")


    MAX_CONTENT_LENGTH = 2 * 1024 * 1024   # 2 MB


    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = ""









# import os

# BASE_DIR = os.path.abspath(os.path.dirname(__file__))


# class Config:
#     SECRET_KEY = "splitmate_secret_key"

#     SQLALCHEMY_DATABASE_URI = ("sqlite:///" + os.path.join(BASE_DIR, "instance", "splitmate.db"))

#     SQLALCHEMY_TRACK_MODIFICATIONS = False

#     MAIL_SERVER = "smtp.gmail.com"
#     MAIL_PORT = 587
#     MAIL_USE_TLS = True
#     MAIL_USERNAME = ""
#     MAIL_PASSWORD = ""
#     MAIL_DEFAULT_SENDER = ""