from itertools import chain
import logging
import os

import click
from dateutil.parser import parse as parse_date
from trello import TrelloClient

from .commands.sync import SyncToRedmineCommand
from .redmine import RedmineProject
from .trello import TrelloBoard
from .util import start_of_today, one_week_ago


@click.group()
@click.option("-v", "--verbose", "verbose", count=True)
@click.option("--trello-api-key", default=os.getenv("TRELLO_API_KEY"))
@click.option("--trello-token", default=os.getenv("TRELLO_TOKEN"))
@click.pass_context
def cli(ctx, verbose, trello_api_key, trello_token):
    ctx.ensure_object(dict)

    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(log_level)
    requests_log.propagate = True

    ctx.obj['trello_client'] = TrelloClient(
        api_key=trello_api_key, api_secret=trello_token)


@cli.command("standup-report")
@click.argument("trello-user", default=os.getenv("TRELLO_USER"))
@click.option("--trello-board", default=os.getenv("TRELLO_BOARD"))
@click.pass_context
def standup_report(ctx, trello_user, trello_board):
    username = trello_user
    trello = TrelloBoard(ctx.obj['trello_client'], board=trello_board)

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
@click.option("--trello-board", default=[os.getenv("TRELLO_BOARD")], multiple=True)
@click.option("--confirm/--no-confirm", default=False)
@click.pass_context
def sync_to_redmine(ctx, redmine_url, redmine_api_key, redmine_project, trello_board, confirm):
    redmine = RedmineProject(url=redmine_url, api_key=redmine_api_key,
                             project=redmine_project)
    for board in trello_board:
        click.echo(click.style(f"Processing board {board}", fg="blue"))
        trello = TrelloBoard(ctx.obj['trello_client'], board=board)
        cmd = SyncToRedmineCommand(redmine_client=redmine, trello_client=trello,
                                   confirm=confirm)
        cmd.run()
