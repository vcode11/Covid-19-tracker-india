"""
:module:`models.py`
-------------------
This module contains Database Models defined using SQLAlchemy ORM.
It contains the tables:

+:class:`Cases`
"""
from dashboard import db

class Cases(db.Model):
    """
        Cases model
        :attr:
    """
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(128))
    total = db.Column(db.Integer, default=0)
    cured = db.Column(db.Integer, default=0)
    death = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime)

    def __repr__(self):
        return f"Date: {self.date} Region:{self.region} total:{self.total}"
