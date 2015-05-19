import json
import os

DWRE_CONFIG = None
def load_config():
    global DWRE_CONFIG
    if not DWRE_CONFIG:
        home = os.path.expanduser("~")
        with open(os.path.join(home, ".dwre.json")) as f:
            dwre = json.load(f)
        DWRE_CONFIG = dwre
    return DWRE_CONFIG


def get_default_project_name():
    config = load_config()
    default_project = config.get('defaultProject')
    if not default_project and len(config["projects"].keys()) == 1:
        default_project = config["projects"].keys()[0]
    if default_project:
        return (default_project, config["projects"][default_project])
    return (None, None)


def get_default_environment_name(project):
    if not project:
        raise Exception("No default environment found in ~/.dwre.json")

    default_env = project.get('defaultEnvironment')
    if not default_env and len(project["environments"].keys()) == 1:
        default_env = project["environments"].keys()[0]
    if default_env:
        return (default_env, project["environments"][default_env])
    return (None, None)

def get_project(name):
    config = load_config()
    return config["projects"][name]

def get_environment(name, project):
    return project["environments"][name]
