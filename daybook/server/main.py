""" daybookd - this server holds the transactions.

The daybook client populates this server's ledger with load. Then this
server can return those transactions to a daybook client on subsequent
calls. This avoids loading transactions from disk for every query.
"""

import os
import sys
from collections import namedtuple
from xmlrpc.server import SimpleXMLRPCServer

import argcomplete

import daybook.server.parser
from daybook.Ledger import Ledger
from daybook.config import add_config_args, user_conf


class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password


# This ledger never reads from csvs - so we dont care about
# its primary currency.
ledger = Ledger(primary_currency='dont-care')
login = Login('', '')


def in_start(start, t):
    return not start or start <= t.date


def in_end(end, t):
    return not end or t.date <= end


def in_accounts(accounts, t):
    return not accounts or t.src in accounts or t.dest in accounts


def in_currencies(currencies, t):
    expected = [t.amount.src_currency, t.amount.dest_currency]
    return not currencies or len([c for c in currencies if c in expected]) > 0


def in_types(types, t):
    return not types or t.src.type in types or t.dest.type in types


def in_tags(tags, t):
    return not tags or len(tags.intersection(t.tags)) > 0


def filter_transaction(t, start, end, accounts, currencies, types, tags):
    """ Return True if transaction matches the criterion.

    Arguments that are None are treated as dont-cares.

    Args:
        t: The Transaction to test.
        start: Reject if t.date is earlier than this.
        end: Reject if t.date is later than this.
        accounts: Reject if t.src and t.dest are not in this.
        types: Reject t if neither involved account's type is in this.
        tags: Reject t if no tags intersect this.
    """
    return (
        in_start(start, t)
        and in_end(end, t)
        and in_accounts(accounts, t)
        and in_currencies(currencies, t)
        and in_types(types, t)
        and in_tags(tags, t))


def clear(username, password):
    if not username == login.username or not password == login.password:
        return 1

    ledger.clear()
    return 0


def dump(username, password, start, end, accounts, currencies, types, tags):
    """ Return filtered transactions.

    Arguments that are None are treated as dont-cares.

    Args:
        username: username for server.
        pasword: password for server.
        start: Grab transactions ocurring on or after this date.
        end: Grab transactions ocurring on or before this date.
        accounts: Filter for transactions involving the specified account
            names. Must be a space-separated string.
        types: Filter for transactions whose type is in this. Must be a space
            separated string.
        tags: Filter for transactions whose tags overlap this. Must be a colon
            separated string.
    """
    if not username == login.username or not password == login.password:
        return 1

    accounts = set(accounts.split()) if accounts else None
    currencies = list(currencies.split()) if currencies else None
    types = set(types.split()) if types else None
    tags = set(tags.split(':')) if tags else None

    return ledger.dump(lambda x: filter_transaction(
        x, start, end, accounts, currencies, types, tags))


def load(username, password, lines):
    if not username == login.username or not password == login.password:
        return 1

    ledger.load(lines)
    return 0


def ping():
    return 0


def main():

    parser = daybook.server.parser.create_server_parser()
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if not os.path.exists(user_conf) and not args.config:
        print('No user config found; run "daybook" first.')
        sys.exit(1)

    if not args.config:
        args.config = user_conf

    args = add_config_args(args, args.config)

    login.username = args.username
    login.password = args.password

    # Create server
    with SimpleXMLRPCServer(('localhost', int(args.port))) as server:

        server.register_function(clear, 'clear')
        server.register_function(dump, 'dump')
        server.register_function(load, 'load')
        server.register_function(ping, 'ping')

        # Run the server's main loop
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == '__main__':
    main()