"""Models are classes on which we operate in python code, and store persistent state in db"""

from copy import deepcopy
import re
from datetime import date, datetime
from lxml import html
from lxml.etree import tostring as et2str
import liczer4pg.utils as utils
import liczer4pg.errors as errors

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
    # points are here because we can determine more precisely if the typer tied up to it hit
    points = sa.Column(sa.Integer, default=0, nullable=False)
    sport = sa.Column(sa.String(128), nullable=False)

    def as_dict(self):
        """Return event object as basic type dict"""
        return {
            "start_time": self.start_time.timestamp(),
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "winner": self.winner if self.winner is not None and self.winner != "" else None
        }

    @classmethod
    def from_dict(cls, d):
        hs = d.get('home_score')
        _as = d.get('away_score')
        ht = d.get('home_team')
        at = d.get('away_team')
        win = d.get('winner')
        if ((hs is None or hs == "" ) and (_as is None or _as == "")) and (
            win is None or win == ""):
            raise ValueError("Can't create object from this dict")
        if hs == "" or _as == "" or hs is None or _as is None:
            raise ValueError("The names of team in event was empty or None")
        return cls(home_score=hs, away_score=_as, home_team=ht, away_team=at, winner=win)

    def set_score(self, value):
        """Setting score for event. If there is winner type of bet, then
        value 1 for home_team or away_team specifies that winner."""
        if not value:
            self.home_score = 0
            self.away_score = 0
            self.winner = None
        elif '-' in value:
            self.home_score = int(value.split('-')[0])
            self.away_score = int(value.split('-')[1])
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
        if self.winner is not None and self.winner != "":
            stra.append(f"{self.home_team}\tVS\t{self.away_team}")
            stra.append(f"\n[WINNER]\t{self.winner}")
        else:
            stra.append(f"{self.home_team}\t{self.result}\t{self.away_team}")
        return ''.join(stra)

    def __eq__(self, other):
        home_cond = self.home_team == other.home_team
        away_cond = self.away_team == other.away_team
        # time_cond = self.start_time == other.start_time
        return home_cond and away_cond

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


class EventParser:
    """Parser for events from users' posts"""

    def __init__(self, /, ref_date, ref_events=None):
        self.pattern = ref_events
        self.base_date = ref_date

    def parse_winner_type(self, line):
        valid_event = [event for event in deepcopy(self.pattern)
                       if event.home_team in line or event.away_team in line][0]
        # Check if that line was valid as event
        if not valid_event:
            raise errors.NotEventLine("That line %s can't be parsed as event line" % (line,))
        # Shortcuts for names
        home, away = valid_event.home_team, valid_event.away_team
        if home in line and away in line:
            raise errors.NotEventLine("There not choice of winner in line %s" % (line,))
        # Checking winner by finding name in line
        valid_event.winner = home if home in line else away
        # Return that event
        return valid_event

    def parse(self, line):
        """Load event from line"""
        # Find event matching in this line, and operate on deepcopy of events from patterns
        single_valid_event = [event for event in deepcopy(self.pattern)
                            if event.home_team in line and event.away_team in line]
        # Check if that line was valid as event
        if not single_valid_event:
            raise errors.NotEventLine("That line %s can't be parsed as event line" % (line,))
        single_valid_event = single_valid_event[0]
        # Group results ints
        home, away = single_valid_event.home_team, single_valid_event.away_team
        pattern = rf'{home}.*(\d+).*-.*(\d+).*{away}'
        # Search pattern in line
        matching = re.search(pattern, line)
        # Enter the result to that event
        single_valid_event.result = '-'.join([matching.group(1), matching.group(2)])
        # Return it.
        return single_valid_event

    @staticmethod
    def _parse_pattern_event(line, year):
        """Load single event from line of pattern."""
        try:
            start_of_braces = line.index('typujemy')
            if line[start_of_braces-1] == '(':
                start_of_braces -= 1
        except ValueError:
            raise errors.NotTimeLine from None
        processed_line = line[:start_of_braces]
        thetime_line = line[start_of_braces:]
        start_time = utils.get_timestamp_from_typujemy_line(thetime_line, year)
        home, away = processed_line.split(' - ')
        home = home.replace('\xa0',' ').strip()
        away = away.replace('\xa0',' ').strip()
        return Event(
            home_team = home,
            away_team = away,
            home_score = 0,
            away_score = 0,
            winner = None,
            start_time = start_time
        )

    @staticmethod
    def get_pattern_events(posts: list[html.Element]) -> list["Event"]:
        """Return list of events knowns as pattern"""
        pattern_events = []
        for post in posts:
            post_year = utils.get_post_timestamp(post).year
            c = re.compile(r'^[Ww]z[oó]r[:]$')
            lines = list(
                filter(None, post.cssselect('.cPost_contentWrap')[0].text_content().splitlines()))
            flist = [c.search(l) for l in lines if c.search(l) is not None]
            rangs = utils.get_post_owner(post, True)[1]
            if flist and ('typer' in rangs or 'zasłużony' in rangs):
                for i in range(lines.index(flist[0].string), len(lines)):
                    try:
                        pattern_events.append(EventParser._parse_pattern_event(lines[i], post_year))
                    except errors.NotTimeLine:
                        # Never silently pass an exception.
                        logger.exception("Cannot find time line in pattern??")
                        # If in pattern there can't find line with time,
                        # then the event won't be counted
                    except Exception as e:
                        logger.exception(e)
                    if re.search(r"[Mm]oje [tT]ypy[:]", lines[i]):
                        break
                break  # only one post has `c` pattern in it.
        return pattern_events


class Bet(Base):
    __tablename__ = 'bets'
    id = sa.Column(sa.Integer, sa.Sequence('bet_id_seq'), primary_key=True)
    events = orm.relationship('Event', back_populates='bet')
    typer_id = sa.Column(sa.Integer, sa.ForeignKey('typers.id'))
    typer = orm.relationship('Typer', back_populates='bets')
    topic_link = sa.Column(sa.String(255), sa.ForeignKey('topics.link'))
    topic = orm.relationship('Topic', back_populates='bets')

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
        post_date = utils.get_post_timestamp(post)
        parser = EventParser(ref_events=pattern_events, ref_date=post_date)
        comment_content = post_root.cssselect('.cPost_contentWrap')[0]
        names = utils.get_all_teams_names(pattern_events)
        lines = map(lambda x: x.replace('\xa0', ' '), comment_content.text_content().splitlines())
        lines = list(filter(
            lambda l: any([names[i] in l for i in range(len(names))]) and '-' not in l, lines))
        if len(lines) > 0:
            bet = cls()
            bet.events = []
            for line in lines:
                try:
                    bet.events.append(parser.parse_winner_type(line))
                # bet.events = [parser.parse_winner_type(line) for line in lines]
                except errors.NotEventLine:
                    logger.info("line %s was omitted as invalid" % (line,))
                except ValueError as e:
                    logger.error(e)
        return bet

    # in that method get single post as in article tag
    @classmethod
    def parse(cls, post, pattern_events) -> "Bet":
        if isinstance(post, str):
            post_root = html.fragment_fromstring(post)
        else:
            post_root = post
        post_date = utils.get_post_timestamp(post)
        parser = EventParser(ref_date=post_date, ref_events=pattern_events)
        comment_content = post_root.cssselect('.cPost_contentWrap')[0]
        lines = comment_content.text_content().splitlines()
        rangs = utils.get_post_owner(post, True)[1]
        if "typer" in rangs or "zasłużony" in rangs:
            try:
                line = [l for l in lines if re.search(r'[Mm]oje [Tt]ypy[:]', l)][0]
                lines = lines[lines.index(line):]
            except Exception as e:
                print("Topic author doesn't include own bet")
                print(e)
        pattern = r'.+\d.*-.*\d.+(?:\(typujemy.*){0,1}'
        c = re.compile(pattern)
        lines = filter(c.search, lines)
        lines = [l.replace('\xa0',' ') for l in lines]
        events = []
        for line in lines:
            try:
                events.append(parser.parse(line))
            except errors.NotEventLine:
                logger.info("line %s was omitted as invalid" % (line,))
            except ValueError as e:
                logger.error(e)
        bet = cls()
        bet.events = events
        return bet

    def count_point(self, good_events_list, kind='scores'):
        """Count point for event if events are equal and the result is correct in some way"""
        # [0] is for get rid nested array, but there is only single element always.
        # There is only single element, because of checking equality of events.
        # checking equality has to be in first list comprehension, because undefined of variable
        if kind == 'scores':
            counting_function = lambda x, y: x.count_point_scores(y)
        # TODO: try change winner to winners
        elif kind == 'winner':
            counting_function = lambda x, y: x.count_point_winner(y)
        else:
            ValueError("Function to counting points is not known")
        if len(good_events_list) != len(self.events):
            ValueError("good_events_list and self.events have different sizes")
        if not good_events_list:
            raise ValueError("good event list was empty")
        return sum([[counting_function(event, good_event)
                    for good_event in good_events_list
                        if event == good_event][0]
                    for event in self.events])


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


    @property
    def bet(self):
        try:
            bet = self.bets.pop()
        except IndexError:
            bet = None
        else:
            self.bets.append(bet)
        return bet

    def __init__(self, name, post):
        self.name = name
        if post is not None:
            self._post = utils.parse_post_if_string(post)
            # self.posts.append(et2str(utils.parse_post_if_string(post)))

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
        #     self._post = utils.parse_post_if_string(self.wpis)

    @post.setter
    def post(self, value):
        self._post = utils.parse_post_if_string(value)
        # self.posts.append(Post(typer_id=self.id, post=et2str(self._post)))

    def load_bet(self, pattern_events, winner_type):
        if not winner_type:
            bet = Bet.parse(self.post, pattern_events)
        else:
            bet = Bet.parse_winner_type(self.post, pattern_events)
        self.bets.append(bet)

    def add_bet(self, bet):
        self.bets.append(bet)

    def count_points_from_bets(self):
        """Count all points from events from bets. Count only from these bets, which was loaded."""
        total = 0
        for bet in self.bets:
            summ = sum([event.points for event in bet.events])
            total += summ
        return total


class Topic(Base):
    """Represent topic, which can be opened/closed"""
    __tablename__ = 'topics'
    link = sa.Column(sa.String(255), unique=True, primary_key=True)
    name = sa.Column(sa.String(255), nullable=True)
    is_open = sa.Column(sa.Boolean, default=True, nullable=False)
    last_event_end = sa.Column(sa.DateTime)
    sport = sa.Column(sa.String(128))
    # tournament = sa.Column(sa.String(128), nullable=False)
    bets = orm.relationship('Bet', back_populates='topic')

    def __repr__(self):
        return "[%s]|%s|%s" % ("OPEN" if self.is_open else "CLOSE", self.link, self.sport)

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
