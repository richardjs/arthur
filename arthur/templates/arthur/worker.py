import json
import logging
import socket
import sys
import urllib.request
from functools import partial
from subprocess import run
from tempfile import TemporaryDirectory


SERVER_ROOT = '{{ SERVER_ROOT }}'
GET_REPO = '{{ GIT_REPO }}'

hostname = socket.gethostname()


def server_request(path):
    logging.debug(f'Requesting {path}')

    request = urllib.request.Request(
        SERVER_ROOT + path,
        headers={
            'Arthur-Hostname': hostname,
        },
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

    start = server_request('/worker/start')

    for player in start['players']:
        with TemporaryDirectory() as tmpdir:
            r = partial(run, cwd=tmpdir)
            r(['git', 'clone', GET_REPO, '.'])
            r(['git', 'checkout', player['commit']])
            # TODO defined build too? or standardized shell script?
            # perhaps make unless an optional build is given
            r(['make'], cwd=f'{tmpdir}/src')


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s:\t%(message)s',
    )

    logging.info('Arthur worker startup')
    logging.debug(f'Server {SERVER_ROOT}')
    logging.debug(f'Repo {GET_REPO}')

    check_prereqs()

    work_loop()


if __name__ == '__main__':
    main()
