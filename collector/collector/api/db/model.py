from collector.api.db import db


class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    node_aid = db.Column(db.String, nullable=False)
    external_id = db.Column(db.Integer, nullable=False)
    db.Index('node_aid', 'external_id', unique=True)
