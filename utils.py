from lxml import html
import re
from datetime import datetime
import pytz


def collect_posts_from_topic(topic_html_doc: str) -> list[html.Element]:
    """Return all post from topic as html.Element.
    This is entry point of creating posts from string to html.Elements.
    Remove last post if it contains a results.
    """
    try:
        doc = html.document_fromstring(topic_html_doc)
    except Exception as e:
        print(e)
    posts: list[html.Element] = doc.xpath('//article')
    for post in posts:
        # TODO: Add condition to searching "punktacja" string.
        imgs = post.cssselect('.ipsColumn_fluid')[0].xpath('*//img')
        if any([re.search('.*wyniki.*png', img.get('alt')) for img in imgs]):
            posts.remove(post)
            break
    return posts

def get_post_timestamp(post, timezone='Europe/Warsaw') -> datetime:
    """Get timestamp from `post` and convert to `timezone`"""
    output_timezone = pytz.timezone(timezone)
    utc_timezone = pytz.timezone('utc')
    t = post.xpath('*//time')[0].get('datetime')
    if not t:
        t = post.xpath('*//time')[1].get('datetime')
    t = t.replace('T', ' ')
    # get rid of seconds and miliseconds then treat it as in utc timezone
    t = utc_timezone.localize(datetime.fromisoformat(t[:t.rindex(':')]))
    return output_timezone.normalize(t)

def get_all_teams_names(events: list["Event"]) -> list[str]:
    """Collect names of home and away teams from events list."""
    names = []
    for event in events:
        names.extend((event.home_team, event.away_team))
    return names

def get_timestamp_from_typujemy_line(line, year):
    start_time = datetime(1970,1,1)
    tsr = re.search(
        r"\(.*typujemy +do +(\d+).(\d+)(?:\.\d{2,4}){0,1} +do +godziny +(\d+):(\d+).*\)",
        line.replace('\xa0',' ')
    )
    if tsr:
        start_time = datetime(year, int(tsr.group(2)), int(tsr.group(1)), int(tsr.group(3)),
                            int(tsr.group(4)))
    else:
        raise ValueError("Pattern event doesn't have time line")
    return start_time

def normalize_name(word: str):
    """The function normalize polish words to do not use diacritic chars"""
    letter_map = { 'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ó': 'o',
        'ś': 's', 'ż': 'z', 'ź': 'z', 'é': 'e', 'á': 'a',
    }
    # normalize to lower and not WS-es before and after
    w = word.lower().strip()
    for k, v in letter_map.items():
        w = w.replace(k, v)
    return w
