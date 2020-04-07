import argparse
from datetime import datetime
import logging
import os
import sys

from taskblaster.redmine import RedmineProject
from taskblaster.trello import TrelloBoard

logging.basicConfig(level=logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

parser = argparse.ArgumentParser(
    prog="taskblaster")
parser.add_argument("--trello-api-key", default=os.getenv("TRELLO_API_KEY"))
parser.add_argument("--trello-token", default=os.getenv("TRELLO_TOKEN"))
parser.add_argument("--trello-board")
parser.add_argument("--redmine-url", default=os.getenv("REDMINE_URL"))
parser.add_argument("--redmine-api-key", default=os.getenv("REDMINE_API_KEY"))
parser.add_argument("--redmine-project")

args = parser.parse_args(sys.argv[1:])

trello = TrelloBoard(api_key=args.trello_api_key, api_secret=args.trello_token,
                     board=args.trello_board)
redmine = RedmineProject(url=args.redmine_url,
                         api_key=args.redmine_api_key, 
                         project=args.redmine_project)

for c in trello.cards_with_redmine_tickets:
    print(redmine.ticket(c["ticket"]))
    # Look up ticket in redmine now.
