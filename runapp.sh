#!/bin/bash

VIRTUALENVS_DIR="C:\\users\\krystofair\\.virtualenvs\\"
NAME=$(ls $VIRTUALENVS_DIR | grep "$(basename $PWD)-")
PYTHON_HOME=$VIRTUALENVS_DIR\\$NAME
export FLASK_APP=.\\liczer4pg\\goFlask.py
# echo $FLASK_APP
# echo $PYTHON_HOME
$PYTHON_HOME\\Scripts\\flask run
