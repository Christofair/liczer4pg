import re
import sys
import requests
import models
import utils

# load config file with pattern events

def count(winners_by_user, results_winners):
    wspolni = set(winners_by_user).intersection(set(results_winners))
    return 2*len(wspolni)  # obliczenie po dwa punkty za kazde trafienie.

if __name__ == "__main__":
    try:
        command = sys.argv[1]
    except IndexError:
        print('you have to enter a command as first argument')
        exit(-1)
    if command == 'get' or command == 'GET':
        if len(sys.argv) < 3:
            print('not enough arguments')
            exit(-1)
        topic_link = sys.argv[2]
        response = requests.get(topic_link)
        assert response.status_code == 200
        topic_doc = response.content.decode("utf-8")
        posts = utils.collect_posts_from_topic(topic_doc)
        events = models.Event.get_pattern_events(posts)
        with open('events_mlb.txt', 'w', encoding='utf-8') as mlbf:
            for event in events:
                mlbf.write("{}: {} VS {}; WINNER=\n".format(event.start_time.isoformat(),
                                                           event.home_team, event.away_team))
        with open('bets.txt', 'w', encoding='utf-8') as bsf:
            for post in posts:
                typer = models.Typer(utils.get_post_owner(post), post)
                typer.load_bet(kind='winner', pattern_events=events)
                bsf.write("TYPER={}\n".format(typer.name))
                for event in typer.bet.events:
                    bsf.write("WINNER={}\n".format(event.winner))

    if command == 'COUNT' or command == 'count':
        # loading winners
        winners = []
        tickets = []
        typer_ticket = []
        with open('events_mlb.txt', 'r', encoding='utf-8') as results:
            for line in results.read().splitlines():
                winner = re.search(r"WINNER=(.*)\b", line).group(1)
                if winner is None:
                    raise ValueError("Error loading winner")
                winners.append(winner)

        with open('bets.txt', 'r', encoding='utf-8') as mlbf:
            lines = mlbf.read().splitlines()
            while lines:
                typer_ticket.clear() #  czyszczenie kuponu usera
                # szukanie nazwy usera
                typername = re.search(r'TYPER=(.*)\b', lines[0])
                if typername is not None:
                    typername = typername.group(1)
                    typer_ticket.append(typername)  # dodanie nazwy typera na poczatku
                    lines.pop(0)  # wyrzucenie lini z nazwą
                    for line in lines[:]:
                        # szukanie nazwy zwyciezcy
                        winner = re.search(r"WINNER=(.*)\b", line)
                        # nie znaleziono przerwij bo pewnie linia z nazwa typera
                        if winner is None:
                            break
                        # dalej jednak winner wiec usun juz te linie
                        lines.remove(line)
                        # dodaj do kuponu usera
                        typer_ticket.append(winner.group(1))
                tickets.append(typer_ticket.copy())
        # w tym miejscu mamy wszystkie kupony na liście tickets.
        # i dla kazdego ticket
        for ticket in tickets:
            print("{} got {}".format(ticket[0], count(ticket[1:], winners)))
