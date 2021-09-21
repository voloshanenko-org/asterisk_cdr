from sqlalchemy.inspection import inspect
from app import db, login
from flask_login import UserMixin
from sqlalchemy import exc


class BaseModel(db.Model):
    __abstract__ = True

    def serialize_me(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize_me() for m in l]

    def serialize(self):
        return self.serialize_me(self)

    def __getitem__(self, key):
        return getattr(self, key)


class User(UserMixin, BaseModel):
    __bind_key__ = "users"
    __tablename__ = "userman_users"
    id = db.Column("default_extension", db.String(45), index=True, unique=True, primary_key=True)
    password = db.Column(db.String(255), index=True, unique=True)


@login.user_loader
def load_user(id):
    try:
        return User.query.get(int(id))
    except exc.OperationalError as e:
        return None


class CelLog(BaseModel):
    __tablename__ = "cel"
    id = db.Column(db.Integer, primary_key=True)
    eventtype = db.Column(db.String(80))
    eventtime = db.Column(db.DateTime, index=True)
    cid_name = db.Column(db.String(80))
    cid_num = db.Column(db.String(80))
    cid_ani = db.Column(db.String(80))
    cid_rdnis = db.Column(db.String(80))
    cid_dnid = db.Column(db.String(80))
    exten = db.Column(db.String(80))
    context = db.Column(db.String(80), index=True)
    channame = db.Column(db.String(80))
    appname = db.Column(db.String(80))
    appdata = db.Column(db.String(80))
    amaflags = db.Column(db.Integer)
    accountcode = db.Column(db.String(20))
    uniqueid = db.Column(db.String(32), index=True)
    linkedid = db.Column(db.String(32))
    peer = db.Column(db.String(80))
    userdeftype = db.Column(db.String(255))
    extra = db.Column(db.String(512))