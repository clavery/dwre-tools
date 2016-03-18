from __future__ import print_function

from argparse import ArgumentParser

import sys
import getpass
import zipfile
from .env import *
from .tail import tail_logs
from .validations import validate_command
from .migrate import (add_migration, apply_migrations, validate_migrations, reset_migrations, 
        run_migration, set_migration)
from .index import reindex_command
from .export import export_command

from colorama import init, deinit

def version():
    import pkg_resources
    return pkg_resources.require("dwre-tools")[0].version


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
    elif "clientcert" in env:
        env["cert"] = (env["clientcert"], env["clientkey"],)
    else:
        env["cert"] = None

    if "verify" not in env:
        env["verify"] = not args.noverify

    if not env["password"]:
        get_env_password(env)

    return env


def list_cmd_handler(args):
    raise NotImplementedError("not implemented yet")


def migrate_cmd_handler(args):

    result = 0
    if args.subcommand == "add":
        result = add_migration(args.directory, args.dir, args.id, args.description, rename=args.rename)
    elif args.subcommand == "apply":
        env = get_env_from_args(args)
        result = apply_migrations(env, args.dir, args.test)
    elif args.subcommand == "validate":
        result = validate_migrations(args.dir)
    elif args.subcommand == "reset":
        env = get_env_from_args(args)
        result = reset_migrations(env, args.dir, args.test)
    elif args.subcommand == "run":
        env = get_env_from_args(args)
        result = run_migration(env, args.dir, args.name)
    elif args.subcommand == "set":
        env = get_env_from_args(args)
        result = set_migration(env, args.dir, args.name)

    if result is False:
        sys.exit(1)


def validate_cmd_handler(args):
    validate_command(args.target)


def export_cmd_handler(args):
    env = get_env_from_args(args)
    export_command(env, args.directory)


def reindex_cmd_handler(args):
    env = get_env_from_args(args)
    result = reindex_command(env)
    if result is False:
        sys.exit(1)


def get_env_password(env):
    env["password"] = getpass.getpass("{}@{} password: ".format(env["username"], env["server"]))


def tail_cmd_handler(args):
    env = get_env_from_args(args)
    logfilters = args.filters.split(',')
    tail_logs(env, logfilters, args.i)

def update_cmd_handler(args):
    os.system("pip install https://devops-pixelmedia-com.s3.amazonaws.com/packages-374e8dc7/dwre-tools-latest.zip")


parser = ArgumentParser(description="Demandware Tools")
parser.add_argument('-p', '--project', help="DWRE Project Name")
parser.add_argument('-e', '--env', help="DWRE Environment Name")
parser.add_argument('--server', help="DWRE server name; overrides env settings")
parser.add_argument('--username', help="DWRE server username; overrides env settings")
parser.add_argument('--password', help="DWRE server password; overrides env settings")
parser.add_argument('--clientcert', help="SSL Client certificate")
parser.add_argument('--clientkey', help="SSL Client private key")
parser.add_argument('--noverify', help="Don't verify server cert", action="store_true")

version_str = version()
parser.add_argument('--version', action='version', version=version_str)
parser.set_defaults(noverify=False)

cmd_parser = parser.add_subparsers(title="Commands")

list_cmd = cmd_parser.add_parser('list', help="list DWRE environments")
list_cmd.set_defaults(func=list_cmd_handler)

reindex_cmd = cmd_parser.add_parser('reindex', help="rebuild search indexes on environment")
reindex_cmd.set_defaults(func=reindex_cmd_handler)

tail_cmd = cmd_parser.add_parser('tail', help="tail logs")
tail_cmd.set_defaults(func=tail_cmd_handler)
tail_cmd.add_argument('-f', '--filters', help="logfile prefix filter [default 'warn,error,fatal,customerror,customfatal']", default="warn,error,fatal,customerror,customfatal")
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
migrate_set_cmd = migrate_parser.add_parser("set", help="set the current migration version")
migrate_set_cmd.add_argument('name', help="migration name")
migrate_set_cmd.set_defaults(subcommand="set")

validate_cmd = cmd_parser.add_parser('validate', help="XMLSchema validations")
validate_cmd.set_defaults(func=validate_cmd_handler)
validate_cmd.add_argument('target', help="filename or directory to validate")

export_cmd = cmd_parser.add_parser('export', help="Site import/export helper")
export_cmd.set_defaults(func=export_cmd_handler)
export_cmd.add_argument('directory', help="destination directory")

update_cmd = cmd_parser.add_parser('update', help="Updates tools")
update_cmd.set_defaults(func=update_cmd_handler)

def main():
    import os, sys
    init() # init colors
    if not os.isatty(sys.stdout.fileno()):
        deinit()

    # disbale insecure warnings (we know because we explicitly ask to verify)
    import requests
    requests.packages.urllib3.disable_warnings()

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(2)
