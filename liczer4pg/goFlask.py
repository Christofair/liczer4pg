from flask import Flask, jsonify, request, g
from flask_cors import CORS
import liczer4pg.dbmanager as dbmanager
import liczer4pg.models as models
import liczer4pg.utils as utils
import liczer4pg.validator as validator
import sqlalchemy as sa
from datetime import datetime
import requests;
import json
import logging

import liczer4pg.formatting_parsers as parsers

app = Flask('typerka_pg_api')
CORS(app, resources={r"*": {'origins':'*'}})
logger = logging.getLogger(__name__)


# TODO - Methods without @app.get etc. routing should be moved to another location.
def get_posts_cache():
    if 'posts_cache' not in g:
        g.posts_cache = dict()
    return g.posts_cache


def check_posts_in_cache(link):
    cache = get_posts_cache()
    if link in cache:
        return True
    return False


def get_posts(link):
    cache = get_posts_cache()
    if not check_posts_in_cache(link):
        response = requests.get(link)
        posts = utils.collect_posts_from_topic(response.content.decode('utf-8'))
        cache.update({link: posts})
    return cache[link]


def get_db():
    if 'db' not in g:
        g.db = dbmanager.DBManager()
    return g.db


@app.get('/')
def index():
    result = get_db().get_bets_typer_by_month(datetime(2022, 7, 1)).all()
    logger.info(result)
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
    raise NotImplementedError


@app.route('/api/v1/forum/pattern', methods=['POST'])
def send_pattern():
    # loads json from string (decoded data to utf-8) 
    # then get field value under "link" key
    data = json.loads(request.data.decode('utf-8'))
    if not validator.check_link(data['link']):
        return jsonify([])
    link = data['link'].split('#')[0]  # delete of anchor in link, cause it's unnecessary.
    posts = get_posts(link)
    events = models.EventParser.get_pattern_events(posts)
    return jsonify([event.as_dict() for event in events])


@app.route('/api/v1/counter/points', methods=['POST'])
def counting_points():
    try:
        data = json.loads(request.data.decode('utf-8'))
        # link to topic from, want to get posts of users
        if not validator.check_link(data['link']):
            return jsonify([])
        link = data['link']
        # get good events to checking with
        good_events = [models.Event.from_dict(event_d) for event_d in data['events']]
    except KeyError as e:
        logger.exception(e)
        raise e
    winner_type = good_events[0].winner is not None and good_events[0].winner != ""
    kind = 'scores' if not winner_type else 'winner'
    posts = get_posts(link)
    typers = []
    for post in posts:
        try:
            typer = models.Typer(utils.get_post_owner(post), post)
            if typer not in typers:
                typer.load_bet(good_events, winner_type)
                typers.append(typer)
        except Exception as e:
            logger.exception(e)
    results_data = []
    for i in range(len(typers)):
        results_data.append({
            'name': typers[i].name,
            'points': typers[i].bet.count_point(good_events, kind)
        })
    return jsonify(results_data)


@app.route('/api/v1/forum/convertion', methods=['POST'])
def rendered_pattern():
    try:
        data = json.loads(request.data.decode('utf-8'))
        matches = data['matches']
        format = data['format']
        dt = data.get('date')
    except KeyError as e:
        logger.exception(e)
        raise e
    # type {home, away, event_time: datetime}
    objects = []
    if format.lower() == 'sofascore' or format.lower() == 'standard':
        objects = parsers.parse_sofa_format(matches)
    elif format.lower() == 'flashscore':
        # XXX THIS CAN RAISE AN EXCEPTION. - when dt will be None.
        objects = parsers.parse_flash_format(matches, datetime.fromisoformat(dt))
    return jsonify(objects)
