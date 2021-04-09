from functools import lru_cache
from itertools import chain

from trello import TrelloClient
from trello import Board, Card, CustomFieldDefinition, Member

FUTURE_LIST = "Future Sync"
FUTURE_BOARD = "Product Roadmap"

class TrelloBoard:
    def __init__(self, client: "TrelloClient", board=None):
        self.client = client
        self.board = board

    def current_cards(self, since=None, future_ok=False):
        board = self.client.get_board(self.board)
        lists = [l for l in board.open_lists() if (future_ok or l.name != FUTURE_LIST)]
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

    def redmine_ticket(self, card: "Card"):
        redmine_ticket_field = card.get_custom_field_by_name("Redmine Ticket")
        return redmine_ticket_field.value if redmine_ticket_field else None

    def set_redmine_ticket(self, card: "Card", ticket_id):
        return card.set_custom_field(
            str(ticket_id), self._redmine_ticket_field)

    def categories(self):
        return [o.value for o in self._category_field.options]

    def card_category(self, card: "Card") -> str:
        custom_field_item = next((
            cf for cf in card.custom_fields
            if cf.definition_id == self._category_field.id
        ), None)
        if not custom_field_item:
            raise ValueError(f"Could not find category for card {card}")
        return custom_field_item.value

    def card_is_future(self, card: "Card") -> bool:
        board = self.client.get_board(self.board)
        return board.name == FUTURE_BOARD or card.get_list().name == FUTURE_LIST

    def card_is_done(self, card: "Card") -> bool:
        return any(l.name == "Done" for l in (card.labels or []))

    def card_is_bug(self, card: "Card") -> bool:
        return any(l.name == "Bug" for l in (card.labels or []))

    def member(self, member_id):
        return next((m for m in self._members if m.id == member_id), None)

    @property
    @lru_cache(maxsize=1)
    def _category_field(self) -> 'CustomFieldDefinition':
        category_field = next((
            field for field in self._custom_fields
            if field.name.lower() == "category"
        ), None)
        if not category_field:
            raise ValueError("Could not find 'Category' custom field")
        return category_field

    @property
    @lru_cache(maxsize=1)
    def _redmine_ticket_field(self) -> 'CustomFieldDefinition':
        redmine_ticket_field = next((
            field for field in self._custom_fields
            if field.name.lower() == "redmine ticket"
        ), None)
        if not redmine_ticket_field:
            raise ValueError("Could not find 'Redmine Ticket' custom field")
        return redmine_ticket_field

    @property
    @lru_cache(maxsize=1)
    def _custom_fields(self):
        return self._board.get_custom_field_definitions()

    @property
    @lru_cache(maxsize=1)
    def _members(self) -> 'list[Member]':
        return self._board.all_members()

    @property
    @lru_cache(maxsize=1)
    def _board(self) -> Board:
        return self.client.get_board(self.board)
