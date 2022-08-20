"""sofa_pms contain parse function, which can parse matches data copied from sofa."""
import re
from datetime import datetime as dt

def parse_sofa_format(content: str):
    """Return list of match objects."""
    obiekty = []
    obiekt = {}
    state = 'data'
    for line in content.splitlines():
        if state == 'nowy obiekt':
            obiekty.append(obiekt)
            obiekt = {}
            state='data'
        elif state == 'data':
            data = re.match(r'(\d+)/(\d+)/(\d+)', line)
            if 'event_time' not in obiekt:
                obiekt['event_time'] = {}
            obiekt['event_time'].update({
                'day': int(data.group(1)),
                'month': int(data.group(2)),
                'year': int(data.group(3))
            })
            state = 'godzina'
        elif state =='godzina':
            godzina = re.match(r"(\d+):(\d+)", line)
            obiekt['event_time'].update({
                'hour': int(godzina.group(1)),
                'minute': int(godzina.group(2))
            })
            state = 'gospodarz'
        elif state == 'gospodarz':
            obiekt['home'] = line
            state='gosc'
        elif state == 'gosc':
            obiekt['away'] = line
            state='nowy obiekt'
    return obiekty

def parse_flash_format(content: str, date: dt):
    """This parser require outside information of data, cause can't be catch from text.
    Return list of match objects."""
    pattern_line = r"(\d+):(\d+)(.*) - (.*) -:-"
    compiled = re.compile(pattern_line)
    objects = []
    matches = content.splitlines()
    for match in matches:
        m = compiled.match(match)
        single_object = {}
        if not m:
            continue
        single_object = {
            "home": m.group(3),
            "away": m.group(4),
            "event_time": {
                "day": date.day,
                "month": date.month,
                "year": date.year,
                "hour": int(m.group(1)),
                "minute": int(m.group(2))
            }
        }
        objects.append(single_object)
    return objects
