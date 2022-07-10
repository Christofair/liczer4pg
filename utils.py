from lxml import html
import re
from datetime import datetime


def collect_posts_from_topic(topic_html_doc: str):
    """Return all post from topic.
    This is entry point of creating posts from string to html.Elements.
    Remove last post if it contains a results.
    """
    try:
        doc = html.document_fromstring(topic_html_doc)
    except Exception as e:
        print(e)
    posts: list[html.Element] = doc.xpath('//article')
    for post in posts:
        imgs = post.cssselect('.ipsColumn_fluid')[0].xpath('*//img')
        if any([re.search('.*wyniki.*png', img.get('alt')) for img in imgs]):
            posts.remove(post)
            break
    return posts

def get_post_timestamp(post):
    t = post.xpath('*//time')[0].get('datetime')
    if not t:
        t = post.xpath('*//time')[1].get('datetime')
    t = t.replace('T', ' ').rstrip('Z')
    return datetime.fromisoformat(t)
