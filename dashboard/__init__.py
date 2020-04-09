"""
COVID-19 Dashboard For India
=================================
This project tracks COVID-19 cases count in India on daily basis.
This data has been obtain from site `Ministry of Health and Family 
Welfare <https://www.mohfw.gov.in/>`_

Project Modules:
-------------------
:module:`dashboard.py` runs the flask server
:module:`models.py` contains the model :class:`dashboard.models.Cases`
:module:`routes.py` contains :func:`dashboard.routesindex` route
and other request and manipulation functions.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

from dashboard import routes, models
