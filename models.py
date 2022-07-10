import re
from datetime import date, datetime
from lxml import html


class Event:
    def __init__(self):
        # pattern to result is "X-Y"
        self.home_team = ""
        self.away_team = ""
        self.start_time: datetime = 0
        # result divided on two properties
        self.result = ""
    
    def __repr__(self):
        stra = []
        if self.start_time:
            stra.append(f"event start at {self.start_time.strftime()}")
        stra.append(f"{self.home_team}\t{self.result}\t{self.away_team}")
        return ''.join(stra)

    @property
    def bet_result(self):
        return self.result

    @bet_result.setter
    def bet_result(self, value):
        self.result = value

    @property
    def ended_result(self):
        return self.result

    @ended_result.setter
    def ended_result(self, value):
        self.result = value

    def count_point(self):
        if self._is_perfect_score():
            return 3
        elif self._is_there_two_points():
            return 2
        else:
            return 0

    def _is_perfect_score(self):
        try:
            # parsing to int by map
            bet_result_home, bet_result_away = list(map(int, self.bet_result.split('-')))
            ended_result_home, ended_result_away = list(map(int, self.ended_result.split('-')))
        except ValueError:
            print("Parsing scores failed in Event")
            return False
        else:
            return bet_result_home == ended_result_home and bet_result_away == ended_result_away

    def _is_there_two_points(self):
        if not re.match(r'\d-\d') or not re.match(r'\d-\d'):
            raise ValueError("Invalid value for some result")
        score_home, score_away = self.ended_result.split('-')
        bet_score_home, bet_score_away = self.bet_result.split('-')
        score_home = int(score_home)
        score_away = int(score_away)
        bet_score_home = int(bet_score_home)
        bet_score_away = int(bet_score_away)
        return (score_home == score_away and bet_score_home == bet_score_away
                or score_home > score_away and bet_score_home > bet_score_away
                or score_home < score_away and bet_score_home < bet_score_away)

    @classmethod
    def parse(cls, line):
        """Load event from line"""
        start_of_braces = line.index('(')
        processed_line = line[:start_of_braces]
        splitted_line = re.split(r'(\d+).*-.*(\d+)', processed_line, maxsplit=1)
        home_name, home_score, away_score, away_name = splitted_line
        home_name = home_name.replace('\xa0',' ').strip()
        away_name = away_name.replace('\xa0',' ').strip()
        if away_score is None or home_score is None:
            if away_score is not None or home_score is not None:
                raise ValueError("[PARSER] Line no contain valid result")
        if not home_name or not away_name:
            raise ValueError("[PARSER] Event has no names for teams")
        obj = cls()
        obj.home_team = home_name
        obj.away_team = away_name
        obj.bet_result =  '-'.join([home_score, away_score])
        obj.start_time = 0
        return obj

    @classmethod
    def parse_pattern_event(cls, line, year=None):
        """Load pattern event from line"""
        start_of_braces = line.index('(')
        processed_line = line[:start_of_braces]
        thetime_line = line[start_of_braces:]
        if not year:
            year = date.today().year
        tsr = re.search(r"\(.*typujemy +do +(\d+).(\d+) +do +godziny +(\d+):(\d+).*\)",
                        thetime_line.replace('\xa0',' '))
        try:
            start_time = datetime(year, int(tsr.group(2)), int(tsr.group(1)), int(tsr.group(3)),
                            int(tsr.group(4)))
        except Exception as e:
            print("Error during getting time")
            print(f'parsing line with time was: {thetime_line!r}')
            print(e)
            raise e from None
        home, away = processed_line.split('-')
        home = home.replace('\xa0',' ').strip()
        away = away.replace('\xa0',' ').strip()
        obj = cls()
        obj.home_team = home
        obj.away_team = away
        obj.ended_result = ""
        obj.bet_result = ""
        obj.start_time = start_time
        return obj

    def __eq__(self, other):
        home_cond = self.home_team == other.home_team
        away_cond = self.away_team == other.away_team
        time_cond = self.start_time == other.start_time
        return home_cond and away_cond and time_cond


class Bet:
    def __init__(self):
        self.events = []

    def __repr__(self):
        string_array = ["-----BET------\n"]
        for event in self.events:
            string_array.extend([str(event), "\n"])
        string_array.append("--------------")
        return ''.join(string_array)

    # in that method get single post as in article tag
    @classmethod
    def parse(cls, post) -> "Bet":
        if isinstance(post, str):
            post_root = html.fragment_fromstring(post)
        else:
            post_root = post
        comment_content = post_root.cssselect('.cPost_contentWrap')[0]
        lines = comment_content.text_content().splitlines()
        pattern = r'.+.*\d.*-.*\d.*\(typujemy.*'
        c = re.compile(pattern)
        lines = filter(c.search, lines)
        lines = [l.replace('\xa0',' ') for l in lines]
        try:
            events = [Event.parse(line) for line in lines]
        except ValueError as e:
            print(e)
            return None
        obj = cls()
        obj.events = events
        return obj

class Typer:
    def __init__(self, name, post):
        self.name = name
        if post is not None:
            self.post = self._parse_post_if_string(post)
        self.bet = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"Typer(name={self.name})\nbet={self.bet}"

    @staticmethod
    def _parse_post_if_string(post):
        if isinstance(post, str):
            p = html.fragment_fromstring(post)
        elif isinstance(post, html.HtmlElement):
            p = post
        else:
            raise ValueError("[TYPER INIT] Post type was wrong.")
        return p

    def load_bet(self):
        self.bet = Bet.parse(self.post)

    def get_post_datetime(self):
        t = self.post.xpath('*//time')[0].get('datetime')
        if not t:
            t = self.post.xpath('*//time')[1].get('datetime')
        t = t.replace('T', ' ').rstrip('Z')
        return datetime.fromisoformat(t)

    @staticmethod
    def get_owner(post):
        p = Typer._parse_post_if_string(post)
        name = p.xpath('aside/h3/strong/a/span')[0].text_content()
        name = name.lstrip('\xa0').lower()
        return name

