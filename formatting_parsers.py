"""sofa_pms contain parse function, which can parse matches data copied from sofa."""
import re
from datetime import datetime as dt
from copy import deepcopy

def parse_sofa_format(content: str):
    """Return list of match objects."""
    td = dt.today()
    # initial object specifies an interface too
    initial_object = {
        'event_time':{'hour': -1, 'minute': -1, 'day': td.day, 'month': td.month, 'year': td.year},
        'home': None,
        'away': None
    }
    obiekt = deepcopy(initial_object)
    obiekty = []
    for line in content.splitlines():
        if line.strip() == '':
            if (obiekt['home'] is not None and obiekt['away'] is not None and
                    obiekt['event_time']['hour'] != -1 and obiekt['event_time']['minute'] != -1):
                obiekty.append(obiekt)
                obiekt = deepcopy(initial_object)
        elif data := re.match(r'(\d+)[-/.](\d+)[-/.](\d+)', line):
            obiekt['event_time'].update({
                'day': int(data.group(1)),
                'month': int(data.group(2)),
                'year': int(data.group(3)),
                'hour': obiekt['event_time']['hour'],
                'minute': obiekt['event_time']['minute']
            })
        elif godzina := re.match(r"(\d+):(\d+)", line):
            obiekt['event_time'].update({
                'day': obiekt['event_time']['day'],
                'month': obiekt['event_time']['month'],
                'year': obiekt['event_time']['year'],
                'hour': int(godzina.group(1)),
                'minute': int(godzina.group(2))
            })
        else:
            if obiekt['home'] is None:
                obiekt.update({'home': line})
            else:
                obiekt.update({'away': line})
    if obiekt not in obiekty:
        if (obiekt['home'] is not None and obiekt['away'] is not None and
                obiekt['event_time']['hour'] != -1 and obiekt['event_time']['minute'] != -1):
            obiekty.append(obiekt)
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
