"""
routes.py
-------------
This match_objectdule contains url routes for the flask app.
This match_objectdule also perform the data wrangling of Datframes from
https://mhfow.com

"""
import datetime
import re


from bs4 import BeautifulSoup
import requests
import pandas as pd
from flask import render_template, request


from dashboard import app, db, models


def rename(df: pd.DataFrame) -> pd.DataFrame:
    """
    This method renames df columns obtained from request to
        https://mhfow.gov.in/ This was required because number of foreign
        nationals is dynamic.
        :param df: Pandas DataFrame object from pd.read_html
        :return Pandas DataFrame object with renamed columns.

    """
    match_object = re.match(r".*(\d{2,}).*", df.columns[2])
    val = match_object.groups()[0]
    names = {
        "Name of State / UT": "state",
        "Total Confirmed cases (Including {} foreign Nationals)".format(val): "total",
        "Cured/Discharged/Migrated": "cured",
        "Death": "death",
    }
    df.rename(columns=names, inplace=True)
    return df


cache = {}


def func(s: str) -> datetime.date:
    """
    This function formats the data objects obtained from data frame.
        These strings are of the form dd/mm/yy which are converted to python
        datetime.date objects.
        :param s: String of the format dd/mm/yy
        :return datetime.date object of the dd/mm/yy.

    """
    if s in cache.keys():
        return cache[s]
    date = list(map(int, s.split("/")))
    cache[s] = datetime.date(2000 + date[2], date[1], date[0])
    return cache[s]


def insert_older_data() -> None:
    """
    This function reads the data from kaggle dataset about covid-19
        cases in India and inserts the older data to the database for analytics.

    """
    df = pd.read_csv("covid_19_india.csv")
    df = df[["Date", "State/UnionTerritory", "Cured", "Deaths", "Confirmed"]]
    df.rename(columns={"State/UnionTerritory": "State"}, inplace=True)
    df["Date"] = df["Date"].apply(func)
    for row in df.itertuples(index=False):
        case = models.Cases(
            region=row.State,
            death=row.Deaths,
            cured=row.Cured,
            total=row.Confirmed,
            date=row.Date,
        )
        db.session.add(case)
    df = df.groupby(["Date"]).sum()
    for row in df.itertuples():
        case = models.Cases(
            region="India",
            death=row.Deaths,
            cured=row.Cured,
            total=row.Confirmed,
            date=row.Index,
        )
        db.session.add(case)
    db.session.commit()
    cache.clear()


def update_db(df : pd.DataFrame, active : int, deaths :int, cured : int) -> None:
    """
    This function updates the number of corona virus cases as per the latest data
        recieved from the MFHOW website's table.
        :param: df Pandas.DataFrame object containing the data of html table
        :param: active: int Active number of cases as show in the top block.
        :param: deaths: int Number of deaths as shown in the top block.
        :param: cured:int  Number of cured as shownn in the top block.
    
    """
    today = datetime.date.today()
    # deleting the older cases
    today_cases = models.Cases.query.filter_by(date=today)
    for case in today_cases:
        db.session.delete(case)
        db.commit()
    # updating the stats
    case = models.Cases(
        region="India",
        total=active + deaths + cured,
        death=deaths,
        cured=cured,
        date=today,
    )
    db.session.add(case)
    states = df.index
    total = df["total"]
    cure = df["cured"]
    deaths = df["death"]
    for region, total_cases, cured, death in zip(states, total, cure, deaths):
        case = models.Cases(
            region=region, total=total_cases, death=death, cured=cured, date=today,
        )
        db.session.add(case)
        db.session.commit()


def get_data(df: pd.DataFrame, state: str):
    """
    This function fetches data from database for a specific region and from
        the DataFrame and constructs the required context dictionary.
        :param df: Pandas DataFrame for reading html table.
        :param state: str Region for which data should be looked up.
        :return data_dict : Context Dictionary contaning change data and 
        current data.
    
    """
    data_dict = {}
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    try:
        data_dict["cured"] = int(df.loc[state][2])
    except KeyError:
        state = "India"
        data_dict["cured"] = int(df.loc[state][2])
    data_dict["death"] = int(df.loc[state][3])
    data_dict["region"] = state
    data_dict["active"] = int(df.loc[state][1]) - data_dict["cured"] - data_dict["death"]
    case = models.Cases.query.filter_by(
        date=datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0),
        region=state,
    ).first()
    if case != None:
        data_dict["change"] = {
            "active": data_dict["active"] - case.total + case.death + case.cured,
            "cured": data_dict["cured"] - case.cured,
            "death": data_dict["death"] - case.death,
        }
    else:
        data_dict["change"] = {}
    return data_dict


@app.before_first_request
def create_tables() -> None:
    """
    Function to intitalize database.
    
    """
    db.create_all()
    insert_older_data()


@app.route("/", methods=["GET", "POST"])
def index():
    """
    / endpoint for flask app.
    Accepts GET request from form for fetching data of a particular region.
    
    """
    r = requests.get("https://www.mohfw.gov.in/")
    soup = BeautifulSoup(r.text, features="html.parser")
    li = soup.select(".site-stats-count > ul > li > strong")
    active = li[0].text
    cured = li[1].text
    deaths = li[2].text
    table = soup.select(".data-table")[0]
    df = pd.read_html(str(table))[0]
    rename(df)
    df = df.iloc[:30]
    df["total"] = df["total"].apply(lambda x: int(x))
    df["cured"] = df["cured"].apply(lambda x: int(x))
    df["death"] = df["death"].apply(lambda x: int(x))
    update_db(df, int(active), int(deaths), int(cured))
    india_ = {
        "state": "India",
        "total": df["total"].sum(),
        "cured": df["cured"].sum(),
        "death": df["death"].sum(),
    }
    df2 = pd.DataFrame(india_, index=["India"])
    df = df.append(df2)
    df.set_index("state", inplace=True)
    data = get_data(df, request.args.get("region", "India"))
    return render_template("index.html", data=data, states=list(df.index)[:-1])
