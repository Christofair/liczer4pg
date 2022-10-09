# Liczer4PG
The Liczer4PG was created to automatic process of counting points at forum PoGrywamy, on which I
warmly invite you. Version 1.0.0 is half automatic, because results have to be inscribe manually.
There is no possibility to paste stream with results to be parsed and automatically counted.
I considered that a program in this form can be treat as version 1.0.0, because it fill my
expectations of ease counting points. The next version with major number 2 (2.0.0) should collect events
to database, there are models prepared for that, but those are not used yet.

# Why I created this. - Motivation
I want that betting at forum to be fun. Cause there is no money for it, only some awards. So I try 
to write topic of leagues people like, watch matches from it, and they will intuitively bet results
for them. Therefore I want have possibility to write more topics without waste of time and then
easy to count all points.

# Installation
To install this flask app, you should clone repo and simple run following command.
```sh
pip install path/to/repo
```
Another method to install, when you don't have `pip` command - tested on my oracle virtual machine.
I get error so that is why write sudo before it.
```sh
[sudo] python3 setup.py install
```

# Run
The entry point of this is goFlask.py. You shold watch that file to know about entrypoints.
Set python environment where you have just installed liczer4pg and run following commands
```sh
export FLASK_APP=goFlask.py
flask run
```

# Run with Docker
Search a Dockerfile, and build an image from it.
That build whole application with NGINX as a proxy.
This version can be used as standalone istance, I think.
```sh
docker image build . -t liczerapi
docker run -d -p 8000:80 liczerapi
```
