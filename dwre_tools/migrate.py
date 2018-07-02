from __future__ import print_function

import tempfile
import functools
import time
import zipfile
import os
import io
import re
import sys
import time
from datetime import datetime
import uuid

try:
    import _thread as thread
except ImportError:
    import thread

import pyquery
import requests
from lxml import etree as ET
from lxml.builder import ElementMaker
from collections import defaultdict

from colorama import Fore, Back, Style

from .validations import validate_xml, validate_file, validate_directory
from .migratemeta import TOOL_VERSION, BOOTSTRAP_META, PREFERENCES, VERSION, SKIP_METADATA_CHECK_ON_UPGRADE, WHITELIST, RERUN_MIGRATIONS_ON_UPGRADE, CARTRIDGE_VERSION, MIGRATION_FILE
from .bmtools import get_current_versions, login_business_manager, wait_for_import
from .utils import directory_to_zip
from .index import reindex
from .exc import NotInstalledException
from .export import get_export_zip
from .cartridge import update_bm_cartridge_server


X = "{http://www.pixelmedia.com/xml/dwremigrate}"

NSMAP_PREFS = {"P" : 'http://www.demandware.com/xml/impex/preferences/2007-03-31'}
NSMAP_ACCESS_ROLE = {"A" : 'http://www.demandware.com/xml/impex/accessrole/2007-09-05'}

def get_install_zip(env, bmsession, webdavsession):
    """Attempts to add the BM extension and access roles to prep for boostrap"""
    filename = "ToolsExport_" + str(uuid.uuid4()).replace("-", "")[:10]
    zip_file = get_export_zip(env, bmsession, webdavsession, 
                              export_units=["AccessRoleExport", "GlobalPreferencesExport"],
                              filename=filename)

    dest_file = "DWREMigrateInstall_" + str(uuid.uuid4()).replace("-", "")[:10]

    install_package_file = io.BytesIO()
    install_package_zip = zipfile.ZipFile(install_package_file, "w")

    preferences = ET.fromstring(zip_file.read("%s/preferences.xml" % filename))
    bm_cartridge_path = preferences.xpath(".//P:standard-preferences/P:all-instances/P:preference[@preference-id='CustomCartridges']", namespaces=NSMAP_PREFS)
    if not bm_cartridge_path:
        raise Exception("Cannot automatically install DWRE tools; must be done manually")
    
    if not bm_cartridge_path[0].text or "bm_dwremigrate" not in bm_cartridge_path[0].text:
        print("Updating BM cartridge path preferences...")
        # create preferences.xml with updated cartridge path
        EP = ElementMaker(namespace="http://www.demandware.com/xml/impex/preferences/2007-03-31",
                          nsmap={None : "http://www.demandware.com/xml/impex/preferences/2007-03-31"})
        old_bm_path = bm_cartridge_path[0].text if bm_cartridge_path[0].text else ""
        new_bm_path = 'bm_dwremigrate:' + old_bm_path
        new_preferences = EP('preferences',
                             EP('standard-preferences',
                                EP('all-instances',
                                   EP('preference', new_bm_path, **{"preference-id" : "CustomCartridges"})
                                )))
        new_prefs_xml = ET.tostring(new_preferences, pretty_print=True, encoding="utf-8", xml_declaration=True)
        install_package_zip.writestr("{}/preferences.xml".format(dest_file), new_prefs_xml)

    access_roles = ET.fromstring(zip_file.read("%s/access-roles.xml" % filename))
    admin_access_role = access_roles.xpath(".//A:access-role[@role-id='Administrator']", namespaces=NSMAP_ACCESS_ROLE)

    if not admin_access_role:
        raise Exception("Cannot find 'Administrator' access role; DWRE tools must be installed manually")
    admin_access_role = admin_access_role[0]
    migration_access = admin_access_role.xpath(".//A:access-controls/A:access-control[@resource-path='BUSINESSMGR/CustomMenu/Sites/-/dwremigrate_menu']", namespaces=NSMAP_ACCESS_ROLE)
    
    if not migration_access or migration_access[0].attrib['permission'] != 'ACCESS':
        print("Adding bm_dwremigrate access role...")
        # need to add access to BM cart
        if migration_access:
            migration_access[0].attrib['permission'] = 'ACCESS'
        else:
            EA = ElementMaker(namespace="http://www.demandware.com/xml/impex/accessrole/2007-09-05",
                              nsmap={None : "http://www.demandware.com/xml/impex/accessrole/2007-09-05"})

            access_controls = admin_access_role.xpath(".//A:access-controls", namespaces=NSMAP_ACCESS_ROLE)[0]
            access_controls.insert(0, EA('access-control', **{"resource-path" : "BUSINESSMGR/CustomMenu/Sites/-/dwremigrate_menu", "permission" : "ACCESS"}))
        new_access_xml = ET.tostring(access_roles, pretty_print=True, encoding="utf-8", xml_declaration=True)
        install_package_zip.writestr("{}/access-roles.xml".format(dest_file), new_access_xml)

    install_package_zip.writestr("{}/version.txt".format(dest_file), """###########################################
# Generated file, do not edit.
# Copyright (c) 2017 by Demandware, Inc.
###########################################
17.8.3""")
    install_package_zip.close()
    return (install_package_file, dest_file)


def get_bootstrap_zip():
    dest_file = "DWREMigrateBootstrap_v{}".format(TOOL_VERSION)

    bootstrap_package_file = io.BytesIO()
    bootstrap_package_zip = zipfile.ZipFile(bootstrap_package_file, "w")

    bootstrap_package_zip.writestr("{}/version.txt".format(dest_file), VERSION)
    bootstrap_package_zip.writestr("{}/preferences.xml".format(dest_file), PREFERENCES)
    #bootstrap_package_zip.writestr("{}/csrf-whitelists.xml".format(dest_file), WHITELIST)
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


def get_migrations(migrations_context, hotfix=False):
    migrations = []
    migration_nodes = defaultdict(list)
    migration_data = {}
    path = []
    for migration in migrations_context.getroot():
        id = migration.attrib["id"]
        location = migration.find(X + "location").text
        description_el = migration.find(X + "description")
        parent_el = migration.find(X + "parent")
        reindex = migration.find(X + "reindex")

        description = ""
        if description_el is not None:
            description = description_el.text

        assert id not in migration_data, "Migration %s already exists" % id
        migration_data[id] = {"id": id, "location" : location, "description": description}

        if reindex is not None and reindex.text.lower() == "true":
            migration_data[id]["reindex"] = True
        else:
            migration_data[id]["reindex"] = False

        if parent_el is not None:
            migration_nodes[parent_el.text].append(id)
        else:
            migration_nodes[None].append(id)
        path.append(id)

    if len(list(migration_data.keys())) == 0:
        return ([], {})

    # validate root exists
    assert migration_nodes[None], "Cannot find root migration (migration with no parent)"

    errors = []
    # validate graph structure
    if not hotfix:
        for parent, names in list(migration_nodes.items()):
            if parent and parent not in migration_data:
                errors.append("Cannot find migration: {}".format(parent))
            if len(names) != 1:
                errors.append("Migration ({}) has multiple ({}) children".format(
                            parent if parent else "ROOT", [m for m in names]))

    if errors:
        raise RuntimeError("Errors in migration context: %s" % (', '.join(errors)))
    else:
        if not hotfix:
            path = find_path(migration_nodes, None)
        migrations.extend([migration_data[m] for m in path])

    return (path, migration_data)


NAME_RE = re.compile(r'[^\w\d ]+')
def normalize_name(name):
    name = NAME_RE.sub('', name)
    return name.replace(' ', '_').lower()


def add_migration(directory, migrations_dir="migrations", id=None, description=None, rename=False, hotfix=False):
    if hotfix:
        migrations_file = os.path.join(migrations_dir, "hotfixes.xml")
        if not os.path.exists(migrations_file):
            with open(migrations_file, 'w') as f:
                f.write(MIGRATION_FILE)
    else:
        migrations_file = os.path.join(migrations_dir, "migrations.xml")
        if not os.path.exists(migrations_file):
            with open(migrations_file, 'w') as f:
                f.write(MIGRATION_FILE)
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

    (path, migrations) = get_migrations(migrations_context, hotfix=hotfix)
    parent = None
    if path and not hotfix:
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
    get_migrations(migrations_context, hotfix=hotfix)

    print("Writing new migration (%s) with parent (%s)" % (id, parent))

    xml_file_output = ET.tostring(migrations_context, pretty_print=True,
                                  encoding="utf-8", xml_declaration=True)
    with open(migrations_file, "wb") as f:
        f.write(xml_file_output)


def apply_migrations(env, migrations_dir, test=False, code_deployed=False):
    if os.path.isfile(migrations_dir):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(migrations_dir, 'r') as stored_zip:
            stored_zip.extractall(path=tempdir.name)
        migrations_dir = os.path.join(tempdir.name, "migrations")

    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    hotfixes_file = os.path.join(migrations_dir, "hotfixes.xml")
    hotfix_path = []
    hotfixes = []
    if os.path.exists(hotfixes_file):
        hotfixes_context = ET.parse(hotfixes_file)
        validate_xml(hotfixes_context)
        (hotfix_path, hotfixes) = get_migrations(hotfixes_context, hotfix=True)

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

    not_installed = False
    try:
        (current_tool_version, current_migration, current_migration_path,
         current_cartridge_version, current_hotfixes) = (
            get_current_versions(env, bmsession))
    except NotInstalledException as e:
        current_cartridge_version = None
        current_tool_version = None
        not_installed = True

    (path, migrations) = get_migrations(migrations_context)

    migration_path = []
    skip_migrations = False
    upgrade_required = False
    if (not_installed or current_cartridge_version is None 
            or int(current_cartridge_version) < int(CARTRIDGE_VERSION)):
        migration_path.append("CARTRIDGE")
        migrations["CARTRIDGE"] = {"id" : "DWRE_MIGRATE_CARTRIDGE", "description" : "Install/upgrade cartridge bm_dwremigrate", "reindex" : False}
        skip_migrations = True
        current_migration_path = []
        upgrade_required = True
        hotfix_path = []

    if current_tool_version is None or int(TOOL_VERSION) > int(current_tool_version):
        upgrade_required = True
        if not_installed:
            migration_path.append("INSTALL")
            migrations["INSTALL"] = {"id" : "DWRE_MIGRATE_INSTALL", "description" : "Install DWRE Migrate BM Extension", "reindex" : False}
            skip_migrations = True
            current_migration_path = []
            upgrade_required = True

        migration_path.append("BOOTSTRAP")
        migrations["BOOTSTRAP"] = {"id" : "DWRE_MIGRATE_BOOTSTRAP", "description" : "DWRE Migrate tools bootstrap/upgrade", "reindex" : False}
        if SKIP_METADATA_CHECK_ON_UPGRADE:
            skip_migrations = True
            current_migration_path = []
            hotfix_path = []

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
                print(Fore.CYAN + "Current Path (on sandbox): " + Fore.RESET, end='')
                current_migration_path_output = []
                color = Fore.GREEN
                for p in current_migration_path:
                    if p == recommended_migration:
                        current_migration_path_output.append(Fore.CYAN + p + Fore.RESET)
                        color = Fore.YELLOW
                    else:
                        current_migration_path_output.append(color + p + Fore.RESET)
                print(",".join(current_migration_path_output))
                expected_path_output = []
                color = Fore.GREEN
                print(Fore.CYAN + "\nExpected Path (from code): " + Fore.RESET, end='')
                for p in path_to_check:
                    if p == recommended_migration:
                        expected_path_output.append(Fore.CYAN + p + Fore.RESET)
                        color = Fore.YELLOW
                    else:
                        expected_path_output.append(color + p + Fore.RESET)
                print(",".join(expected_path_output))

                print(Fore.YELLOW + "migration path does not match expected value; See output above and use 'dwre migrate set' command or manually fix" + Fore.RESET)
                print(Fore.YELLOW + "Recommend reverting to migration:" + Fore.RESET,
                        Fore.CYAN + ("%s" % recommended_migration) + Fore.RESET)
                return False
        else:
            current_migration_path = path_to_check

        if current_hotfixes and hotfixes:
            print(hotfixes)
            hotfix_path = [h for h in hotfixes if h not in current_hotfixes]

    if migration_path or hotfix_path:
        print(Fore.YELLOW + "%s migrations required..." % len(migration_path) + Fore.RESET)
        if hotfix_path:
            print(Fore.YELLOW + "%s hotfixes required..." % len(hotfix_path) + Fore.RESET)
    else:
        if current_migration is None:
            current_migration = "No Migrations in Context"
        print(Fore.GREEN + "No migrations required. Instance is up to date: %s" % current_migration + Fore.RESET)
        return

    reindex_requested = False
    for migration in migration_path:
        migration_data = migrations[migration]

        print("[%s] %s" % (migration_data["id"], migration_data["description"]), end="")

        if migration_data["reindex"]:
            reindex_requested = True
            print(Fore.CYAN + " (Reindex Requested)" + Fore.RESET)
        else:
            print("")

    for migration in hotfix_path:
        migration_data = hotfixes[migration]

        print("[%s] %s " % (migration_data["id"], migration_data["description"]), end="")
        print(Fore.CYAN + "(hotfix", end="")
        if migration_data["reindex"]:
            reindex_requested = True
            print(",Reindex Requested)")
        else:
            print(")", Fore.RESET)

    if test:
        print("Will not perform migrations, exiting...")
        return

    print("\nRunning migrations...")


    for m in migration_path:
        migration = migrations[m]

        start_time = time.time()

        zip_filename = "dwremigrate_%s" % migration["id"]
        if m is "CARTRIDGE":
            if code_deployed:
                print(Fore.RED + "Error: cartridge does not appear to have upgraded; check code version", Fore.RESET)
                sys.exit(2)
            print("[DWRE_MIGRATE_CARTRIDGE] Install/upgrade cartridge bm_dwremigrate ")
            print(Fore.YELLOW + "Recommend running upgrade-bm-cartridge to avoid this in the future" + Fore.RESET)
            update_bm_cartridge_server(env, webdavsession)
            print("Waiting for code deployment...")
            time.sleep(10)
            code_deployed = True
            continue
        elif m is "BOOTSTRAP":
            zip_file = get_bootstrap_zip()
            zip_filename = "DWREMigrateBootstrap_v{}".format(TOOL_VERSION)
        elif m is "INSTALL":
            (zip_file, zip_filename) = get_install_zip(env, bmsession, webdavsession)
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
        if m not in ['CARTRIDGE', 'INSTALL', 'BOOTSTRAP']:
            response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                      data={"NewVersion" : migration["id"], "NewVersionPath" : new_version_path})

        # delete file
        dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
                    env["server"], zip_filename)
        response = webdavsession.delete(dest_url)
        response.raise_for_status()

        end_time = time.time()
        print("Migrated %s in %.3f seconds" % (migration["id"], end_time - start_time), end="")
        if migration["reindex"]:
            print(Fore.CYAN + " (Reindex Requested)" + Fore.RESET)
        else:
            print("")

    for m in hotfix_path:
        migration = hotfixes[m]

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

        # update migration version
        current_hotfixes.append(migration["id"])
        new_version_path = ",".join(current_hotfixes)
        response = bmsession.post("https://{}/on/demandware.store/Sites-Site/default/DWREMigrate-UpdateVersion".format(env["server"]),
                                  data={"dwreMigrateHotfixes" : new_version_path})

        # delete file
        dest_url = "https://{0}/on/demandware.servlet/webdav/Sites/Impex/src/instance/{1}.zip".format(
                    env["server"], zip_filename)
        response = webdavsession.delete(dest_url)
        response.raise_for_status()

        end_time = time.time()
        print("Migrated %s in %.3f seconds" % (migration["id"], end_time - start_time), end="")
        if migration["reindex"]:
            print(Fore.CYAN + " (Reindex Requested)" + Fore.RESET)
        else:
            print("")


    if skip_migrations and not RERUN_MIGRATIONS_ON_UPGRADE:
        print(Fore.YELLOW + "Migrations may have been skipped due to tool upgrade, rerun apply to check." + Fore.RESET)
    elif upgrade_required and RERUN_MIGRATIONS_ON_UPGRADE:
        print(Fore.YELLOW + "Upgrade complete...rerunning migrations" + Fore.RESET)
        return apply_migrations(env, migrations_dir, test, code_deployed)
    else:
        print(Fore.GREEN + "Successfully updated instance with current migrations" + Fore.RESET)

    if reindex_requested:
        print(Fore.CYAN + "One or more migrations request a search reindex" + Fore.RESET)
        try:
            reindex(env)
            print(Fore.GREEN + "Initiated reindex on {0}".format(env['server']) + Fore.RESET)
        except requests.exceptions.HTTPError as e:
            print(Fore.RED + "Error reindexing (try updated your bm_dwremigrate cartridge): {}".format(e.message) + Fore.RESET)

    if tempdir:
        tempdir.cleanup()


def run_all(env, migrations_dir, test=False):
    if os.path.isfile(migrations_dir):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(migrations_dir, 'r') as stored_zip:
            stored_zip.extractall(path=tempdir.name)
        migrations_dir = os.path.join(tempdir.name, "migrations")

    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"
    parser = ET.XMLParser(remove_blank_text=True)
    migrations_context = ET.parse(migrations_file, parser)
    validate_xml(migrations_context)
    (path, migrations) = get_migrations(migrations_context)

    hotfixes_file = os.path.join(migrations_dir, "hotfixes.xml")
    hotfix_path = []
    if os.path.exists(hotfixes_file):
        hotfixes_context = ET.parse(hotfixes_file)
        validate_xml(hotfixes_context)
        (hotfix_path, hotfixes) = get_migrations(hotfixes_context, hotfix=True)

    webdavsession = requests.session()
    webdavsession.auth=(env["username"], env["password"],)
    webdavsession.verify = env["verify"]
    webdavsession.cert = env["cert"]
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    login_business_manager(env, bmsession)

    not_installed = False
    try:
        (current_tool_version, current_migration, current_migration_path,
         current_cartridge_version, current_hotfixes) = (
            get_current_versions(env, bmsession))
    except NotInstalledException as e:
        raise RuntimeError("migrations not installed; use apply subcommand to bootstrap")

    required_migrations = list(set(path).difference(set(current_migration_path)))
    required_migrations = sorted(required_migrations, key=functools.cmp_to_key(lambda x, y: path.index(x) - path.index(y)))

    required_hotfixes = [h for h in hotfix_path if h not in current_hotfixes]

    if required_migrations:
        print(Fore.YELLOW + "%s migrations to run..." % len(required_migrations) + Fore.RESET)
    if required_hotfixes:
        print(Fore.YELLOW + "%s hotfixes required..." % len(required_hotfixes) + Fore.RESET)

    for migration in required_migrations:
        migration_data = migrations[migration]

        print("[%s] %s" % (migration_data["id"], migration_data["description"]))

    for migration in required_hotfixes:
        migration_data = hotfixes[migration]

        print("[%s] %s" % (migration_data["id"], migration_data["description"]))

    if test:
        print("Will not perform migrations, exiting...")
        return

    for migration in required_migrations:
        migration_data = migrations[migration]
        run_migration(env, os.path.join(migrations_dir, migration_data["location"]), migration)
    for migration in required_hotfixes:
        migration_data = hotfixes[migration]
        run_migration(env, os.path.join(migrations_dir, migration_data["location"]), migration)

    if tempdir:
        tempdir.cleanup()


def run_migration(env, directory, name=None):
    webdavsession = requests.session()
    webdavsession.auth = (env["username"], env["password"],)
    webdavsession.verify = env["verify"]
    webdavsession.cert = env["cert"]
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    login_business_manager(env, bmsession)

    start_time = time.time()

    if not os.path.exists(directory):
        print(Fore.RED + "Can't find directory: {}".format(directory) + Fore.RESET)
        return False

    if name is not None:
        zip_filename = name
    else:
        zip_filename = "dwremigrate_%s" % str(uuid.uuid4())
    zip_file = directory_to_zip(os.path.join(directory), zip_filename)

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

    response = webdavsession.delete(dest_url)
    response.raise_for_status()

    end_time = time.time()
    print("Imported %s in %.3f seconds" % (directory, end_time - start_time))


def reset_migrations(env, migrations_dir, test=False):
    if os.path.isfile(migrations_dir):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(migrations_dir, 'r') as stored_zip:
            stored_zip.extractall(path=tempdir.name)
        migrations_dir = os.path.join(tempdir.name, "migrations")

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

    (current_tool_version, current_migration, current_migration_path,
     current_cartridge_version, hotfixes) = (
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
    if os.path.isfile(migrations_dir):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(migrations_dir, 'r') as stored_zip:
            stored_zip.extractall(path=tempdir.name)
        migrations_dir = os.path.join(tempdir.name, "migrations")

    migrations_file = os.path.join(migrations_dir, "migrations.xml")
    assert os.path.exists(migrations_file), "Cannot find migrations.xml"

    hotfixes_file = os.path.join(migrations_dir, "hotfixes.xml")

    print(Fore.MAGENTA + "Validating migrations.xml" + Fore.RESET, end=' ')
    migrations_context = ET.parse(migrations_file)
    validate_xml(migrations_context)
    print(Fore.GREEN + "[OK]" + Fore.RESET)
    hotfix_path = []
    if os.path.exists(hotfixes_file):
        print(Fore.MAGENTA + "Validating hotfixes.xml" + Fore.RESET, end=' ')
        hotfixes_context = ET.parse(hotfixes_file)
        validate_xml(hotfixes_context)
        print(Fore.GREEN + "[OK]" + Fore.RESET)
        (hotfix_path, hotfixes) = get_migrations(hotfixes_context, hotfix=True)

    (path, migrations) = get_migrations(migrations_context)

    results = []
    for m in path:
        print(Fore.MAGENTA + "Validating migration: %s" % m + Fore.RESET)
        data = migrations[m]
        result = validate_directory(os.path.join(migrations_dir, data["location"]))
        results.append(result)
    for m in hotfix_path:
        print(Fore.MAGENTA + "Validating hotfix: %s" % m + Fore.RESET)
        data = hotfixes[m]
        result = validate_directory(os.path.join(migrations_dir, data["location"]))
        results.append(result)
    return all(results)


def set_migration(env, migrations_dir, migration_name):
    if os.path.isfile(migrations_dir):
        tempdir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(migrations_dir, 'r') as stored_zip:
            stored_zip.extractall(path=tempdir.name)
        migrations_dir = os.path.join(tempdir.name, "migrations")

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
