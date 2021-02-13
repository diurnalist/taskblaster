from itertools import chain
import logging
import os

import click
from dateutil.parser import parse as parse_date

from .commands.sync import SyncToRedmineCommand
from .redmine import RedmineProject
from .trello import TrelloBoard
from .util import start_of_today, one_week_ago


@click.group()
@click.option("-v", "--verbose", "verbose", count=True)
@click.option("--trello-api-key", default=os.getenv("TRELLO_API_KEY"))
@click.option("--trello-token", default=os.getenv("TRELLO_TOKEN"))
@click.option("--trello-board", default=os.getenv("TRELLO_BOARD"))
@click.pass_context
def cli(ctx, verbose, trello_api_key, trello_token, trello_board):
    ctx.ensure_object(dict)

    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(log_level)
    requests_log.propagate = True

    ctx.obj['trello_client'] = TrelloBoard(api_key=trello_api_key,
                                           api_secret=trello_token,
                                           board=trello_board)


@cli.command("standup-report")
@click.argument("trello-user", default=os.getenv("TRELLO_USER"))
@click.pass_context
def standup_report(ctx, trello_user):
    username = trello_user
    trello = ctx.obj['trello_client']

    report_lines = ['*Today*']

    def format_comment(comm):
        text = comm["data"]["text"]
        return [
            f'- {line.strip().replace("- ", "")}'
            for line in text.split("\n")
            if line.strip()
        ]

    for c in trello.cards_for_member(username, since=one_week_ago()):
        card_updates = [
            com for com in c.get_comments()
            if (com['memberCreator']['username'] == username
                and parse_date(com['date']) > start_of_today())
        ]
        if not card_updates:
            continue
        report_lines += [
            f'\n_{c.name}_',
            *chain(*[format_comment(comm) for comm in card_updates]),
        ]

    print("\n".join(report_lines))


@cli.command("sync-to-redmine")
@click.option("--redmine-url", default=os.getenv("REDMINE_URL"))
@click.option("--redmine-api-key", default=os.getenv("REDMINE_API_KEY"))
@click.option("--redmine-project", default=os.getenv("REDMINE_PROJECT", "chameleon"))
@click.option("--confirm/--no-confirm", default=False)
@click.pass_context
def sync_to_redmine(ctx, redmine_url, redmine_api_key, redmine_project, confirm):
    trello = ctx.obj['trello_client']  # type: TrelloBoard
    redmine = RedmineProject(url=redmine_url, api_key=redmine_api_key,
                             project=redmine_project)
    cmd = SyncToRedmineCommand(redmine_client=redmine, trello_client=trello,
                               confirm=confirm)
    return cmd.run()
