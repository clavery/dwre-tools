from __future__ import unicode_literals

import re
import time
from threading import Timer, Thread
import os.path

from terminaltables import AsciiTable
from pygments import highlight
from pygments.lexers import JavascriptLexer
from pygments.formatters import TerminalFormatter
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory, FileHistory
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.shortcuts import create_prompt_application, create_eventloop, create_prompt_layout
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

import requests
from dwre_tools.env import get_default_environment, get_default_project
from dwre_tools.sync import collect_cartridges, sync_command


CARTRIDGES = {}
CLIENT_ID = "dwre-tools"

CURRENT_THREAD = None
THREADS = []
WATCH_VAR = None
WATCH_VAL = None

STYLE = style_from_dict({
    Token.Toolbar: '#ffffff bg:#666666',
    Token.Watch: '#ff0000 bg:#666666',
})


def get_bottom_toolbar_tokens(cli):
    tokens = []
    thread = "Running"
    if CURRENT_THREAD:
        thread_id = CURRENT_THREAD
        thread = [t for t in THREADS if t.get('id') == CURRENT_THREAD].pop()
        if thread['status'] != 'halted':
            return [(Token.Toolbar, '[RUNNING]')]
        frame = thread['call_stack'][0]
        loc = frame['location']
        filename = os.path.basename(loc['script_path'])
        location = "%s @ %s:%s" % (loc['function_name'], filename, loc['line_number'])
        tokens.append((Token.Toolbar, '[HALTED] Current Thread: %s   %s' % (thread_id, location)))

        if WATCH_VAR:
            value = WATCH_VAL if WATCH_VAL else ""
            tokens.append((Token.Watch, '   %s: %s' % (WATCH_VAR, value)))
        return tokens
    
    return [(Token.Toolbar, '[RUNNING]')]


def list_current_code():
    if not CURRENT_THREAD:
        return
    thread_id = CURRENT_THREAD
    thread = [t for t in THREADS if t.get('id') == CURRENT_THREAD].pop()
    if thread['status'] != 'halted':
        return
    frame = thread['call_stack'][0]
    loc = frame['location']
    filename = loc['script_path']
    line_num = loc['line_number']
    
    parts = filename[1:].split('/')
    (cartridge, rest) = parts[0], '/'.join(parts[1:])

    cartridge_path = CARTRIDGES.get(cartridge)
    
    if not cartridge_path:
        print "Cannot find file: " % filename
        return

    real_path = os.path.join(cartridge_path, rest)

    with open(real_path, 'r') as f:
        lines = f.readlines()
    lines = [l.decode('utf-8') for l in lines]

    # TODO: this is ugly
    starting_offset = 6 if line_num > 5 else line_num

    code = ''.join(lines)
    result = highlight(code, JavascriptLexer(), TerminalFormatter(bg="dark"))
    output = result

    code_lines = output.split('\n')

    for num, line in enumerate(code_lines):
        if num+1 < (line_num - 5) or num > (line_num + 5):
            continue
        if num+1 == line_num:
            print "---> %s:" % str(num + 1).zfill(3), line
        else:
            print "     %s:" % str(num + 1).zfill(3), line


def print_thread(session):
    if not CURRENT_THREAD:
        return
    for thread in THREADS:
        print "THREAD %s [%s]" % (thread['id'], thread['status'])
        for frame in thread['call_stack']:
            loc = frame['location']
            print "\t", "%s @ %s:%s" % (loc['function_name'], loc['script_path'], loc['line_number'])


def clean_value(val):
    if len(val) > 60:
        return val[0:60] + "..."
    return val

def print_members(session, base_url, member, refine=None):
    if not CURRENT_THREAD:
        return
    
    if member:
        resp = session.get(base_url + "/threads/%s/frames/0/members" % CURRENT_THREAD, params={"object_path" : member})
        resp.raise_for_status()
    else:
        resp = session.get(base_url + "/threads/%s/frames/0/members" % CURRENT_THREAD)
        resp.raise_for_status()

    members = resp.json().get('object_members')

    if members:
        table_data = [(m['name'], clean_value(m['value']), m['type']) for m in members 
                      if not m['name'] == 'arguments' and 
                      (not refine or (refine and re.search(refine, m['name'], re.IGNORECASE)))]
        table_data.insert(0, ['Name', 'Value', 'Type'])
        table = AsciiTable(table_data)

        print table.table


def thread_eval(session, base_url, expr):
    if not CURRENT_THREAD:
        return
    resp = session.get(base_url + "/threads/%s/frames/0/eval" % CURRENT_THREAD, params={"expr" : expr})
    resp.raise_for_status()
    print resp.json().get('result')


def debug_command(env, breakpoint_locations=None):
    global CARTRIDGES, WATCH_VAR, WATCH_VAL
    cartridges = collect_cartridges(".")
    CARTRIDGES = {name:path for path, name in cartridges}
    cartridge_paths = {path:name for path, name in cartridges}

    breakpoints = []
    if breakpoint_locations:
        for location in breakpoint_locations:
            (path, line) = location.split(":")
            abs_location = os.path.abspath(path)
            script_path = None

            for name, path in CARTRIDGES.iteritems():
                abs_cart_path = os.path.abspath(path)
                common_prefix = os.path.commonprefix([abs_cart_path, abs_location])
                if os.path.basename(common_prefix) == name:
                    # cartridge match
                    script_path = "/%s%s" % (name, abs_location[len(common_prefix):])
                    breakpoints.append({
                        "line_number" : int(line),
                        "script_path" : script_path
                    })
            if script_path is None:
                print "Cannot find cartridge code for " + location

    base_url = "https://{0}/s/-/dw/debugger/v1_0".format(env['server'])

    auth = env['username'], env['password']
    headers = {
        "x-dw-client-id" : CLIENT_ID
    }

    session = requests.session()
    session.auth = auth
    session.headers.update(headers)

    resp = session.delete(base_url + "/client")
    resp.raise_for_status()
    resp = session.post(base_url + "/client")
    resp.raise_for_status()

    resp = session.delete(base_url + "/breakpoints")
    if breakpoints:
        resp = session.post(base_url + "/breakpoints", json={
            "breakpoints" : breakpoints
        })
        resp.raise_for_status()

    manager = KeyBindingManager(enable_abort_and_exit_bindings=True)
    history = FileHistory(os.path.expanduser("~/.dwredebughist"))
    app = create_prompt_application(message="> ", get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                                    style=STYLE, history=history)
    cli = CommandLineInterface(application=app, eventloop=create_eventloop())

    t = None
    def keepalive():
        resp = session.post(base_url + "/threads/reset")
        t = Timer(15, keepalive)
        t.daemon = True
        t.start()
    keepalive()

    def check_for_threads():
        global CURRENT_THREAD, THREADS, WATCH_VAR, WATCH_VAL
        while True:
            resp = session.get(base_url + "/threads")
            threads = resp.json().get("script_threads")
            if threads:
                CURRENT_THREAD = threads[0].get("id")
                THREADS = threads
                resp = session.get(base_url + "/threads/%s/frames/0/members" % CURRENT_THREAD, params={"object_path" : WATCH_VAR})
                members = resp.json().get('object_members') 
                if members:
                    WATCH_VAL = members[0]["value"]
            else:
                CURRENT_THREAD = None
                WATCH_VAL = None
                THREADS = []
            cli.request_redraw()
            time.sleep(1)

    thread_check_thread = Thread(target=check_for_threads)
    thread_check_thread.daemon = True
    thread_check_thread.start()

    print "Connected to {} [version: {}], starting interactive session...".format(env["server"], env["codeVersion"])
    
    resp = session.get(base_url + "/breakpoints")
    server_bp = resp.json().get('breakpoints')
    if server_bp:
        for bp in server_bp:
            print "BREAKPOINT %s:%s" % (bp['script_path'], bp['line_number'])

    while True:
        try:
            result = cli.run()
            if not result.text.strip():
                continue
            cmd = result.text.split(' ')[0]
            rest = result.text.split(' ')[1:]
            if cmd in ['exit']:
                resp = session.delete(base_url + "/client")
                resp.raise_for_status()
                return
            elif cmd in ['print', 'p']:
                var = None
                refine = None
                if rest:
                    var = rest[0]
                if len(rest) > 1:
                    refine = rest[1]
                print_members(session, base_url, var, refine)
            elif cmd in ['stack', 's']:
                print_thread(session)
            elif cmd in ['watch']:
                if rest:
                    WATCH_VAR = rest[0]
                    WATCH_VAL = None
            elif cmd in ['continue', 'c']:
                if CURRENT_THREAD:
                    resp = session.post(base_url + "/threads/%s/resume" % CURRENT_THREAD)
            elif cmd in ['into', 'i']:
                if CURRENT_THREAD:
                    resp = session.post(base_url + "/threads/%s/into" % CURRENT_THREAD)
            elif cmd in ['out', 'o']:
                if CURRENT_THREAD:
                    resp = session.post(base_url + "/threads/%s/out" % CURRENT_THREAD)
            elif cmd in ['next', 'n']:
                if CURRENT_THREAD:
                    resp = session.post(base_url + "/threads/%s/over" % CURRENT_THREAD)
            elif cmd in ['list', 'l']:
                list_current_code()
            elif cmd in ['eval', 'e']:
                thread_eval(session, base_url, ' '.join(rest))
            else:
                thread_eval(session, base_url, result.text)
                
        except (EOFError, KeyboardInterrupt):
            resp = session.delete(base_url + "/client")
            resp.raise_for_status()
            return
        except (Exception):
            resp = session.delete(base_url + "/client")
            resp.raise_for_status()
            raise

