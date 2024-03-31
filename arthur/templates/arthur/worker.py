import json
import logging
import os
import socket
import sys
import urllib.parse
import urllib.request
from collections import Counter
from functools import partial
from subprocess import run
from tempfile import TemporaryDirectory


SERVER_ROOT = '{{ SERVER_ROOT }}'
MAX_GAME_DEPTH = {{ MAX_GAME_DEPTH }}
DRAW_REPITITIONS = {{ DRAW_REPITITIONS }}

hostname = socket.gethostname()
worker_name = os.environ.get('ARTHUR_WORKER', hostname)


def server_request(path, data=None):
    logging.debug(f'Requesting {path}')

    request = urllib.request.Request(
        SERVER_ROOT + path,
        headers={
            'Arthur-Worker': worker_name,
        },
        data=urllib.parse.urlencode(data).encode() if data else None,
    )

    res = urllib.request.urlopen(request)
    data = json.load(res)
    logging.debug(f'Response {data}')

    return data


def check_prereqs():
    try:
        p = run(['git', 'version'], capture_output=True)
        logging.debug(p.stdout.decode().strip())
    except FileNotFoundError:
        logging.critical('Cannot run git!')
        sys.exit(1)


def work_loop():
    logging.info('Starting new loop')

    start_data = server_request('{% url "worker-start" %}')
    players = start_data['players']
    for player in players:
        player["tmpdir"] = TemporaryDirectory()

    # Build the engines
    for player in start_data['players']:
        logging.info(f'Building player {player["id"]}...')

        r = partial(run, cwd=player["tmpdir"].name, capture_output=True)
        # TODO it's inefficent to clone the repo twice every time we start a new game
        # perhaps clone it once to local filesystem, and then clone from there?
        # or somehow have the server send us the code instead? we might not need the whole history
        r(['git', 'clone', player['repository'], '.'])
        r(['git', 'checkout', player['commit']])
        # TODO defined build too? or standardized shell script?
        # perhaps make unless an optional build is given
        r(['make'], cwd=f'{player["tmpdir"].name}/src')

    state = start_data['state']

    logging.info(f'Playing game starting from {state}')
    # TODO break out after repititions of state?
    move_count = 0
    repititions = Counter()
    result = None
    while not result:
        repititions[state] += 1
        if repititions[state] == DRAW_REPITITIONS:
            result = 'draw'
            logging.debug(f'draw by repitition')
            break

        player = players.pop(0)
        players.append(player)

        logging.debug(f'Player {player["number"] + 1} (#{player["id"]}) moving from {state}')
        prev_state = state

        p = run(
            player['invocation'].split() + [state],
            cwd=f'{player["tmpdir"].name}/src',
            capture_output=True,
        )

        for line in p.stderr.decode().split('\n'):
            line = line.strip()
            if ':' in line:
                field, value = line.split(':', 1)
                field = field.strip().lower()
                value = value.strip()

                if field == 'next':
                    state = value

                elif field == 'result':
                    result = value.lower()

        # TODO send asynchronously to keep game progressing?
        # TODO check request result
        server_request('{% url "worker-log" %}', data={
            # TODO it should probably be named game, not game_id
            'game_id': start_data['game_id'],
            'player': player['id'],
            'number': move_count,
            'state': prev_state,
            'text': p.stderr.decode(),
        })

        move_count += 1
        if move_count == MAX_GAME_DEPTH:
            result = 'depth_out'
            logging.warning(f'Hit {MAX_GAME_DEPTH} moves; stopping game')
            break

    # TODO who wins if there are more than two players?
    # TODO check request result

    winner = player['id']

    if result == 'loss':
        winner = players.pop(0)['id']
        result = 'win'

    server_request('{% url "worker-finish" %}', data={
        'game_id': start_data['game_id'],
        'result': result,
        'winner': winner,
    })

    for player in players:
        player['tmpdir'].cleanup()


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s:\t%(message)s',
    )

    logging.info('Arthur worker startup')
    logging.debug(f'Server {SERVER_ROOT}')

    check_prereqs()

    while 1:
        work_loop()


if __name__ == '__main__':
    main()
