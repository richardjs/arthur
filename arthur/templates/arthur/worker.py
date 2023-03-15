import json
import logging
import socket
import sys
import urllib.parse
import urllib.request
from functools import partial
from subprocess import run
from tempfile import TemporaryDirectory


SERVER_ROOT = '{{ SERVER_ROOT }}'
MAX_GAME_DEPTH = {{ MAX_GAME_DEPTH }}

hostname = socket.gethostname()


def server_request(path, data=None):
    logging.debug(f'Requesting {path}')

    request = urllib.request.Request(
        SERVER_ROOT + path,
        headers={
            'Arthur-Hostname': hostname,
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
    result = None
    while not result:
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

        # TODO send log to server (in a separate thread, to keep game progressing?)

        move_count += 1
        if move_count == MAX_GAME_DEPTH:
            logging.warning(f'Hit {MAX_GAME_DEPTH} moves; stopping game')
            break

    # TODO do we support result: loss conditions? who wins if there are more than two players?
    server_request('{% url "worker-finish" %}', data={
        'game_id': start_data['game_id'],
        'result': result,
        'winner': player['id'],
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

    work_loop()


if __name__ == '__main__':
    main()
