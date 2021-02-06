#!/usr/bin/env bash
set -a; source .env; set +a

source .tox/py37/bin/activate

python -m taskblaster --trello-board PUntCdot "$@"
