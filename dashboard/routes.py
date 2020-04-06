import requests
import datetime
import re

from bs4 import BeautifulSoup

import pandas as pd

from flask import render_template

from dashboard import app, db, models
def rename(df):
    mo = re.match(r'.*(\d{2,}).*',df.columns[2])
    val = mo.groups()[0]
    names = {
            'Name of State / UT': 'state',
            'Total Confirmed cases (Including {} foreign Nationals)'.format(val):'total',
            'Cured/Discharged/Migrated':'cured',
            'Death':'death',
        }
    df.rename(columns=names,inplace=True)
    return df

cache = {}
def func(s):
    if s in cache.keys():
        return cache[s]
    l = list(map(int,s.split('/')))
    cache[s] = datetime.date(2000+l[2],l[1],l[0])
    return cache[s]
def insert_older_data():
    df = pd.read_csv('covid_19_india.csv')
    df = df[['Date','State/UnionTerritory', 'Cured','Deaths','Confirmed']]
    df.rename(columns={'State/UnionTerritory':'State'},inplace=True)
    df['Date'] = df['Date'].apply(func)
    for row in df.itertuples(index=False):
        case = models.Cases(region=row.State,
                            death=row.Deaths,
                            cured=row.Cured,
                            total=row.Confirmed,
                            date=row.Date,
                            )
        db.session.add(case)
    df = df.groupby(['Date']).sum()
    for row in df.itertuples():
        case = models.Cases(region="India",
                            death=row.Deaths,
                            cured=row.Cured,
                            total=row.Confirmed,
                            date=row.Index,
                            )
        db.session.add(case)
    db.session.commit()
    cache.clear()

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
    case = models.Cases.query.filter_by(date=datetime.datetime(yesterday.year,yesterday.month,yesterday.day,0,0), region=state).first()
    d['cured'] = int(df.loc[state][2])
    d['death'] = int(df.loc[state][3])
    d['region'] = state
    d['active'] = int(df.loc[state][1])-d['cured']-d['death']

    if case != None:
        d['24'] = {
                'active':d['active']-case.total + case.death + case.cured,
                'cured':d['cured'] -case.cured,
                'deaths':d['death'] - case.death,
            }
    return d

@app.before_first_request
def create_tables():
    db.create_all()
    print('DB created.')
    insert_older_data()

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
    rename(df)
    df = df.iloc[:30]
    df['total'] = df['total'].apply(lambda x: int(x))
    df['cured'] = df['cured'].apply(lambda x: int(x))
    df['death'] = df['death'].apply(lambda x: int(x))
    india_ = {
                'state':'India',
                'total':df['total'].sum(),
                'cured':df['cured'].sum(),
                'death':df['death'].sum(),
            }
    df2 = pd.DataFrame(india_,index=['India'])
    df = df.append(df2)
    df.set_index('state', inplace=True)
    print(df.head())
    print(get_data(df, 'India'))
    check(df,int(active),int(deaths),int(cured))
    data = []
    
    return render_template("index.html", cured=cured,\
            active=active,deaths=deaths)
