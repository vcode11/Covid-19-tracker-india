import requests
from bs4 import BeautifulSoup

import pandas as pd

from flask import render_template

from dashboard import app, db, models

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    r = requests.get('https://www.mohfw.gov.in/')
    soup = BeautifulSoup(r.text, features="html.parser")
    li = soup.select('.site-stats-count > ul > li > strong')
    active = li[0].text
    cured = li[1].text
    deaths = li[2].text
    table = soup.select('.data-table')[0]
    df = pd.read_html(str(table))[0]
    print(df.head())
    return render_template("index.html", cured=cured,\
            active=active,deaths=deaths)
