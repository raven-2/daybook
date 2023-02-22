import os
from argparse import RawDescriptionHelpFormatter
from pathlib import Path

from daybook.client.parsergroups import create_csv_opts, create_filter_opts, create_server_opts
from daybook.client.cli.report.main import import_reporters


presets_base = f'{Path.home()}/.local/usr/share/daybook/presets'
default_presets = f'{os.getcwd()}:{presets_base}/report'


def add_reporter_subparsers(subparsers, parents):

    if 'DAYBOOK_REPORTERS' not in os.environ:
        os.environ['DAYBOOK_REPORTERS'] = default_presets

    paths = os.environ['DAYBOOK_REPORTERS'].split(':')

    reporters = import_reporters(paths)
    reporters = {k: reporters[k] for k in sorted(reporters)}

    for name, tupe in reporters.items():
        help, description, _, _ = tupe
        description = '\n'.join([help, '', description])
        sp = subparsers.add_parser(
            name, help=help, description=description,
            parents=parents, formatter_class=RawDescriptionHelpFormatter)

        sp.add_argument('-b', '--budgets', help='List of budget files.', nargs='*')


def add_subparser(subparsers):
    csv_opts = create_csv_opts()
    filter_opts = create_filter_opts()
    server_opts = create_server_opts()

    desc = f"""
    The report subcommand generates reports by sending transactions to a
    reporter module. This module may be one listed below, or a path to an
    module on the filesystem.

    The reporter modules are found in the locations specified by the
    DAYBOOK_REPORTERS environment variable. If this variable is not set
    then it defaults to ./:$HOME/.local/usr/share/daybook/presets/report

    See the manpage for daybook-report for details on writing custom
    reporters.
    """.splitlines()
    desc = '\n'.join([x.strip() for x in desc])

    sp = subparsers.add_parser(
        'report',
        help='Display reports.',
        description=desc,
        formatter_class=RawDescriptionHelpFormatter)

    reporters = sp.add_subparsers(
        metavar='reporter',
        dest='reporter',
        description='Available reporters. Each has its own [-h, --help] statement.')

    add_reporter_subparsers(reporters, [csv_opts, server_opts, filter_opts])
