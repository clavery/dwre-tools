from __future__ import print_function

from argparse import ArgumentParser

import sys
import getpass
import zipfile
from .env import *
from .tail import tail_logs
from .validations import validate_command
from .migrate import add_migration, apply_migrations, validate_migrations, reset_migrations, run_migration

from colorama import init, deinit


def get_env_from_args(args):
    if not args.server:
        if not args.project:
            (project_name, project) = get_default_project()
            args.project = project_name
        else:
            project = get_project(args.project)

        if not args.env:
            (env_name, env) = get_default_environment(project)
            args.env = env_name
        else:
            env = get_environment(args.env, project)
    else:
        assert args.username, "Must specify a username"
        env = {
            "server" : args.server,
            "username" : args.username,
            "password" : args.password
        }

    if args.clientcert:
        assert args.clientkey, "must specify a private key with certificate"
        env["clientcert"] = args.clientcert
        env["clientkey"] = args.clientkey
        env["cert"] = (args.clientcert, args.clientkey,)
    else:
        env["cert"] = None

    env["verify"] = not args.noverify

    if not env["password"]:
        get_env_password(env)

    return env


def list_cmd_handler(args):
    raise NotImplementedError("not implemented yet")


def migrate_cmd_handler(args):
    env = get_env_from_args(args)

    result = 0
    if args.subcommand == "add":
        result = add_migration(args.directory, args.dir, args.id, args.description, rename=args.rename)
    elif args.subcommand == "apply":
        result = apply_migrations(env, args.dir, args.test)
    elif args.subcommand == "validate":
        result = validate_migrations(args.dir)
    elif args.subcommand == "reset":
        result = reset_migrations(env, args.dir, args.test)
    elif args.subcommand == "run":
        result = run_migration(env, args.dir, args.name)

    if result is False:
        sys.exit(1)


def validate_cmd_handler(args):
    validate_command(args.target)


def get_env_password(env):
    env["password"] = getpass.getpass("{}@{} password: ".format(env["username"], env["server"]))


def tail_cmd_handler(args):
    env = get_env_from_args(args)
    logfilters = args.filters.split(',')
    tail_logs(env, logfilters, args.i)


parser = ArgumentParser(description="Demandware Tools")
parser.add_argument('-p', '--project', help="DWRE Project Name")
parser.add_argument('-e', '--env', help="DWRE Environment Name")
parser.add_argument('--server', help="DWRE server name; overrides env settings")
parser.add_argument('--username', help="DWRE server username; overrides env settings")
parser.add_argument('--password', help="DWRE server password; overrides env settings")
parser.add_argument('--clientcert', help="SSL Client certificate")
parser.add_argument('--clientkey', help="SSL Client private key")
parser.add_argument('--noverify', help="Don't verify server cert", action="store_true")
parser.set_defaults(noverify=False)

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

migrate_parser = migrate_cmd.add_subparsers(title="Sub Commands")
migrate_add_cmd = migrate_parser.add_parser("add", help="add a new migration")
migrate_add_cmd.set_defaults(subcommand="add")
migrate_add_cmd.add_argument('-d', '--description', help="description of migration (default: empty)")
migrate_add_cmd.add_argument('-r', '--rename', dest="rename", help="rename folder to generated or specified ID", action="store_true")
migrate_cmd.set_defaults(rename=False)
migrate_add_cmd.add_argument('--id', help="id of migration (default: generated)")
migrate_add_cmd.add_argument('directory', help="migration directory")
migrate_apply_cmd = migrate_parser.add_parser("apply", help="apply migrations to environment")
migrate_apply_cmd.set_defaults(subcommand="apply")
migrate_validate_cmd = migrate_parser.add_parser("validate", help="validate migrations directory")
migrate_validate_cmd.set_defaults(subcommand="validate")
migrate_reset_cmd = migrate_parser.add_parser("reset", help="reset migration state to current code version")
migrate_reset_cmd.set_defaults(subcommand="reset")
migrate_run_cmd = migrate_parser.add_parser("run", help="run a single migration without updating version")
migrate_run_cmd.add_argument('name', help="migration name")
migrate_run_cmd.set_defaults(subcommand="run")

validate_cmd = cmd_parser.add_parser('validate', help="XMLSchema validations")
validate_cmd.set_defaults(func=validate_cmd_handler)
validate_cmd.add_argument('target', help="filename or directory to validate")


def main():
    import os, sys
    init() # init colors
    if not os.isatty(sys.stdout.fileno()):
        deinit()

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(2)
