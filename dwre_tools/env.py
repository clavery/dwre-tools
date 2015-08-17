import json
import os

def load_config():
    home = os.path.expanduser("~")
    with open(os.path.join(home, ".dwre.json")) as f:
        return json.load(f)

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
