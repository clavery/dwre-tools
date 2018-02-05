from __future__ import print_function

from .env import load_config
import sys


def pw_list():
    hosts, _ = get_dwre_hosts()
    for a in hosts:
        print(a.get("account_name"))


def pw_get(account_name):
    _, hosts_by_name = get_dwre_hosts()
    host = hosts_by_name.get(account_name)

    print(host.get('password'), end='')
    print(host.get('extra'), file=sys.stderr)


def get_dwre_hosts():
    hosts = []
    hosts_by_name = {}

    j = load_config()
    for project_name, p in j.get('projects').items():
        for env_name, e in p.get('environments').items():
            name = "%s-%s" % (project_name, env_name)
            extra = "https://%s@%s/on/demandware.store/Sites-Site/" % (
                e.get("username"), e.get("server"))
            account = {"account_name": name,
                       "extra": extra,
                       "username": e.get("username"),
                       "password": e.get("password")}
            hosts.append(account)
            hosts_by_name[name] = account
    return hosts, hosts_by_name
