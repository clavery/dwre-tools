from __future__ import print_function

import requests
import zipfile
import io
import re
import time
from datetime import datetime
import pyquery

try:
    import _thread as thread
except ImportError:
    import thread

import os
from lxml import etree as ET
from lxml.builder import ElementMaker
from collections import defaultdict

from colorama import Fore, Back, Style

from .validations import validate_xml, validate_file, validate_directory
from .migratemeta import TOOL_VERSION, BOOTSTRAP_META, PREFERENCES, VERSION, SKIP_METADATA_CHECK_ON_UPGRADE
from .bmtools import get_current_versions, login_business_manager, wait_for_import
from .utils import directory_to_zip


X = "{http://www.pixelmedia.com/xml/dwremigrate}"


def get_bootstrap_zip():
    dest_file = "DWREMigrateBootstrap_v{}".format(TOOL_VERSION)

    bootstrap_package_file = io.BytesIO()
    bootstrap_package_zip = zipfile.ZipFile(bootstrap_package_file, "w")

    bootstrap_package_zip.writestr("{}/version.txt".format(dest_file), VERSION)
    bootstrap_package_zip.writestr("{}/preferences.xml".format(dest_file), PREFERENCES)
    bootstrap_package_zip.writestr("{}/meta/system-objecttype-extensions.xml".format(dest_file), BOOTSTRAP_META)
    bootstrap_package_zip.close()

    return bootstrap_package_file


def find_path(graph, start, path=None):
    if path is None:
        path = []
    else:
        path = path + [start]

    if start not in graph:
        return path

    for node in graph[start]:
        if node not in path:
            newpath = find_path(graph, node, path)
            if newpath: return newpath
            else: return path
    return None


def get_path(current_migration, migrations):
    migration_nodes = defaultdict(list)
    return []


def get_migrations(migrations_context):
    migrations = []
    migration_nodes = defaultdict(list)
    migration_data = {}
    for migration in migrations_context.getroot():
        id = migration.attrib["id"]
        location = migration.find(X + "location").text
        description_el = migration.find(X + "description")
        parent_el = migration.find(X + "parent")

        description = ""
        if description_el is not None:
            description = description_el.text

        assert id not in migration_data, "Migration %s already exists" % id
        migration_data[id] = {"id": id, "location" : location, "description": description}
        if parent_el is not None:
            migration_nodes[parent_el.text].append(id)
        else:
            migration_nodes[None].append(id)

    if len(list(migration_data.keys())) == 0:
        return migrations

    # validate root exists
    assert migration_nodes[None], "Cannot find root migration (migration with no parent)"

    errors = []
    # validate graph structure
    for parent, names in list(migration_nodes.items()):
        if parent and parent not in migration_data:
            errors.append("Cannot find migration: {}".format(parent))
        if len(names) != 1:
            errors.append("Migration ({}) has multiple ({}) children".format(
                        parent if parent else "ROOT", [m for m in names]))

    if errors:
        raise RuntimeError("Errors in migration context: %s" % (', '.join(errors)))
    else:
        path = find_path(migration_nodes, None)
        migrations.extend([migration_data[m] for m in path])

    return (path, migration_data)


NAME_RE = re.compile(r'[^\w\d ]+')
def normalize_name(name):
    name = NAME_RE.sub('', name)
    return name.replace(' ', '_').lower()


def add_migration(directory, migrations_dir="migrations", id=None, description=None, rename=False):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"
    parser = ET.XMLParser(remove_blank_text=True)
    migrations_context = ET.parse(migrations_file, parser)
    validate_xml(migrations_context)

    normalized_location = os.path.join(migrations_dir, os.path.basename(directory))
    if not os.path.exists(normalized_location):
        raise RuntimeError("Cannot find directory at %s"  % normalized_location)

    if id is None:
        id = datetime.now().strftime("%Y%m%dT%H%M_")

        if description:
            id = id + normalize_name(description)
        else:
            id = id + normalize_name(os.path.basename(directory))

    E = ElementMaker(namespace="http://www.pixelmedia.com/xml/dwremigrate",
                     nsmap={None : "http://www.pixelmedia.com/xml/dwremigrate"})

    (path, migrations) = get_migrations(migrations_context)
    parent = None
    if path:
        parent = path[-1]

    migration = E.migration(id=id)

    if description:
        migration.append(E.description(description))

    location = os.path.basename(directory)
    if rename:
        location = id
        os.rename(normalized_location, os.path.join(migrations_dir, id))

    migration.append(E.location(location))

    if parent:
        migration.append(E.parent(parent))

    migrations_context.getroot().append(migration)

    validate_xml(migrations_context)
    # validate path
    migrations = get_migrations(migrations_context)

    print("Writing new migration (%s) with parent (%s)" % (id, parent))

    #print ET.tostring(migrations_context, pretty_print=True, encoding="utf-8", xml_declaration=True)
    xml_file_output = ET.tostring(migrations_context, pretty_print=True, encoding="utf-8", xml_declaration=True)
    with open(os.path.join(migrations_dir, "migrations.xml"), "wb") as f:
        f.write(xml_file_output)


def apply_migrations(env, migrations_dir, test=False):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)

    webdavsession = requests.session()
    webdavsession.verify = env["verify"]
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.cert = env["cert"]
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    login_business_manager(env, bmsession)

    (current_tool_version, current_migration, current_migration_path) = (
        get_current_versions(env, bmsession))

    (path, migrations) = get_migrations(migrations_context)

    migration_path = []
    skip_migrations = False
    if current_tool_version is None or int(TOOL_VERSION) > int(current_tool_version):
        migration_path.insert(0, None)
        migrations[None] = {"id" : "DWRE_MIGRATE_BOOTSTRAP", "description" : "DWRE Migrate tools bootstrap/upgrade" }
        if SKIP_METADATA_CHECK_ON_UPGRADE:
            skip_migrations = True

    if not skip_migrations:
        if current_migration is not None:
            assert current_migration in path, "Cannot find current migration version (%s) in migrations context; this requires manual intervention" % current_migration
            migration_path = path[path.index(current_migration)+1:]
            path_to_check = path[:path.index(current_migration)+1]
        else:
            migration_path = path
            path_to_check = []

        if current_migration_path:
            if path_to_check != current_migration_path:
                # TODO refactor this debug output
                recommended_migration = None
                for path_pair in zip(path, current_migration_path):
                    if path_pair[0] != path_pair[1]:
                        break
                    recommended_migration = path_pair[0]

                print(Fore.YELLOW + "WARNING migration path does not match expected value" + Fore.RESET)
                print(Fore.BLUE + "Current Path (on sandbox): " + Fore.RESET, end='')
                current_migration_path_output = []
                color = Fore.GREEN
                for p in current_migration_path:
                    if p == recommended_migration:
                        current_migration_path_output.append(Fore.BLUE + p + Fore.RESET)
                        color = Fore.YELLOW
                    else:
                        current_migration_path_output.append(color + p + Fore.RESET)
                print(",".join(current_migration_path_output))
                expected_path_output = []
                color = Fore.GREEN
                print(Fore.BLUE + "\nExpected Path (from code): " + Fore.RESET, end='')
                for p in path_to_check:
                    if p == recommended_migration:
                        expected_path_output.append(Fore.BLUE + p + Fore.RESET)
                        color = Fore.YELLOW
                    else:
                        expected_path_output.append(color + p + Fore.RESET)
                print(",".join(expected_path_output))

                print(Fore.YELLOW + "migration path does not match expected value; See output above and use 'dwre migrate set' command or manually fix" + Fore.RESET)
                print(Fore.YELLOW + "Recommend reverting to migration:" + Fore.RESET,
                        Fore.BLUE + ("%s" % recommended_migration) + Fore.RESET)
                return False
        else:
            current_migration_path = path_to_check

    if migration_path:
        print(Fore.YELLOW + "%s migrations required..." % len(migration_path) + Fore.RESET)
    else:
        print(Fore.GREEN + "No migrations required. Instance is up to date: %s" % current_migration + Fore.RESET)
        return

    for migration in migration_path:
        migration_data = migrations[migration]
        print("[%s] %s" % (migration_data["id"], migration_data["description"]))

    if test:
        print("Will not perform migrations, exiting...")
        return

    print("\nRunning migrations...")

    for m in migration_path:
        migration = migrations[m]

        start_time = time.time()

        zip_filename = "dwremigrate_%s" % migration["id"]
        if m is None:
            zip_file = get_bootstrap_zip()
            zip_filename = "DWREMigrateBootstrap_v{}".format(TOOL_VERSION)
        else:
            zip_file = directory_to_zip(os.path.join(migrations_dir, migration["location"]), zip_filename)

        # upload
        dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
            env["server"], zip_filename)
        response = webdavsession.put(dest_url, data=zip_file)
        response.raise_for_status()

        # activate
        response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch".format(env["server"]),
                                  data={"import" :"", "ImportFileName" : zip_filename + ".zip", "realmUse": "False"})
        response.raise_for_status()

        wait_for_import(env, bmsession, zip_filename)

        # update migration version
        current_migration_path.append(migration["id"])
        new_version_path = ",".join(current_migration_path)
        if m is not None:
            response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                      data={"NewVersion" : migration["id"], "NewVersionPath" : new_version_path})

        # delete file
        dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
                    env["server"], zip_filename)
        response = webdavsession.delete(dest_url)
        response.raise_for_status()

        end_time = time.time()
        print("Migrated %s in %.3f seconds" % (migration["id"], end_time - start_time))
    print(Fore.GREEN + "Successfully updated instance with current migrations" + Fore.RESET)
    if skip_migrations:
        print(Fore.YELLOW + "Migrations may have been skipped due to tool upgrade, rerun apply to check." + Fore.RESET)


def run_migration(env, migrations_dir, migration_name):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)

    webdavsession = requests.session()
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.verify = env["verify"]
    webdavsession.cert = env["cert"]
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    login_business_manager(env, bmsession)

    (path, migrations) = get_migrations(migrations_context)

    assert migration_name in migrations, "Cannot find migration"

    migration = migrations[migration_name]

    start_time = time.time()

    zip_filename = "dwremigrate_%s" % migration["id"]
    zip_file = directory_to_zip(os.path.join(migrations_dir, migration["location"]), zip_filename)

    # upload
    dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
        env["server"], zip_filename)
    response = webdavsession.put(dest_url, data=zip_file)
    response.raise_for_status()

    # activate
    response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/ViewSiteImpex-Dispatch".format(env["server"]),
                                data={"import" :"", "ImportFileName" : zip_filename + ".zip", "realmUse": "False"})
    response.raise_for_status()

    wait_for_import(env, bmsession, zip_filename)

    # delete file
    dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
                env["server"], zip_filename)
    response = webdavsession.delete(dest_url)
    response.raise_for_status()

    end_time = time.time()
    print("Migrated %s in %.3f seconds" % (migration["id"], end_time - start_time))


def reset_migrations(env, migrations_dir, test=False):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)

    webdavsession = requests.session()
    webdavsession.verify = env["verify"]
    webdavsession.cert = env["cert"]
    webdavsession.auth=(env["username"], env["password"],)
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    login_business_manager(env, bmsession)

    (current_tool_version, current_migration, current_migration_path) = (
        get_current_versions(env, bmsession))

    (path, migrations) = get_migrations(migrations_context)

    print("Will reset migrations to %s" % migrations[path[-1]]["id"])
    for i, p in enumerate(path):
        print("\t" + "%s:" % i, p)

    if not test:
        response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                  data={"NewVersion" : migrations[path[-1]]["id"], "NewVersionPath" : ",".join(path)})
        print("Updated migrations to code version")


def validate_migrations(migrations_dir):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    print(Fore.MAGENTA + "Validating migrations.xml" + Fore.RESET, end=' ')
    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)
    print(Fore.GREEN + "[OK]" + Fore.RESET)

    (path, migrations) = get_migrations(migrations_context)

    results = []
    for m in path:
        print(Fore.MAGENTA + "Validating migration: %s" % m + Fore.RESET)
        data = migrations[m]
        result = validate_directory(os.path.join(migrations_dir, data["location"]))
        results.append(result)
    return all(results)


def set_migration(env, migrations_dir, migration_name):
    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)

    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    (path, migrations) = get_migrations(migrations_context)

    login_business_manager(env, bmsession)

    assert migration_name in migrations, "Cannot find migration"
    
    # TODO slice path at migrations set on bm
    new_path = path[:path.index(migration_name)+1]

    response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
            data={"NewVersion" : migration_name, "NewVersionPath" : ",".join(new_path)})
    response.raise_for_status()
    print("Updated migrations to %s" % migration_name)
