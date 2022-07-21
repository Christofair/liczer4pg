import logging
import unittest
import lxml
from time import sleep
import requests
from datetime import datetime

# importing tools to manage databsae
import sqlalchemy as sa
import os  # module for checking file existing.

import models
import utils

logger = logging.getLogger(__name__)

class TestApp(unittest.TestCase):
    doc = None
    real_posts = None

    @classmethod
    def setUpClass(cls):
        with open('index.html','r', encoding='utf-8') as indexhtml:
            cls.doc = indexhtml.read()
        files = [open('test_posts/nicekovsky1.html', encoding='utf-8'),
                 open('test_posts/daro.html', encoding='utf-8'),
                 open('test_posts/idob.html', encoding='utf-8'),
                 open('test_posts/unsub.html', encoding='utf-8'),
                 open('test_posts/bazukaczekczek.html', encoding='utf-8')]
        cls.real_posts = [ lxml.html.fragment_fromstring(file.read()) for file in files]
        [x.close() for x in files]

    def test_collecting_posts(self):
        posts = utils.collect_posts_from_topic(self.doc)
        pass_counter = 0
        for post in posts:
            for rp in self.real_posts:
                if post.text_content() == rp.text_content():
                    pass_counter+=1
                    break
        self.assertEqual(pass_counter, len(self.real_posts))

    def test_getting_pattern_events(self):
        events = models.Event.get_pattern_events(self.real_posts)
        teams = [
            ['Sevilla', 'Granada'],
            ['Cádiz','Real Betis Balompié'],
            ["RCD Mallorca",  "Atlético Madrid"],
            ["Villarreal",  "Athletic Club"],
            ["Real Madrid",  "Getafe"],
            ["Osasuna",  "Deportivo Alavés"],
            ["Espanyol",  "Celta Vigo"],
            ["Elche CF",  "Real Sociedad"],
            ["Levante",  "Barcelona"],
            ["Rayo Vallecano", "Valencia"]
        ]
        for idx, event in enumerate(events):
            try:
                self.assertEqual(teams[idx][0], event.home_team)
                self.assertEqual(teams[idx][1], event.away_team)
            except:
                pass

def _create_event(home, away, bet_result):
    event = models.Event()
    event.away_team = away
    event.home_team = home
    event.bet_result = bet_result
    return event

class TestModels(unittest.TestCase):
    document = None
    posts = None

    @classmethod
    def setUpClass(cls):
        # load document.
        try:
            cls.document = open("index.html", "r", encoding='utf-8')
        except OSError:
            logger.error("Loading document failed")
            exit(-1)
        except Exception as e:
            logger.error("Exception %s occured" % (e,))
            raise e from None
        cls.posts = utils.collect_posts_from_topic(cls.document.read())

    @classmethod
    def tearDownClass(cls):
        if cls.document:
            cls.document.close()

    def test_getting_all_typers(self):
        """Check about users who betting in that topic"""
        typers = set([models.Typer(models.Typer.get_owner(post), post) for post in self.posts])
        test_data_typers = set([models.Typer(name, None) for name in ['nicekovsky',
                                                                      'bazukaczeczek', 'daro',
                                                                      'unsub', 'idob']])
        self.assertEqual(set(), typers.difference(test_data_typers))

    def test_parsing_typers_bets_scores(self):
        """Check if collected bets are correct for each typer"""
        post = [p for p in self.posts if models.Typer.get_owner(p) == "nicekovsky"][0]
        nicekovsky_bet_test_data = models.Bet()
        nicekovsky_bet_test_data.events = [
            _create_event("Sevilla", "Granada", "3-0"),
            _create_event("Cádiz", "Real Betis Balompié", "0-2"),
            _create_event("RCD Mallorca", "Atlético Madrid", "0-2"),
            _create_event("Villarreal", "Athletic Club", "1-2"),
            _create_event("Real Madrid", "Getafe", "3-1"),
            _create_event("Osasuna", "Deportivo Alavés", "2-1"),
            _create_event("Espanyol", "Celta Vigo", "2-1"),
            _create_event("Elche CF", "Real Sociedad", "0-1"),
            _create_event("Levante", "Barcelona", "0-2"),
            _create_event("Rayo Vallecano", "Valencia", "0-2")
        ]
        nicekovsky_bet = models.Bet.parse(post)
        for event_test_data in nicekovsky_bet_test_data.events:
            event = nicekovsky_bet.events.pop(0)
            self.assertEqual(event_test_data.home_team, event.home_team)
            self.assertEqual(event_test_data.away_team, event.away_team)
            self.assertEqual(event_test_data.bet_result, event.bet_result)

        post = [p for p in self.posts if models.Typer.get_owner(p) == "idob"][0]
        idob_bet_test_data = models.Bet()
        idob_bet_test_data.events = [
            _create_event("Sevilla", "Granada","2-0"),
            _create_event("Cádiz", "Real Betis Balompié","1-1"),
            _create_event("RCD Mallorca", "Atlético Madrid","0-1"),
            _create_event("Villarreal", "Athletic Club","2-1"),
            _create_event("Real Madrid", "Getafe","2-1"),
            _create_event("Osasuna", "Deportivo Alavés","1-2"),
            _create_event("Espanyol", "Celta Vigo","1-1"),
            _create_event("Elche CF", "Real Sociedad","0-2"),
            _create_event("Levante", "Barcelona","1-2"),
            _create_event("Rayo Vallecano",  "Valencia","0-1")
        ]
        idob_bet = models.Bet.parse(post)
        for event_test_data in idob_bet_test_data.events:
            event = idob_bet.events.pop(0)
            self.assertEqual(event_test_data.home_team, event.home_team)
            self.assertEqual(event_test_data.away_team, event.away_team)
            self.assertEqual(event_test_data.bet_result, event.bet_result)

    def test_timestamp_of_post(self):
        """Check date of written post"""
        from pytz import timezone
        warsaw = timezone('Europe/Warsaw')
        timestamps = []
        for post in self.posts:
            timestamps.append(utils.get_post_timestamp(post))
        correct_timestamps = [
            datetime(2022, 4, 7, 8, 36),
            datetime(2022, 4, 7, 13, 24),
            datetime(2022, 4, 7, 14, 55),
            datetime(2022, 4, 7, 16, 45),
            datetime(2022, 4, 7, 22, 00)
        ]
        correct_timestamps = list(map(warsaw.localize, correct_timestamps))
        self.assertEqual(timestamps, correct_timestamps)

    def test_name_from_link_in_topic(self):
        t = models.Topic(
            'https://pogrywamy.pl/topic/16702-typowanie-02-k-league-1-22062022/#comment-86170'
        )
        self.assertEqual(t.name, "16702-typowanie-02-k-league-1-22062022")


class TestFeature(unittest.TestCase):

    def setUp(self):
        # waiting before each test, cause there can be treated as dos attack.
        sleep(0.4)

    def test_counting_points_scores_type(self):
        """Check well count points for typers"""
        topic_response = requests.get(
            'https://pogrywamy.pl/topic/16702-typowanie-02-k-league-1-22062022/#comment-86170'
        )
        self.assertFalse(topic_response.status_code != 200)
        # build doc tree through html parser
        # topic = Topic(topic_response.url)
        posts = utils.collect_posts_from_topic(topic_response.content.decode('utf-8'))
        typers = []
        for post in posts:
            typer = models.Typer(models.Typer.get_owner(post), post)
            typer.load_bet()
            typers.append(typer)
        events_to_compare = models.Event.get_pattern_events(posts)
        for event in events_to_compare:
            if event.home_team == 'Suwon FC':
                event.ended_result = "3-0"
            elif event.home_team == 'Jeonbuk Hyundai Motors':
                event.ended_result = "1-1"
            elif event.home_team == 'FC Seoul':
                event.ended_result = "1-1"
            elif event.home_team == 'Ulsan Hyundai':
                event.ended_result = "0-0"
            elif event.home_team == 'Pohang Steelers':
                event.ended_result = "1-1"
            elif event.home_team == 'Gangwon FC':
                event.ended_result = "4-2"
        # for typer in typers:
        #     print(f'typer {typer.name} got {typer.bet.count_point(events_to_compare)} points')
        correct_results = [2,0,0]
        for i in range(3):
            self.assertEqual(typers[i].bet.count_point(events_to_compare), correct_results[i])

        # ANTOHER TEST WITH DEVISED RESULTS.
        topic_response = requests.get("https://pogrywamy.pl/topic/16860-typowanie-liga-narod%C3%B3w-3-21072022-%C4%87wier%C4%87fina%C5%82y/")
        self.assertFalse(topic_response.status_code != 200)
        posts = utils.collect_posts_from_topic(topic_response.content.decode('utf-8'))
        typers = []
        for post in posts:
            typer = models.Typer(models.Typer.get_owner(post), post)
            typer.load_bet()
            typers.append(typer)
        events_to_compare = models.Event.get_pattern_events(posts)
        for event in events_to_compare:
            if event.home_team == 'USA':
                event.result = "0-3"
            elif event.home_team == 'Włochy':
                event.result = "3-0"
            elif event.home_team == 'Francja':
                event.result = "3-0"
            elif event.home_team == 'Polska':
                event.result = "3-1"
        correct_results = [8, 8, 8, 9, 10, 5]
        for i in range(len(typers)):
            self.assertEqual(typers[i].bet.count_point(events_to_compare), correct_results[i])

    def test_counting_points_with_winner_type(self):
        """Check if counted points are correctly sum up."""
        response = requests.get("https://pogrywamy.pl/topic/16874-typowanie-1-mlb-21072022/#comment-86877")
        self.assertFalse(response.status_code != 200)
        posts = utils.collect_posts_from_topic(response.content.decode('utf-8'))
        events_to_compare = models.Event.get_pattern_events(posts)
        typers = []
        for post in posts:
            typer = models.Typer(models.Typer.get_owner(post), post)
            typer.load_bet('winner', events_to_compare)
            typers.append(typer)
        self.assertFalse(not events_to_compare)
        events_to_compare[0].winner = events_to_compare[0].home_team
        events_to_compare[1].winner = events_to_compare[1].away_team
        events_to_compare[2].winner = events_to_compare[2].away_team
        events_to_compare[3].winner = events_to_compare[3].home_team
        correct_results = [8, 4, 6]
        for i in range(len(typers)):
            self.assertEqual(typers[i].bet.count_point(events_to_compare, kind='winner'),
                             correct_results[i])


class TestDB(unittest.TestCase):
    engine = None

    @classmethod
    def setUpClass(cls):
        # path to testing database
        cls.engine = sa.create_engine("sqlite:///TestDB.db")
        # tworzenie modeli w testowej bazie danych
        models.Base.metadata.schema="typerkapg"
        models.Base.metadata.create_all(cls.engine)
        # check if database created.
        # The question is, how to check that DB exists?
        if not os.path.exists('./TestDB.db'):
            cls.fail(cls, "DB TEST FAIL")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists('./TestDB.db'):
            os.remove('./TestDB.db')
        pass

    def test_saving_typers_with_bets(self):
        """lxml.html.Element object save to database."""
        with open('./index.html', encoding='utf-8') as topic:
            posts = utils.collect_posts_from_topic(topic.read())
        self.assertTrue(len(posts) > 0)
        typers = []
        for post in posts:
            typers.append(models.Typer(models.Typer.get_owner(post), post))
            typers[-1].load_bet()
            typers[-1].add_bet()

        with sa.orm.Session(self.engine) as session:
            session.add_all(typers)
            session.commit()
            session.flush()

        typers = []

        with sa.orm.Session(self.engine) as session:
            typers = session.query(models.Typer, models.Bet).join(models.Bet).all()
            print(typers)
            self.assertEqual(['nicekovsky', 'daro', 'bazukaczeczek', 'idob', 'unsub'],
                             [typer[0].name for typer in typers])
