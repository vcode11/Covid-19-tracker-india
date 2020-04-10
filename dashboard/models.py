"""
:py:mod:`models.py`
-------------------
This module contains Database Models defined using SQLAlchemy ORM.
It contains the tables:

+ :class:`Cases`

"""
from dashboard import db

class Cases(db.Model):
    """
        Cases model
        :attr:
    """
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(128)) #type : str
    total = db.Column(db.Integer, default=0) #type : int
    cured = db.Column(db.Integer, default=0) #type: int
    death = db.Column(db.Integer, default=0) #type: int
    date = db.Column(db.DateTime) #type: datetime.datetime

    def __repr__(self) -> str:
        return f"Date: {self.date} Region:{self.region} total:{self.total}"
