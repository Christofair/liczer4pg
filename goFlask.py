from flask import Flask, jsonify, request, g
from flask_cors import CORS
import dbmanager
import models
import utils
import sqlalchemy as sa
from datetime import datetime
import requests;
import json

app = Flask('typerka_pg_api')
CORS(app)

def get_db():
    if 'db' not in g:
        g.db = dbmanager.DBManager()
    return g.db

@app.get('/')
def index():
    result = get_db().get_bets_typer_by_month(datetime(2022, 7, 1)).all()
    print(result)
    return jsonify(result)


@app.route('/api/v1/top/month/<int:month>/<int:year>', methods=['GET', 'POST'])
def top_month(month, year):
    """Generate json which contain top 10 typers from specified month and year
    otherwise generate another count number of typers which is specified in POST data"""
    how_many_typers = 10
    if request.method == "POST":
        how_many_typers = int(request.form["HOW_MANY_TYPERS"])
    with get_db().session() as session:
        typers = session.execute(sa.select(models.Typer, models.Bet)
                                 .join(models.Bet).join(models.Event)
                                 # .(sum(models.Event.points))
                                 .group_by(models.Typer.name)
                                 .where(models.Event.start_time < datetime(year, month+1, 1)))
                                 #        and models.Event.start_time >= datetime(year, month, 1))
                                 # .limit(how_many_typers)).all()
        top = [{'name':typer[0].name, 'points':typer[0].count_point()} for typer in typers]

    return jsonify(top)

@app.route('/api/top/dw')
def top_dw():
    """Generate json which contain top 5"""
    raise NotImplemented()

@app.route('/api/v1/forum/pattern', methods=['POST'])
def send_pattern():
    # loads json from string (decoded data to utf-8) 
    # then get field value under "link" key
    link = json.loads(request.data.decode('utf-8'))['link']
    # do request to that link
    # TODO: validate string for forum domain.
    response = requests.get(link)
    posts = utils.collect_posts_from_topic(response.content.decode('utf-8'))
    events = models.EventParser.get_pattern_events(posts)
    return jsonify([event.as_dict() for event in events])
