from lxml import html
import re
import models


def collect_posts_from_topic(topic_html_doc):
    """Return all post from topic"""
    doc = html.document_fromstring(topic_html_doc)
    posts = doc.xpath('//article')
    return posts

def get_pattern_events(posts: list[html.Element]) -> list[models.Event]:
    """Return post in which is pattern to all bets."""
    pattern_events = []
    for post in posts:
        lines = list(
            filter(None, post.cssselect('.cPost_contentWrap')[0].text_content().split_lines()))
        c = re.compile(r'[Ww]z[oó]r\b')
        flist = [c.search(l) for l in lines if c.search(l) is not None]
        if flist:
            for i in range(lines.index(flist[0].string), len(lines)):
                try:
                    pattern_events.append(models.Event.parse_pattern_event(lines[i]))
                except Exception as e:
                    print(e)
                if lines[i] == '\xa0' or "Moje Typy:" in lines[i]:
                    break
            break
    return pattern_events

