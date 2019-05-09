from os import environ
from random import SystemRandom
from string import ascii_uppercase, digits
from datetime import timedelta

class Config(object):

    rnd_secret_key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(50))

    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = environ.get('PERMANENT_SESSION_LIFETIME') or timedelta(hours=8)
    SESSION_PERMANENT = True

    if "FLASK_DEBUG" in environ:
        SECRET_KEY = "DEBUG_SECRET_KEY"
    else:
        SECRET_KEY = environ.get('SECRET_KEY') or rnd_secret_key


    DB_HOST = environ.get('DB_HOST') or '127.0.0.1'
    DB_NAME_CDR = environ.get('DB_NAME_CDR') or 'asteriskcdrdb'
    DB_NAME_USERS = environ.get('DB_NAME_USERS') or 'asterisk'
    DB_USERNAME = environ.get('DB_USERNAME') or "root"
    DB_PASSWORD = environ.get('DB_PASSWORD')

    ASTERISK_HOST = environ.get('ASTERISK_HOST') or None
    ASTERISK_AMI_USERNAME = environ.get('ASTERISK_AMI_USERNAME') or None
    ASTERISK_AMI_PASSWORD = environ.get('ASTERISK_AMI_PASSWORD') or None

    FLASK_DEBUG = environ.get('FLASK_DEBUG') or "0"

    SQLALCHEMY_DATABASE_URI = "mysql://{0}:{1}@{2}/{3}".format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME_CDR)
    SQLALCHEMY_BINDS = {
        "users":    "mysql://{0}:{1}@{2}/{3}".format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME_USERS)
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 600
    SQLALCHEMY_POOL_TIMEOUT = 120