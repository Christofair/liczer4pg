import re
from datetime import date, datetime
from lxml import html

class Event:
    def __init__(self):
        # pattern to result is "X-Y"
        ended_result = ""
        home_team = ""
        away_team = ""
        start_time = 0 
        bet = None

    def count_point(self):
        if self._is_perfect_score():
            return 3
        elif self._check_bet_for_result():
            return 2
        else:
            return 0

    def _is_perfect_score(self):
        return self.ended_result == self.bet

    def _is_there_two_points(self):
        if not re.match(r'\d-\d') or not re.match(r'\d-\d'):
            raise ValueError("Invalid value for some result")
        score_home, score_away = self.ended_result.split('-')
        bet_score_home, bet_score_away = self.bet.split('-')
        score_home = int(score_home)
        score_away = int(score_away)
        bet_score_home = int(bet_score_home)
        bet_score_away = int(bet_score_away)
        if (score_home == score_away and bet_score_home == bet_score_away
                or score_home > score_away and bet_score_home > bet_score_away
                or score_home < score_away and bet_score_home < bet_score_away):
            return True
        else:
            return False

    @classmethod
    def parse(cls, line, year=None):
        start_of_braces = line.index('(')
        processed_line = line[:start_of_braces]
        thetime_line = line[start_of_braces:]
        if not year:
            year = date.today().year
        tsr = re.search(r"\(typujemy do (\d+).(\d+) do godziny (\d+):(\d+)\)",
                        thetime_line)
        try:
            start_time = date(year, int(tsr.group(2)), int(tsr.group(1)), int(tsr.group(3)),
                            int(tsr.group(4)))
        except Exception as e:
            print("Error during getting time")
            print(e)
            raise e from None
        home, away = processed_line.split('-')
        home_re = re.search(r"(.+).+(\d).*", processed_line)
        away_re = re.search(r".*(\d).+(.+)", processed_line)
        home_name = home_re.group(1)
        home_score = home_re.group(2)
        away_name = away_re.group(2)
        away_score = away_re.group(1)
        if away_score is None or home_score is None:
            if away_score is not None or home_score is not None:
                raise ValueError("[PARSER] Line no contain valid result")
        if not home_name or not away_name:
            raise ValueError("[PARSER] Event has no names for teams")

        obj = cls()
        obj.home_team = home_name
        obj.away_team = away_name
        obj.ended_result = '-'.join([home_score, away_score])
        obj.start_time = start_time
        return obj

class Bet:
    def __init__(self):
        events = []

    # in that method get single post as in article tag
    @staticmethod
    def parse(post) -> "Bet":
        post_root = html.fragment_fromstring(post)
        post_root.cssselect('#cPost_contentWrap')

        pass

class Typer:
    def __init__(self, name, post):
        self.name = name
        self.post = post
        self.bets = []

    def load_bets(self):
        pass

    def get_post_datetime(self):
        t = etree.fromstring(self.post, parser='html')

