from argparse import ArgumentParser

import getpass
import zipfile
from .env import *
from .tail import tail_logs
from .validations import validate_command

from colorama import init, deinit


def list_cmd_handler(args):
    raise NotImplementedError("not implemented yet")


def migrate_cmd_handler(args):
    print args.test
    raise NotImplementedError("not implemented yet")


def validate_cmd_handler(args):
    validate_command(args.target)


def get_env_password(env):
    env["password"] = getpass.getpass("{}@{} password: ".format(env["username"], env["server"]))


def tail_cmd_handler(args):
    project = get_project(args.project)
    env = get_environment(args.env, project)

    if not env["password"]:
        get_env_password(env)

    logfilters = args.filters.split(',')
    tail_logs(env["server"], env["username"], env["password"], logfilters, args.i)


parser = ArgumentParser(description="Demandware Tools")
parser.add_argument('-p', '--project', help="DWRE Project Name")
parser.add_argument('-e', '--env', help="DWRE Environment Name")

cmd_parser = parser.add_subparsers(title="Commands")

list_cmd = cmd_parser.add_parser('list', help="list DWRE environments")
list_cmd.set_defaults(func=list_cmd_handler)

tail_cmd = cmd_parser.add_parser('tail', help="tail logs")
tail_cmd.set_defaults(func=tail_cmd_handler)
tail_cmd.add_argument('-f', '--filters', help="logfile prefix filter [default 'warn,error,fatal']", default="warn,error,fatal")
tail_cmd.add_argument('-i', help="refresh interval in seconds [default 5]", default=5, type=int)

migrate_cmd = cmd_parser.add_parser('migrate', help="schema/data migrations")
migrate_cmd.set_defaults(func=migrate_cmd_handler)
migrate_cmd.add_argument('-n', dest="test", help="test run; do not execute migrations", action="store_true")
migrate_cmd.set_defaults(test=False)
migrate_cmd.add_argument('-d', '--dir', help="migrations directory (default: migrations)", default="migrations")
migrate_cmd.set_defaults(test=False)

validate_cmd = cmd_parser.add_parser('validate', help="XMLSchema validations")
validate_cmd.set_defaults(func=validate_cmd_handler)
validate_cmd.add_argument('target', help="filename or directory to validate")


def main():
    import os, sys
    init() # init colors
    if not os.isatty(sys.stdout.fileno()):
        deinit()

    args = parser.parse_args()
    load_config()
    if not args.project:
        (project_name, project) = get_default_project()
        args.project = project_name
    if not args.env:
        (env_name, creds) = get_default_environment(project)
        args.env = env_name

    args.func(args)
