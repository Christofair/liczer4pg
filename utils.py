from typing import Union

from lxml import html
import re
from datetime import datetime
import pytz

import errors

def parse_post_if_string(post) -> html.HtmlElement:
    if isinstance(post, str):
        p = html.fragment_fromstring(post)
    elif isinstance(post, html.HtmlElement):
        p = post
    else:
        raise ValueError("Post type was neither str nor html.HtmlElement.")
    return p

def collect_posts_from_topic(topic_html_doc: str) -> list[html.Element]:
    """Return all post from topic as html.Element.
    This is entry point of creating posts from string to html.Elements.
    Remove last post if it contains a results.
    """
    try:
        doc = html.document_fromstring(topic_html_doc)
    except Exception as e:
        if isinstance(topic_html_doc, html.HtmlElement):
            doc = topic_html_doc
        else:
            raise
    posts: list[html.Element] = doc.xpath('//article')
    for post in posts:
        imgs = post.cssselect('.cPost_contentWrap')[0].xpath('*//img')
        if any([re.search('.*wyniki.*png', img.get('alt')) for img in imgs]):
            posts.remove(post)
            break
        if any([re.search('.*35a820dc36f8f7f5203f0c731661b385.*png', img.get('src')) for
                img in imgs]):
            posts.remove(post)
            break
        if any([re.search('.*typowanieinnykolor2.*d3509b73d73f36d87c4163016b44e81a.*png',
                          img.get('src')) for img in imgs]):
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

def get_post_owner(post, check_rang=False) -> Union[str, tuple[str, list[str]]]:
    """Retrieve the owner of post from post, and if specified get all its rangs on forum"""
    p = parse_post_if_string(post)
    name = p.xpath('aside/h3/strong/a/span')[0].text_content()
    name = name.strip('\xa0').strip('\n').lower()
    if check_rang:
        major_rang = p.xpath('aside//*[@data-role="group"]')
        rest_rangs = p.xpath('aside//*[@data-role="axen-group-secondary"]')
        rangs = major_rang + rest_rangs
        rangs = [rang.text_content().strip('\n').strip('\xa0').lower() for rang in rangs]
        return (name, rangs)
    return name

def get_all_teams_names(events: list["Event"]) -> list[str]:
    """Collect names of home and away teams from events list."""
    names = []
    for event in events:
        names.extend((event.home_team, event.away_team))
    return names

def get_timestamp_from_typujemy_line(line, year):
    start_time = datetime(1970,1,1)
    tsr = re.search(
        r".*typujemy +do +(\d+).(\d+)(?:\.\d{2,4}){0,1} +do +godziny +(\d+):(\d+).*",
        line.replace('\xa0',' ')
    )
    if tsr:
        start_time = datetime(year, int(tsr.group(2)), int(tsr.group(1)), int(tsr.group(3)),
                            int(tsr.group(4)))
    else:
        raise errors.NotTimeLine("Pattern event doesn't have time line")
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
