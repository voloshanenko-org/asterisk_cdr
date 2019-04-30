from sqlalchemy.inspection import inspect
from app import db, login
from flask_login import UserMixin

class BaseModel(db.Model):
    __abstract__ = True

    def serialize_me(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize_me() for m in l]

    def serialize(self):
        d = self.serialize_me(self)
        return d

    def __getitem__(self, key):
        return getattr(self, key)

class User(UserMixin, BaseModel):
    __bind_key__ = "users"
    __tablename__ = "sip"
    id = db.Column(db.String(20), index=True, unique=True, primary_key=True)
    keyword = db.Column(db.String(30), index=True, unique=True)
    data = db.Column(db.String(255))


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class CallsLog(BaseModel):
    __tablename__ = "cdr"
    calldate = db.Column(db.DateTime, index=True)
    clid = db.Column(db.String(80))
    src = db.Column(db.String(80))
    dst = db.Column(db.String(80), index=True)
    dcontext = db.Column(db.String(80))
    channel = db.Column(db.String(80))
    dstchannel = db.Column(db.String(80))
    lastapp = db.Column(db.String(80))
    lastdata = db.Column(db.String(80))
    duration = db.Column(db.Integer)
    billsec = db.Column(db.Integer)
    disposition = db.Column(db.String(45))
    amaflags = db.Column(db.Integer)
    accountcode = db.Column(db.String(20), index=True)
    uniqueid = db.Column(db.String(32), index=True)
    userfield = db.Column(db.String(255))
    did = db.Column(db.String(50), index=True)
    recordingfile = db.Column(db.String(255), index=True)
    cnum = db.Column(db.String(40))
    cnam = db.Column(db.String(40))
    outbound_cnum = db.Column(db.String(40))
    outbound_cnam = db.Column(db.String(40))
    dst_cnam = db.Column(db.String(40))
    linkedid = db.Column(db.String(32))
    peeraccount = db.Column(db.String(80))
    sequence = db.Column(db.Integer, primary_key=True)


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

