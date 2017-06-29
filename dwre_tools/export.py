from __future__ import print_function

from flask import Flask, request, render_template
import requests
import webbrowser
import yaml
import re
import tempfile
import uuid
import zipfile, io
import os
import shutil

from .bmtools import login_business_manager, get_list_data_units, get_export_zip


def export_units(env):
    pass

def export_command(env, directory):
    bmsession = requests.session()
    bmsession.verify = env["verify"]
    bmsession.cert = env["cert"]

    print("Getting data units from business manager...")
    login_business_manager(env, bmsession)
    data_units = get_list_data_units(env, bmsession)

    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app = Flask(__name__)

    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route("/")
    def index():
        return render_template('index.html', data_units=data_units)

    export_units = []
    cancelled = False
    @app.route("/config", methods=["POST"])
    def shutdown():
        if "cancel" in request.form:
            shutdown_server()
            cancelled = True
            return 'Canceled export...'
        else:
            for unit,value in request.form.items():
                if value == "on":
                    export_units.append(unit)
            shutdown_server()
            return 'Saving migration'

    webbrowser.open("http://localhost:5698")
    print("Launching web browser to http://localhost:5698")
    app.run(port=5698)

    if not cancelled:
        print("Exporting units:")
        [print("\t", u) for u in export_units]

        filename = "ToolsExport_" + str(uuid.uuid4()).replace("-", "")[:10]

        webdavsession = requests.session()
        webdavsession.verify = env["verify"]
        webdavsession.auth=(env["username"], env["password"],)
        webdavsession.cert = env["cert"]

        export_zip = get_export_zip(env, bmsession, webdavsession, export_units, filename)

        tempdir = tempfile.mkdtemp()
        export_zip.extractall(tempdir)

        shutil.move(os.path.join(tempdir, filename), directory)

        print("Saved export to", directory)
