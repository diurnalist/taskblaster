from functools import lru_cache
from itertools import chain

from trello import TrelloClient
from trello import Board, CustomFieldDefinition, Member


class TrelloBoard:
    def __init__(self, api_key=None, api_secret=None, board=None):
        self.client = TrelloClient(
            api_key=api_key,
            api_secret=api_secret
        )
        self.board = board

    def current_cards(self, since=None, future_ok=False):
        board = self.client.get_board(self.board)
        lists = [l for l in board.open_lists() if (future_ok or l.name != "Future Sync")]
        if not lists:
            raise ValueError("Could not find any valid open lists")
        all_cards = list(chain(*[l.list_cards() for l in lists]))
        if since:
            return [c for c in all_cards if c.date_last_activity > since]
        else:
            return all_cards

    def cards_for_member(self, username, since=None):
        board = self.client.get_board(self.board)
        member_id = next(
            (m.id for m in board.all_members() if m.username == username), None)
        if not member_id:
            raise ValueError(f"Member {username} is not part of this board")
        return [c for c in self.current_cards(since=since) if member_id in c.member_id]

    def cards_with_redmine_tickets(self, since=None):
        with_tickets = []
        for c in self.current_cards(since=since, future_ok=True):
            ticket = self.redmine_ticket(c)
            if ticket:
                with_tickets.append(dict(card=c, ticket=ticket))
        return with_tickets

    def redmine_ticket(self, card):
        fields = [f for f in card.customFields if f.name == "Redmine Ticket"]

        if fields:
            return fields[0].value
        else:
            return None

    def categories(self):
        return [o.value for o in self._category_field.options]

    def card_category(self, card) -> str:
        custom_field_item = next((
            cf for cf in card.custom_fields
            if cf.definition_id == self._category_field.id
        ), None)
        if not custom_field_item:
            raise ValueError(f"Could not find category for card {card}")
        return custom_field_item.value

    def member(self, member_id):
        return next((m for m in self._members if m.id == member_id), None)

    @property
    @lru_cache(maxsize=1)
    def _category_field(self) -> 'CustomFieldDefinition':
        category_field = next((
            fd for fd in self._board.get_custom_field_definitions()
            if fd.name == "Category"
        ), None)
        if not category_field:
            raise ValueError("Could not find 'Category' custom field")
        return category_field

    @property
    @lru_cache(maxsize=1)
    def _members(self) -> 'list[Member]':
        return self._board.all_members()

    @property
    @lru_cache(maxsize=1)
    def _board(self) -> Board:
        return self.client.get_board(self.board)
