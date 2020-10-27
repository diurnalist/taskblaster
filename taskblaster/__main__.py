import argparse
from datetime import datetime
import logging
import os
import pytz
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


def standup_report():
    username = 'jasonandersonatuchicago'
    start_of_today = datetime.utcnow().replace(
        hour=0, minute=0, second=0, tzinfo=pytz.timezone('America/Chicago'))
    report_lines = ['*Today*']
    def format_comment(comm):
        text = comm["data"]["text"]
        return text.replace("\n", " ")
    for c in trello.cards_for_member(username):
        if c.date_last_activity > start_of_today:
            comments = [
                com for com in c.get_comments()
                if com['memberCreator']['username'] == username
            ]
            report_lines += [
                f'\n_{c.name}_',
                *[f'  * {format_comment(comm)}' for comm in comments],
            ]
    print("\n".join(report_lines))


def sync_to_redmine():
    # priorities = redmine.list_priorities()
    # categories = redmine.list_categories()
    version = redmine.get_current_version()

    for c in trello.cards_with_redmine_tickets:
        card = c["card"]
        fields = dict(
            subject=card.name,
            description=card.description,
            # Always mark High
            priority_id=5,
            # Map from Trello to Redmine categories
            category_id=0,
            # Always put to latest version
            fixed_version_id=version.internal_id,
            # Map from Trello to Redmine users
            assigned_to_id=0,
            # If checklist, calculate % done
            done_ratio=0
        )

        print(fields)

        if c["ticket"].lower() == "new":
            # Create a new ticket
            # ticket = redmine.create_ticket(**fields)
            # Update Trello card with ticket #
            continue

        # Check what will be done
        # Update existing ticket
        # redmine.update_ticket(c["ticket"], **fields)

standup_report()
