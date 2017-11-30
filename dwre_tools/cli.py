from __future__ import print_function

from argparse import ArgumentParser

import sys
import getpass
import zipfile
from .env import *
from .tail import tail_logs
from .validations import validate_command
from .migrate import (add_migration, apply_migrations, validate_migrations, reset_migrations, 
        run_migration, set_migration, run_all)
from .index import reindex_command
from .export import export_command
from .sync import sync_command
from .webdav import copy_command
from .debugger import debug_command
from .cartridge import upgrade_bm_cartridge
from .cred import get_credential, get_credential_info, put_credential

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


def sync_cmd_handler(args):
    env = get_env_from_args(args)
    sync_command(env, args.delete)


def migrate_cmd_handler(args):

    result = 0
    if args.subcommand == "add":
        result = add_migration(args.directory, args.dir, args.id, args.description, rename=args.rename, hotfix=args.hotfix)
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
        result = run_migration(env, args.directory)
    elif args.subcommand == "runall":
        env = get_env_from_args(args)
        result = run_all(env, args.dir, args.test)
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


def debug_cmd_handler(args):
    env = get_env_from_args(args)
    debug_command(env, args.breakpoints)


def webdav_cmd_handler(args):
    if args.subcommand == "cp":
        env = get_env_from_args(args)
        copy_command(env, args.src, args.dest)


def upgrade_bm_cartridge_handler(args):
    upgrade_bm_cartridge()


def cred_cmd_handler(args):
    if args.subcommand == "get":
        get_credential(args.name)
    elif args.subcommand == "info":
        get_credential_info(args.name)
    elif args.subcommand == "put":
        put_credential(args.name, args.value, description=args.description)


parser = ArgumentParser(description="Demandware/SFCC Tools")
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

migrate_parser = migrate_cmd.add_subparsers(title="Sub Commands", dest='subcommand')
migrate_parser.required = True
migrate_add_cmd = migrate_parser.add_parser("add", help="add a new migration")
migrate_add_cmd.set_defaults(subcommand="add")
migrate_add_cmd.add_argument('-d', '--description', help="description of migration (default: empty)")
migrate_add_cmd.add_argument('-r', '--rename', dest="rename", help="rename folder to generated or specified ID", action="store_true")
migrate_cmd.set_defaults(rename=False)
migrate_add_cmd.add_argument('--hotfix', dest="hotfix", help="create migration as a hotfix", action="store_true")
migrate_cmd.set_defaults(hotfix=False)
migrate_add_cmd.add_argument('--id', help="id of migration (default: generated)")
migrate_add_cmd.add_argument('directory', help="migration directory (within migrations/)")
migrate_apply_cmd = migrate_parser.add_parser("apply", help="apply migrations to environment")
migrate_apply_cmd.set_defaults(subcommand="apply")
migrate_validate_cmd = migrate_parser.add_parser("validate", help="validate migrations directory")
migrate_validate_cmd.set_defaults(subcommand="validate")
migrate_reset_cmd = migrate_parser.add_parser("reset", help="reset migration state to current code version")
migrate_reset_cmd.set_defaults(subcommand="reset")
migrate_run_cmd = migrate_parser.add_parser("run", help="run a single site import without validating or updating migrations")
migrate_run_cmd.add_argument('directory', help="directory containing migration")
migrate_run_cmd.set_defaults(subcommand="run")
migrate_set_cmd = migrate_parser.add_parser("set", help="set the current migration version")
migrate_set_cmd.add_argument('name', help="migration name")
migrate_set_cmd.set_defaults(subcommand="set")
migrate_runall_cmd = migrate_parser.add_parser("runall", help="run all migrations not currently applied without validating or updating/applying migrations")
migrate_runall_cmd.set_defaults(subcommand="runall")

validate_cmd = cmd_parser.add_parser('validate', help="XMLSchema validations")
validate_cmd.set_defaults(func=validate_cmd_handler)
validate_cmd.add_argument('target', help="filename or directory to validate")

export_cmd = cmd_parser.add_parser('export', help="Site import/export helper")
export_cmd.set_defaults(func=export_cmd_handler)
export_cmd.add_argument('directory', help="destination directory")

update_cmd = cmd_parser.add_parser('update', help="Updates tools")
update_cmd.set_defaults(func=update_cmd_handler)

sync_cmd = cmd_parser.add_parser('sync', help="Sync cartridges from current directory")
sync_cmd.set_defaults(func=sync_cmd_handler)
sync_cmd.add_argument('-d', '--delete', dest="delete", help="delete code version first", action="store_true")

debug_cmd = cmd_parser.add_parser('debug', help="Begin an interactive debugging session")
debug_cmd.set_defaults(func=debug_cmd_handler)
debug_cmd.add_argument('breakpoints', metavar='breakpoint_locations', nargs='+',
                    help='path:line_num breakpoints')

webdav_cmd = cmd_parser.add_parser('webdav', help="webdav operations")
webdav_cmd.set_defaults(func=webdav_cmd_handler)
webdav_parser = webdav_cmd.add_subparsers(title="Sub Commands", dest='subcommand')
webdav_parser.required = True
webdav_cp_cmd = webdav_parser.add_parser("cp", help="Copy a file to/from the webdav location")
webdav_cp_cmd.add_argument('src', help="src file name")
webdav_cp_cmd.add_argument('dest', help="destination on webdav (relative to /on/demandware.servlet/webdav/Sites)")

upgrade_bm_cartridge_cmd = cmd_parser.add_parser('upgrade-bm-cartridge', help="upgrades the bm_dwremigrate cartridge to the latest version")
upgrade_bm_cartridge_cmd.set_defaults(func=upgrade_bm_cartridge_handler)

cred_cmd = cmd_parser.add_parser('cred', help="credential management")
cred_cmd.set_defaults(func=cred_cmd_handler)
cred_parser = cred_cmd.add_subparsers(title="Sub Commands", dest='subcommand')
cred_parser.required = True
cred_get_cmd = cred_parser.add_parser("get", help="get a credential")
cred_get_cmd.add_argument('name', help="credential name")
cred_info_cmd = cred_parser.add_parser("info", help="credential information")
cred_info_cmd.add_argument('name', help="credential name")
cred_put_cmd = cred_parser.add_parser("put", help="create or update credential")
cred_put_cmd.add_argument('-d', '--description', dest="description", help="credential description")
cred_put_cmd.add_argument('name', help="credential name")
cred_put_cmd.add_argument('value', help="new value")


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
