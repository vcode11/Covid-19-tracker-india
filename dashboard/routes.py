import requests
import datetime

from bs4 import BeautifulSoup

import pandas as pd

from flask import render_template

from dashboard import app, db, models
names = {
        'Name of State / UT': 'state',
        'Total Confirmed cases (Including 65 foreign Nationals)':'total',
        'Cured/Discharged/Migrated':'cured',
        'Death':'death',
    }
def update_db(df, active, deaths, cured):
    case = models.Cases(region='India',
                        total=active+deaths+cured,
                        death=deaths,
                        cured=cured,
                        date=datetime.date.today(),
            )
    db.session.add(case)
    states = df.index
    total = df['total']
    cure = df['cured']
    deaths = df["death"]
    for region, total_cases, cured, death in zip(states,total,cure, deaths):
        case = models.Cases(region=region,
                            total=total_cases,
                            death=death,
                            cured=cured,
                            date = datetime.date.today(),
                            )
        db.session.add(case)
        db.session.commit()
    with open("last_updated.txt","w") as f:
        f.write(str(datetime.date.today()))
    
def check(*args, **kwargs):
    with open('last_updated.txt') as f:
        date = f.read().strip()
        date = date.split('-')
        date = datetime.date(int(date[0]), int(date[1]), int(date[2]))
        if datetime.date.today()-date >= datetime.timedelta(days=1):
            update_db(*args, **kwargs)
def get_data(df, state):
    d = {}
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    case = models.Cases.query.filter_by(date=yesterday, region=state).first()
    d['cured'] = int(df.loc[state][2])
    d['death'] = int(df.loc[state][3])
    d['region'] = state
    d['active'] = int(df.loc[state][1])-d['cured']-d['death']

    if case is not None:
        d['24'] = {
                'active':d['active']-case.total + case.deaths + case.cured,
                'cured':d['cured'] -case.cured,
                'deaths':d['death'] - case.death,
            }
    return d

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
    df.rename(columns=names, inplace=True)
    df.set_index('state', inplace=True)
    print(df.head())
    print(get_data(df, 'Bihar'))
    check(df,int(active),int(deaths),int(cured))
    data = []
    
    return render_template("index.html", cured=cured,\
            active=active,deaths=deaths)
