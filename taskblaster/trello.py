from trello import TrelloClient
from itertools import chain

class TrelloBoard:
    def __init__(self, api_key=None, api_secret=None, board=None):
        self.client = TrelloClient(
            api_key=api_key,
            api_secret=api_secret
        )
        self.board = board

    def current_cards(self, since=None):
        board = self.client.get_board(self.board)
        lists = [l for l in board.open_lists() if l.name != "Future Sync"]
        if not lists:
            raise ValueError("Could not find any valid open lists")
        return list(chain(*[l.list_cards() for l in lists]))

    def cards_for_member(self, username, since=None):
        board = self.client.get_board(self.board)
        member_id = next(iter([
            m.id for m in board.all_members() if m.username == username
        ]), None)
        if not member_id:
            raise ValueError(f"Member {username} is not part of this board")
        return [c for c in self.current_cards(since=since) if member_id in c.member_id]

    @property
    def cards_with_redmine_tickets(self):
        with_tickets = []
        for c in self.current_cards:
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
