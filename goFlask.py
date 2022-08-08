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

def get_posts_cache():
    if 'posts_cache' not in g:
        g.posts_cache = dict()
    return dict()

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
    raise NotImplemented

@app.route('/api/v1/forum/pattern', methods=['POST'])
def send_pattern():
    # loads json from string (decoded data to utf-8) 
    # then get field value under "link" key
    link = json.loads(request.data.decode('utf-8'))['link']
    # do request to that link
    # TODO: validate string for forum domain.
    response = requests.get(link)
    posts = utils.collect_posts_from_topic(response.content.decode('utf-8'))
    # cache this link with posts
    # TODO: Validate link to not contain a "#comment" string.
    cache = get_posts_cache()
    cache.update({link: posts})
    events = models.EventParser.get_pattern_events(posts)
    return jsonify([event.as_dict() for event in events])

@app.route('/api/v1/counter/points', methods=['POST'])
def counting_points():
    try:
        data = json.loads(request.data.decode('utf-8'))
        # link to topic from, want to get posts of users
        link = data['link']
        # get good events to checking with
        good_events = [models.Event.from_dict(event_d) for event_d in data['events']]
    except KeyError as e:
        print(e)
        raise e;
    # winner_type = good_events[0].winner is not None and good_events[0].winner != ""
    winner_type = False
    kind = 'scores' if not winner_type else 'winner'
    posts = None
    cache = get_posts_cache()
    if link in cache:
        posts = cache[link]
    else:
        topic_response = requests.get(link)
        posts = utils.collect_posts_from_topic(topic_response.content.decode('utf-8'))
    typers = []
    for post in posts:
        try:
            typer = models.Typer(utils.get_post_owner(post), post)
            typer.load_bet(good_events, winner_type)
            typers.append(typer)
        except Exception as e:
            print(e)
    results_data = {}
    for i in range(len(typers)):
        results_data.update({typers[i].name: typers[i].bet.count_point(good_events, kind)})
    return jsonify(results_data)
