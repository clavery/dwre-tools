from argparse import ArgumentParser

import getpass
import zipfile
from .env import *
from .tail import tail_logs

def list_cmd_handler(args):
    print args.project
    print "\t", args.env


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

def main():
    args = parser.parse_args()
    load_config()
    if not args.project:
        (project_name, project) = get_default_project()
        args.project = project_name
    if not args.env:
        (env_name, creds) = get_default_environment(project)
        args.env = env_name
    args.func(args)
