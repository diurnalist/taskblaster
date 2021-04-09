#!/usr/bin/env bash
set -a; source .env; set +a

source .tox/py37/bin/activate

export TRELLO_BOARD=PUntCdot
python -m taskblaster "$@"
