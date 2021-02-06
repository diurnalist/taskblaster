from datetime import datetime, timedelta
from difflib import Differ
from itertools import chain
import logging
import os

import click
from dateutil.parser import parse as parse_date
from tabulate import tabulate

from .redmine import RedmineProject
from .trello import TrelloBoard
from .util import start_of_today, one_week_ago


CATEGORY_MAP = {
    "Appliances": "Appliances (technical debt)",
    "Operations": "Systems operations (technical debt)",
    "Outreach": "Outreach",
    "Testbed services": "Systems (development)",
    "User services": "Portal and User Services (technical debt)",
}

USER_MAP = {
    "zhenz-uchicago": "Zhuo Zhen",
}

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
@click.option("--trello-user", default=os.getenv("TRELLO_USER"))
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
    differ = Differ()

    high_priority = next(
        (p for p in redmine.list_priorities() if p.name == "High"), None)
    if not high_priority:
        raise ValueError("Could not find Redmine High priority enumeration")

    version = redmine.get_current_version()
    if not version:
        raise ValueError("Could not determine current Redmine version")

    categories = redmine.list_categories()
    members = redmine.list_members()

    all_cards = trello.cards_with_redmine_tickets(since=one_week_ago())
    click.echo(f"Will process {len(all_cards)} cards.\n")

    for c in all_cards:
        card = c["card"]  # type: trello.Card
        ticket_ref = c["ticket"].lower()

        card_category = trello.card_category(card)
        redmine_category = next((
            c for c in categories
            if c.name == CATEGORY_MAP[card_category]
        ), None)
        if not redmine_category:
            raise ValueError((
                "Could not find Redmine category for Trello category "
                f"'{card_category}'"))

        fields = dict(
            subject=card.name,
            description=card.description,
            # Always mark High
            priority=high_priority,
            category=redmine_category,
            fixed_version=version,
            # TODO: if checklist, calculate % done
            # done_ratio=0
        )

        def to_update_fields(fields):
            updates_with_ids = {}
            for field, value in fields.items():
                if hasattr(value, "id"):
                    updates_with_ids[f"{field}_id"] = value.id
                else:
                    updates_with_ids[field] = value
            return updates_with_ids

        if card.member_id:
            trello_user = trello.member(card.member_id[0])
            redmine_member = next((
                m.user for m in members
                if m.user.name in [
                    trello_user.full_name,
                    USER_MAP.get(trello_user.full_name, "not found")
                ]
            ), None)
            if not redmine_member:
                raise ValueError((
                    "Could not find Redmine user for Trello user "
                    f"'{trello_user.full_name}'"))
            fields["assigned_to"] = redmine_member

        if ticket_ref == "new":
            # 1. Create a new ticket
            ticket = redmine.create_ticket(**to_update_fields(fields))
            # 2. Update Trello card with ticket #
            continue

        ticket_id = int(ticket_ref)
        ticket = redmine.get_ticket(ticket_id)

        click.echo(f"#{ticket_id}: {ticket.subject}")
        updates = {}
        updates_summary = []
        for field, value in fields.items():
            ticket_value = getattr(ticket, field, None)
            value_norm = str(value).strip()
            ticket_value_norm = str(ticket_value).strip()
            if value_norm == ticket_value_norm:
                continue
            diff = '\n'.join(list(differ.compare(
                ticket_value_norm.splitlines(),
                value_norm.splitlines()
            )))
            if confirm:
                click.echo(tabulate([[field, diff]], tablefmt="plain"))
                if not click.confirm(f"Apply update to {field}?"):
                    continue
            updates[field] = value
            updates_summary.append([field, diff])

        if not updates:
            continue

        click.echo(tabulate(updates_summary, tablefmt="fancy_grid"))
        if click.confirm("Apply this update?"):
            updates_with_ids = {}
            for field, value in updates.items():
                if hasattr(value, "id"):
                    updates_with_ids[f"{field}_id"] = value.id
                else:
                    updates_with_ids[field] = value
            redmine.update_ticket(ticket_id, **updates_with_ids)
