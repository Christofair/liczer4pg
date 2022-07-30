from flask import Flask, jsonify, request, g
from flask_cors import CORS
import dbmanager
import models
import utils
import sqlalchemy as sa
from datetime import datetime

app = Flask('typerka_pg_api')
CORS(app)

def get_db():
    if 'db' not in g:
        g.db = dbmanager.DBManager()
    return g.db

@app.get('/')
def index():
    with get_db().session() as session:
        typers = session.query(models.Typer).join(models.Bet).join(models.Event)
        lista = list(map(str, typers[0].bets))
        # lista = list(map(str, typers))
    # lista = [(typer.name,
     #          sum([sum([event.points for event in bet.events]) for bet in typer.bets])) for typer in typers]

    return jsonify(lista)

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
        top = [{'name':typer[0].name, 'points':typer[0].count_point() for typer in typers]

    return jsonify(top)

@app.route('/api/top/dw')
def top_dw():
    """Generate json which contain top 5"""
    raise NotImplemented()

# @app.route('/api/v1/')
