from __future__ import print_function

import json
import os
import sys


def load_config():
    home = os.path.expanduser("~")
    if os.path.exists(os.path.join(home, ".dwre.json.gpg")):
        try:
            import gnupg
            gpg = gnupg.GPG(use_agent=True)
        except ImportError as e:
            print("You must have gnupg installed: pip install python-gnupg", file=sys.stderr)
            print("You must have GNUpg installed and the following python module: pip install python-gnupg", file=sys.stderr)
            sys.exit(1)
        with open(os.path.join(home, ".dwre.json.gpg"), 'rb') as f:
            decrypted = gpg.decrypt_file(f)
            if decrypted.ok:
                return json.loads(str(decrypted))
            else:
                raise RuntimeError(decrypted.status)
    else:
        with open(os.path.join(home, ".dwre.json")) as f:
            return json.load(f)


def save_config(config):
    config_data = json.dumps(config, indent=2)
    home = os.path.expanduser("~")
    if os.path.exists(os.path.join(home, ".dwre.json.gpg")):
        try:
            import gnupg
            gpg = gnupg.GPG(use_agent=True)
        except ImportError as e:
            print("You must have gnupg installed: pip install python-gnupg", file=sys.stderr)
            print("You must have GNUpg installed and the following python module: pip install python-gnupg", file=sys.stderr)
            sys.exit(1)
        with open(os.path.join(home, ".dwre.json.gpg"), 'wb') as f:
            encrypted = gpg.encrypt(config_data, ['B050C1999B5B4181'])
            if encrypted.ok:
                f.write(encrypted.data)
            else:
                raise RuntimeError(encrypted.status)
    else:
        with open(os.path.join(home, ".dwre.json"), 'wb') as f:
            f.write(config_data.encode('utf-8'))
    pass


def get_default_project():
    config = load_config()
    default_project = config.get('defaultProject')
    if not default_project and len(list(config["projects"].keys())) == 1:
        default_project = list(config["projects"].keys())[0]
    if default_project:
        return (default_project, config["projects"][default_project])
    return (None, None)


def get_default_environment(project):
    if not project:
        raise Exception("No default environment found in ~/.dwre.json")

    default_env = project.get('defaultEnvironment')
    if not default_env and len(list(project["environments"].keys())) == 1:
        default_env = list(project["environments"].keys())[0]
    if default_env:
        return (default_env, project["environments"][default_env])
    return (None, None)


def get_project(name):
    config = load_config()
    return config["projects"][name]


def get_environment(name, project):
    return project["environments"][name]
