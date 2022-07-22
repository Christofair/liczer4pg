from flask import Flask, jsonify, request, g

app = Flask('typerka_pg_api')

class Typer:
    """Role of user, who can add topics and then open it and closing"""
    pass

class NotAuthUser:
    """User 

@app.get('/')
def index():
    return jsonify("Nothing")
    pass

@app.route('/top/<str:what>')
def top(what):
    """Represent TOP ranking on website.
    Parameters:
        :what:
    pass
