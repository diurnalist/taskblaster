from collections import namedtuple
from difflib import Differ
from textwrap import dedent, indent

import click
from tabulate import tabulate

from ..util import one_week_ago

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..redmine import RedmineProject
    from ..trello import TrelloBoard
    from redminelib.resources import Issue
    from trello import Card

RedmineContext = namedtuple("RedmineContext", [
    "high_priority", "version", "categories", "members"
])


class SyncToRedmineCommand(object):
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

    def __init__(self, redmine_client: "RedmineProject"=None,
                 trello_client: "TrelloBoard"=None, confirm=False):
        self.redmine = redmine_client
        self.trello = trello_client
        self.confirm = confirm
        self.redmine_data = self._redmine_context()

    def run(self):
        all_cards = self.trello.cards_with_redmine_tickets(since=one_week_ago())
        click.echo(f"Will process {len(all_cards)} cards.\n")

        for c in all_cards:
            card = c["card"]  # type: Card
            ticket_ref = c["ticket"].lower()
            self._process_card(card, ticket_ref)

    def _process_card(self, card, ticket_ref):
        fields = self._redmine_ticket_fields(card)

        if ticket_ref == "new":
            ticket = self._create_ticket(fields)
            self.trello.set_redmine_ticket(card, ticket.id)
        else:
            ticket_id = int(ticket_ref)
            ticket = self.redmine.get_ticket(ticket_id)  # type: Issue
            self._update_ticket(ticket, fields)

        self._add_notes(card, ticket)

    def _update_ticket(self, ticket: "Issue", fields):
        click.echo(f"\n#{ticket.id}: {ticket.subject}")
        updates = {}
        updates_summary = []
        for field, value in fields.items():
            ticket_value = getattr(ticket, field, None)
            # Normalize line endings
            value_norm = str(value).strip().replace("\r\n", "\n")
            ticket_value_norm = str(ticket_value).strip().replace("\r\n", "\n")
            if value_norm == ticket_value_norm:
                continue
            diff = '\n'.join(list(Differ().compare(
                ticket_value_norm.splitlines(),
                value_norm.splitlines()
            )))
            if self.confirm:
                click.echo(tabulate([[field, diff]], tablefmt="plain"))
                if not click.confirm(f"Apply update to {field}?"):
                    continue
            updates[field] = value
            updates_summary.append([field, diff])

        if not updates:
            click.echo(click.style("(skipped, no updates)", fg="bright_black"))
            return

        click.echo(tabulate(updates_summary, tablefmt="fancy_grid"))
        if click.confirm("Apply this update?"):
            updates_with_ids = {}
            for field, value in updates.items():
                if hasattr(value, "id"):
                    updates_with_ids[f"{field}_id"] = value.id
                else:
                    updates_with_ids[field] = value
            self.redmine.update_ticket(ticket.id, **updates_with_ids)

    def _create_ticket(self, fields) -> "Issue":
        click.echo(tabulate(fields.items(), tablefmt="fancy_grid"))
        if click.confirm("Create this ticket?"):
            ticket = self.redmine.create_ticket(
                **self._to_update_fields(fields))
            click.echo(f"\nCreated ticket {ticket.id}")
            return ticket
        return None

    def _add_notes(self, card: "Card", ticket: "Issue"):
        comments = card.get_comments()
        pending = [
            comment for comment in comments
            if not any(
                comment["id"] in getattr(item, "notes", "")
                for item in ticket.journals
            )
        ]

        if not pending:
            click.echo(click.style("(no new comments)", fg="bright_black"))
            return

        for comment in pending:
            member = comment["memberCreator"]
            note = dedent(f"""
            {member['fullName']} said at {comment['date']}:

            {indent(comment['data']['text'], '> ')}

            ~{comment['id']}~
            """)
            click.echo(note)
            if click.confirm("Add this note?"):
                self.redmine.update_ticket(ticket.id, notes=note)

    def _redmine_ticket_fields(self, card):
        # Always mark High
        priority = self.redmine_data.high_priority
        category = self._redmine_category(card)
        fields = dict(
            subject=card.name,
            description=card.description,
            priority=priority,
            category=category,
            # TODO: if checklist, calculate % done
            # done_ratio=0
        )

        if card.member_id:
            fields["assigned_to"] = self._redmine_member(card)

        if not self.trello.card_is_future(card):
            fields["fixed_version"] = self.redmine_data.version

        return fields

    def _redmine_category(self, card):
        card_category = self.trello.card_category(card)
        redmine_category = next((
            c for c in self.redmine_data.categories
            if c.name == self.CATEGORY_MAP[card_category]
        ), None)
        if not redmine_category:
            raise ValueError((
                "Could not find Redmine category for Trello category "
                f"'{card_category}'"))
        return redmine_category

    def _redmine_member(self, card):
        trello_user = self.trello.member(card.member_id[0])
        redmine_member = next((
            m.user for m in self.redmine_data.members
            if m.user.name in [
                trello_user.full_name,
                self.USER_MAP.get(trello_user.full_name, "not found")
            ]
        ), None)
        if not redmine_member:
            raise ValueError((
                "Could not find Redmine user for Trello user "
                f"'{trello_user.full_name}'"))
        return redmine_member

    def _to_update_fields(self, fields):
        updates_with_ids = {}
        for field, value in fields.items():
            if hasattr(value, "id"):
                updates_with_ids[f"{field}_id"] = value.id
            else:
                updates_with_ids[field] = value
        return updates_with_ids

    def _redmine_context(self):
        high_priority = next(
            (p for p in self.redmine.list_priorities() if p.name == "High"), None)
        if not high_priority:
            raise ValueError("Could not find Redmine High priority enumeration")

        version = self.redmine.get_current_version()
        if not version:
            raise ValueError("Could not determine current Redmine version")

        categories = self.redmine.list_categories()
        members = self.redmine.list_members()

        return RedmineContext(
            high_priority=high_priority,
            version=version,
            categories=categories,
            members=members
        )
