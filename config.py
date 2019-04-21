import os

class Config(object):

    SEND_FILE_MAX_AGE_DEFAULT = 0
    DB_HOST = os.environ.get('DB_HOST') or '127.0.0.1'
    DB_NAME = os.environ.get('DB_NAME') or 'asteriskcdrdb'
    DB_USERNAME = os.environ.get('DB_USERNAME') or "root"
    DB_PASSWORD = os.environ.get('DB_PASSWORD')

    SQLALCHEMY_DATABASE_URI = "mysql://{0}:{1}@{2}/{3}".format(DB_USERNAME, DB_PASSWORD, DB_HOST, DB_NAME)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 600
    SQLALCHEMY_POOL_TIMEOUT = 120
