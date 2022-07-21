"""Models are classes on which we operate in python code, and store persistent state in db"""

import re
from datetime import date, datetime
from lxml import html
from lxml.etree import tostring as et2str
import utils

# imports for do database
import sqlalchemy as sa
import sqlalchemy.orm as orm
import logging

logger = logging.getLogger(__name__)

Base = orm.declarative_base()

class Event(Base):
    __tablename__ = 'events'
    id = sa.Column(sa.Integer, sa.Sequence('event_id_seq'), primary_key=True)
    bet_id = sa.Column(sa.Integer, sa.ForeignKey('bets.id'))
    bet = orm.relationship('Bet', back_populates='events')
    start_time = sa.Column(sa.DateTime, nullable=False, default=datetime(1970,1,1))
    home_team = sa.Column(sa.String(255), nullable=False)
    away_team = sa.Column(sa.String(255), nullable=False)
    home_score = sa.Column(sa.Integer, default=None, nullable=True)
    away_score = sa.Column(sa.Integer, default=None, nullable=True)
    winner = sa.Column(sa.String(255), default=None, nullable=True)
    result_required = sa.CheckConstraint(
        '(winner is NULL and home_score is not NULL and away_score is not NULL)'
        ' or (winner is not NULL and home_score is NULL and away_score is NULL)')
    points = sa.Column(sa.Integer, default=0, nullable=False)
    sport = sa.Column(sa.String(128), nullable=False)

    def set_score(self, value):
        """Setting score for event. If there is winner type of bet, then
        value 1 for home_team or away_team specifies that winner."""
        if not value:
            self.home_score = 0
            self.away_score = 0
            self.winner = None
        elif '-' in value:
            self.home_score = value.split('-')[0]
            self.away_score = value.split('-')[1]
            if self.home_score > self.away_score:
                self.winner = self.home_team
            elif self.home_score < self.away_score:
                self.winner = self.away_team
            else:
                self.winner = None
        else:
            if value == self.home_team:
                self.home_score = None
                self.away_score = None
                self.winner = value
            elif value == self.away_team:
                self.home_score = None
                self.away_score = None
                self.winner = value
            else:
                ValueError("Passed value has wrong style")

    def get_score(self):
        return "{}-{}".format(self.home_score, self.away_score)

    result = property(get_score, set_score)
    bet_result = property(get_score, set_score)
    ended_result = property(get_score, set_score)

    def __repr__(self):
        stra = []
        if self.start_time:
            stra.append(f"\nStart at {self.start_time.ctime()}\n")
        if self.winner is not None and self.result == "0-0":
            stra.append(f"{self.home_team}\tVS\t{self.away_team}")
            stra.append(f"\n[WINNER]\t{self.winner}")
        else:
            stra.append(f"{self.home_team}\t{self.result}\t{self.away_team}")
        return ''.join(stra)

    def count_point_scores(self, result_event):
        if self != result_event:
            raise ValueError("These events are different.")
        if self._is_perfect_score(result_event):
            return 3
        elif self._is_there_two_points(result_event):
            return 2
        return 0

    def count_point_winner(self, result_event):
        # check if winner is play in this event at all
        if self.winner in self.home_team or self.winner in self.away_team:
            return 2 if self.winner == result_event.winner else 0
        else:
            raise ValueError("That player or team was not play in this event")
        return 0

    def _is_perfect_score(self, result_event):
            home_cond = self.home_score == result_event.home_score
            away_cond = self.away_score == result_event.away_score
            return home_cond and away_cond

    def _is_there_two_points(self, result_event):
        return ((self.home_score == self.away_score
                 and result_event.home_score == result_event.away_score)
                or (self.home_score > self.away_score
                    and result_event.home_score > result_event.away_score)
                or (self.home_score < self.away_score
                    and result_event.home_score < result_event.away_score))

    @classmethod
    def parse_winner_type(cls, line, ref_event, year=None):
        sb = len(line)
        try:
            sb = line.index('(')
            thetime_line = line[sb:]
            if not year:
                year = date.today().year
            start_time = utils.get_timestamp_from_typujemy_line(thetime_line, year)
        except ValueError:
            try: sb = line.index('\xa0')
            except: pass
        obj = cls()
        obj.winner = line[:sb].strip()
        obj.start_time = start_time
        obj.home_team = ref_event.home_team
        obj.away_team = ref_event.away_team
        obj.home_score = 0
        obj.away_score = 0
        return obj


    @classmethod
    def parse(cls, line, year=None):
        """Load event from line"""
        pattern = r'(\d+).*-.*(\d+)'
        start_of_braces = line.index('(')
        processed_line = line[:start_of_braces]
        splitted_line = re.split(pattern, processed_line, maxsplit=1)
        if len(splitted_line) < 2:
            raise ValueError("[EVENT PARSER] The line was wrong formatted")
        home_name, home_score, away_score, away_name = splitted_line
        home_name = home_name.replace('\xa0',' ').strip()
        away_name = away_name.replace('\xa0',' ').strip()
        thetime_line = line[start_of_braces:]
        if not year:
            year = date.today().year
        try:
            start_time = utils.get_timestamp_from_typujemy_line(thetime_line, year)
        except Exception as e:
            logger.exception("Error during getting time")
            logger.info(f'parsing line with time was: {thetime_line!r}')
            raise e from None
        if away_score is None or home_score is None:
            if away_score is not None or home_score is not None:
                raise ValueError("[PARSER] Line no contain valid result")
        if not home_name or not away_name:
            raise ValueError("[PARSER] Event has no names for teams")
        obj = cls()
        obj.home_team = home_name
        obj.away_team = away_name
        obj.home_score = home_score
        obj.away_score = away_score
        obj.start_time = start_time
        return obj

    @classmethod
    def _parse_pattern_event(cls, line, year=None):
        """Load pattern event from line"""
        start_of_braces = line.index('(')
        processed_line = line[:start_of_braces]
        thetime_line = line[start_of_braces:]
        if not year:
            year = date.today().year
        start_time = utils.get_timestamp_from_typujemy_line(thetime_line, year)
        home, away = processed_line.split('-')
        home = home.replace('\xa0',' ').strip()
        away = away.replace('\xa0',' ').strip()
        obj = cls()
        obj.home_team = home
        obj.away_team = away
        obj.home_score = 0
        obj.away_score = 0
        obj.start_time = start_time
        return obj

    @staticmethod
    def get_pattern_events(posts: list[html.Element]) -> list["Event"]:
        """Return post in which is pattern for all bets."""
        pattern_events = []
        for post in posts:
            post_year = utils.get_post_timestamp(post).year
            c = re.compile(r'^[Ww]z[oó]r[:]$')
            lines = list(
                filter(None, post.cssselect('.cPost_contentWrap')[0].text_content().splitlines()))
            flist = [c.search(l) for l in lines if c.search(l) is not None]
            if flist:
                for i in range(lines.index(flist[0].string), len(lines)):
                    try:
                        pattern_events.append(Event._parse_pattern_event(lines[i],
                                                                         year=post_year))
                    except ValueError as e:
                        # only logging, that there was an exception 
                        # Never silently pass an exception.
                        logger.info(e)
                        pass  # value error can be passed away.
                    except Exception as e:
                        logger.exception(e)
                    if re.search(r"[Mm]oje [tT]ypy[:]", lines[i]) or lines[i] == '\xa0':
                        break
                break  # only one post has `c` pattern in it.
        return pattern_events


    def __eq__(self, other):
        home_cond = self.home_team == other.home_team
        away_cond = self.away_team == other.away_team
        # time_cond = self.start_time == other.start_time
        return home_cond and away_cond


class Bet(Base):
    __tablename__ = 'bets'
    id = sa.Column(sa.Integer, sa.Sequence('bet_id_seq'), primary_key=True)
    events = orm.relationship('Event', back_populates='bet')
    typer_id = sa.Column(sa.Integer, sa.ForeignKey('typers.id'))
    typer = orm.relationship('Typer', back_populates='bets')
    topic_link = sa.Column(sa.String(255), sa.ForeignKey('topics.link'))

    def __init__(self):
        self.events = []

    def __repr__(self):
        string_array = ["-----BET------\n"]
        for event in self.events:
            string_array.extend([str(event), "\n"])
        string_array.append("--------------")
        return ''.join(string_array)

    @classmethod
    def parse_winner_type(cls, post, pattern_events) -> "Bet":
        if isinstance(post, str):
            post_root = html.fragment_fromstring(post)
        else:
            post_root = post
        bet = None
        post_year = utils.get_post_timestamp(post).year
        comment_content = post_root.cssselect('.cPost_contentWrap')[0]
        names = utils.get_all_teams_names(pattern_events)
        lines = map(lambda x: x.replace('\xa0', ' '), comment_content.text_content().splitlines())
        lines = list(filter(
            lambda l: any([names[i] in l for i in range(len(names))]) and '-' not in l, lines))
        if len(lines) > 0:
            bet = cls()
            try:
                for line in lines:
                    ref_event = [event for event in pattern_events
                                if event.home_team in line or event.away_team in line][0]
                    event = Event.parse_winner_type(line, ref_event, year=post_year)
                    bet.events.append(event)
            except ValueError as e:
                logger.error(e)
        return bet


    # in that method get single post as in article tag
    @classmethod
    def parse(cls, post) -> "Bet":
        if isinstance(post, str):
            post_root = html.fragment_fromstring(post)
        else:
            post_root = post
        post_year = utils.get_post_timestamp(post).year
        comment_content = post_root.cssselect('.cPost_contentWrap')[0]
        lines = comment_content.text_content().splitlines()
        pattern = r'.+.*\d.*-.*\d.*(?:\(typujemy.*){0,1}'
        c = re.compile(pattern)
        lines = filter(c.search, lines)
        lines = [l.replace('\xa0',' ') for l in lines]
        try:
            events = [Event.parse(line, year=post_year) for line in lines]
        except ValueError as e:
            logger.error(e)
        obj = cls()
        obj.events = events
        return obj

    def count_point(self, good_events_list, kind='scores'):
        """Count point for event if events are equal and the result is correct in some way"""
        # [0] is for get rid nested array, but there is only single element always.
        # There is only single element, because of checking equality of events.
        # checking equality has to be in first list comprehension, because undefined of variable
        if kind == 'scores':
            counting_function = lambda x, y: x.count_point_scores(y)
        elif kind == 'winner':
            counting_function = lambda x, y: x.count_point_winner(y)
        else:
            ValueError("Function to counting points is not known")
        if len(good_events_list) != len(self.events):
            ValueError("good_events_list and self.events have different sizes")
        if good_events_list:
            return sum([[counting_function(event, good_event)
                        for good_event in good_events_list
                            if event.home_team == good_event.home_team][0]
                        for event in self.events])
        raise ValueError("good event list was empty")


# Class for collect posts of typers, but I dont want to collect them at first
# class Post(Base):
#     __tablename__ = 'posts'
#     id = sa.Column(sa.Integer, primary_key=True)
#     typer_id = sa.Column(sa.Integer, sa.ForeignKey('typers.id')) 
#     typer = orm.relationship('Typer', back_populates='posts')
#     post = sa.Column(sa.BLOB)


class Typer(Base):
    __tablename__ = 'typers'
    id = sa.Column(sa.Integer, sa.Sequence('typer_id_seq'), primary_key=True)
    name = sa.Column(sa.String(255), index=True, unique=True)
    bets = orm.relationship('Bet', back_populates='typer')
    # posts = orm.relationship('Post', back_populates='typer')

    def __init__(self, name, post):
        self.name = name
        if post is not None:
            self._post = self._parse_post_if_string(post)
            # self.posts.append(et2str(self._parse_post_if_string(post)))
        self.bet = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"Typer({self.name})"

    @property
    def post(self):
        return self._post
        # else:
        #     self._post = self._parse_post_if_string(self.wpis)

    @post.setter
    def post(self, value):
        self._post = self._parse_post_if_string(value)
        # self.posts.append(Post(typer_id=self.id, post=et2str(self._post)))

    @staticmethod
    def _parse_post_if_string(post):
        if isinstance(post, str):
            p = html.fragment_fromstring(post)
        elif isinstance(post, html.HtmlElement):
            p = post
        else:
            raise ValueError("[TYPER INIT] Post type was wrong.")
        return p

    def load_bet(self, kind='scores', pattern_events=[]):
        if kind == 'scores':
            self.bet = Bet.parse(self.post)
        elif kind == 'winner':
            if len(pattern_events) > 0:
                self.bet = Bet.parse_winner_type(self.post, pattern_events)

    def add_bet(self, bet=None):
        if bet is not None:
            self.bets.append(bet)
            self.bet = bet
        elif self.bet is not None:
            self.bets.append(self.bet)

    def when_written(self):
        return utils.get_post_timestamp(self.post)

    @staticmethod
    def get_owner(post):
        p = Typer._parse_post_if_string(post)
        name = p.xpath('aside/h3/strong/a/span')[0].text_content()
        name = name.lstrip('\xa0').lower()
        return name


class Topic(Base):
    """Represent topic, which can be opened/closed"""
    __tablename__ = 'topics'
    link = sa.Column(sa.String(255), unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=True)
    is_open = sa.Column(sa.Boolean, default=True, nullable=False)
    last_event_end = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String(128))
    bets = orm.relationship('Bet')

    def __init__(self, link, name=""):
        self.is_open = True
        self.link = link
        if not name:
            splitted_link = link.split('/')
            self.name = splitted_link[splitted_link.index('topic')+1]
        else:
            self.name = name

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    @staticmethod
    def _repr_event_to_pattern(event):
        if event.start_time == datetime(1970,1,1):
            raise ValueError("Invalid event date in construction of pattern to topic")
        event_pattern = ("{} - {} (typujemy do {} )"
                         .format(event.home_team, event.away_team,
                                 event.start_time.strftime("%d.%m do godziny %H:%M")))

    def generate_topic_part(self, events: list[Event]):
        events_in_string = []
        events_failed = []
        for event in events:
            try:
                events_in_string.append(self._repr_event_to_pattern(event))
            except ValueError:
                events_failed.append(event)
        return '\n'.join(events_in_string)
