import logging
import unittest
import lxml

import models
import app

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
        posts = app.collect_posts_from_topic(self.doc)
        pass_counter = 0
        for post in posts:
            for rp in self.real_posts:
                if post.text_content() == rp.text_content():
                    pass_counter+=1
                    break
        self.assertEqual(pass_counter, len(self.real_posts))

    def test_getting_pattern_events(self):
        events = app.get_pattern_events(self.real_posts)
        teams = [
            ['Sevilla','Granada'],
            ['Cádiz','Real Betis Balompié'],
            ["RCD Mallorca",  "Atlético Madrid"],
            ["Villarreal",  "Athletic Club"],
            ["Real Madrid",  "Getafe"],
            ["Osasuna",  "Deportivo Alavés"],
            ["Espanyol",  "Celta Vigo"],
            ["Elche CF",  "Real Sociedad"],
            ["Levante",  "Barcelona "],
            ["Rayo Vallecano", "Valencia"]
        ]
        for idx, event in enumerate(events):
            self.assertEqual(teams[idx][0], event.home_team)
            self.assertEqual(teams[idx][1], event.away_team)

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
        cls.posts = app.collect_posts_from_topic(cls.document.read())

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

    def test_typers_bets(self):
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
            c1 = event_test_data.home_team == event.home_team
            c2 = event_test_data.away_team == event.away_team
            c3 = event_test_data.bet_result == event.bet_result
            self.assertTrue(c1 and c2 and c3)

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
            c1 = event_test_data.home_team == event.home_team
            c2 = event_test_data.away_team == event.away_team
            c3 = event_test_data.bet_result == event.bet_result
            self.assertTrue(c1 and c2 and c3)

    def test_timestamp_of_post(self):
        """Check date of written post"""
        pass

    def test_finding_pattern_to_follow(self):
        """Check pattern in which there are names of teams and timestamps to start match"""
        # For this should be a function with passing a post content to it.
        pass

    def test_getting_single_event(self):
        """Check if single event from post have properly set date,
        and result if there was a result."""
        pass
