import os.path
import re
import time
import json
from threading import Thread, Timer
from typing import Dict, List, Optional

import requests
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML, to_formatted_text
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.application import run_in_terminal
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JavascriptLexer
from terminaltables import AsciiTable

from dwre_tools.sync import collect_cartridges

from .vim import vim_call

CLIENT_ID = "dwre-tools"


class DebugContext():
    def __init__(self,
                 server: str,
                 username: str,
                 password: str,
                 breakpoints: List[Dict]):
        """Initialize a DWRE debugging session

        @param breakpoints: dictionary of breakpoints {line_number:.., script_path:...}
        """
        self._current_thread = None
        self._threads_state = None
        self._threads = []
        self.state_change_listeners = []
        # future
        self._watches = []
        self.base_url = f"https://{server}/s/-/dw/debugger/v2_0"

        auth = username, password
        headers = {
            "x-dw-client-id": CLIENT_ID
        }

        self.session = requests.session()
        self.session.auth = auth
        self.session.headers.update(headers)
        resp = self.session.delete(f"{self.base_url}/client")
        resp.raise_for_status()
        resp = self.session.post(f"{self.base_url}/client")
        resp.raise_for_status()

        resp = self.session.delete(f"{self.base_url}/breakpoints")
        if breakpoints:
            resp = self.session.post(f"{self.base_url}/breakpoints", json={
                "breakpoints": breakpoints
            })
            resp.raise_for_status()

        self.t = None
        def keepalive():
            self.session.post(f"{self.base_url}/threads/reset")
            self.t = Timer(15, keepalive)
            self.t.daemon = True
            self.t.start()
        keepalive()

        def check_for_threads():
            while True:
                resp = self.session.get(f"{self.base_url}/threads")
                threads = resp.json().get("script_threads")
                if threads and any([t.get('status') != 'running' for t in threads]):
                    self._threads = threads
                    threads_json = json.dumps(threads)
                    if threads_json != self._threads_state:
                        for l in self.state_change_listeners:
                            l(self)
                    self._threads_state = threads_json
                else:
                    self._threads = []
                    if self._threads_state is not None:
                        for l in self.state_change_listeners:
                            l(self)
                    self._threads_state = None
                time.sleep(0.250)

        self.thread_check_thread = Thread(target=check_for_threads)
        self.thread_check_thread.daemon = True
        self.thread_check_thread.start()

    @property
    def current_thread(self):
        if self._threads:
            thread = [t for t in self._threads if t.get('status') == 'halted'].pop()
        return thread

    @property
    def current_thread_id(self):
        if self.is_halted():
            return self.current_thread.get('id')

    @property
    def breakpoints(self):
        resp = self.session.get(f"{self.base_url}/breakpoints")
        resp.raise_for_status()
        server_bp = resp.json().get('breakpoints')
        return server_bp

    def add_state_change_listener(self, l):
        self.state_change_listeners.append(l)

    @property
    def threads(self):
        return self._threads

    def is_running(self):
        return (not self._threads or
                not any([t.get('status') != 'running' for t in self._threads]))

    def is_halted(self):
        return not self.is_running()

    def get_current_location(self, frame=0):
        """Returns tuple of script, line_number, function_name or None"""
        if self.is_halted():
            thread = self.current_thread
            frame = thread['call_stack'][frame]
            loc = frame['location']
            script = loc['script_path']
            return (script, loc['line_number'], loc['function_name'])

    def disconnect(self):
        resp = self.session.delete(f"{self.base_url}/client")
        resp.raise_for_status()

    def eval(self, expr, frame=0):
        if self.is_halted():
            resp = self.session.get(f"{self.base_url}/threads/{self.current_thread_id}/" +
                                    f"frames/{frame}/eval",
                                    params={"expr": expr})
            resp.raise_for_status()
            return resp.json().get('result')

    def continue_(self):
        if self.is_halted():
            resp = self.session.post(f"{self.base_url}/threads/{self.current_thread_id}/resume")
            resp.raise_for_status()

    def next(self):
        if self.is_halted():
            resp = self.session.post(f"{self.base_url}/threads/{self.current_thread_id}/over")
            resp.raise_for_status()

    def into(self):
        if self.is_halted():
            resp = self.session.post(f"{self.base_url}/threads/{self.current_thread_id}/into")
            resp.raise_for_status()

    def out(self):
        if self.is_halted():
            resp = self.session.post(f"{self.base_url}/threads/{self.current_thread_id}/out")
            resp.raise_for_status()

    def get_object_members(self, frame=0, object_path=None):
        if self.is_halted():
            if object_path:
                resp = self.session.get(f"{self.base_url}/threads/{self.current_thread_id}/" +
                                        f"frames/{frame}/members",
                                        params={"object_path": object_path})
            else:
                resp = self.session.get(f"{self.base_url}/threads/{self.current_thread_id}/" +
                                        f"frames/{frame}/members")

            resp.raise_for_status()

            members = resp.json().get('object_members')
            return members

    def get_variables(self, frame=0):
        if self.is_halted():
            resp = self.session.get(f"{self.base_url}/threads/{self.current_thread_id}/" +
                                    f"frames/{frame}/variables")
            resp.raise_for_status()
            members = resp.json().get('object_members')
            return members


COMPLETE_CACHE = {}
CURRENT_FRAME = 0

def get_bottom_toolbar(context):
    global CURRENT_FRAME
    if context.is_halted():
        (script, line, function) = context.get_current_location(CURRENT_FRAME)
        thread_id = context.current_thread.get('id')
        filename = os.path.basename(script)
        location = "[%s] %s @ %s:%s" % (CURRENT_FRAME, function, filename, line)
        return to_formatted_text(HTML('[HALTED] Current Thread: %s   %s' % (thread_id, location)))

    return to_formatted_text(HTML('[RUNNING]'))


def script_path_to_real(script, cartridges):
    parts = script[1:].split('/')
    (cartridge, rest) = parts[0], '/'.join(parts[1:])

    cartridge_path = cartridges.get(cartridge)
    if not cartridge_path:
        return
    return os.path.join(cartridge_path, rest)


def list_current_code(context, cartridges):
    global CURRENT_FRAME
    if not context.is_halted():
        return
    (filename, line_num, _) = context.get_current_location(CURRENT_FRAME)

    real_path = script_path_to_real(filename, cartridges)
    if not real_path or not os.path.exists(real_path):
        print(f"Cannot find file for current frame")
        return

    with open(real_path, 'rb') as f:
        lines = f.readlines()
    lines = [l.decode('utf-8') for l in lines]

    code = ''.join(lines)
    result = highlight(code, JavascriptLexer(), TerminalFormatter(bg="dark"))
    output = result

    code_lines = output.split('\n')

    for num, line in enumerate(code_lines):
        if num+1 < (line_num - 10) or num > (line_num + 10):
            continue
        if num+1 == line_num:
            print("---> %s:" % str(num + 1).zfill(3), line)
        else:
            print("     %s:" % str(num + 1).zfill(3), line)


def print_thread(context):
    global CURRENT_FRAME
    if not context.is_halted():
        return
    threads = context.threads
    for thread in threads:
        print("THREAD %s [%s]" % (thread['id'], thread['status']))
        for i, frame in enumerate(thread['call_stack']):
            loc = frame['location']
            if i == CURRENT_FRAME:
                print("-->", end='')
            print("\t", "[%s] %s @ %s:%s" %
                  (i, loc['function_name'], loc['script_path'], loc['line_number']))


def clean_value(val):
    if len(val) > 60:
        return val[0:60] + "..."
    return val


def print_members(context, member, refine=None):
    global CURRENT_FRAME
    if not context.is_halted():
        return

    members = context.get_object_members(frame=CURRENT_FRAME, object_path=member)
    if members:
        table_data = [(m['name'], clean_value(m['value']), m['type']) for m in members 
                      if not m['name'] == 'arguments' and 
                      (not refine or (refine and re.search(refine, m['name'], re.IGNORECASE)))]
        table_data.insert(0, ['Name', 'Value', 'Type'])
        table = AsciiTable(table_data)
        print(table.table)


def print_variables(context, refine=None):
    global CURRENT_FRAME
    if not context.is_halted():
        return

    members = context.get_variables(frame=CURRENT_FRAME)
    if members:
        table_data = [(m['name'], clean_value(m['value']), m['type']) for m in members 
                      if not m['name'] == 'arguments' and 
                      (not refine or (refine and re.search(refine, m['name'], re.IGNORECASE)))]
        table_data.insert(0, ['Name', 'Value', 'Type'])
        table = AsciiTable(table_data)
        print(table.table)


class MemberCompleter(Completer):
    def __init__(self, context):
        self.context = context

    def get_completions(self, document, complete_event):
        global COMPLETE_CACHE, CURRENT_FRAME
        if not self.context.is_halted():
            return

        doc = document.text.replace("p ", "").replace("print ", "")

        member = ".".join(doc.split('.')[0:-1])
        if member in COMPLETE_CACHE:
            members = COMPLETE_CACHE.get(member)
        else:
            members = self.context.get_object_members(frame=CURRENT_FRAME, object_path=member)
            COMPLETE_CACHE[member] = members

        tomatch = doc.split('.')[-1]
        if members:
            matched_members = [m for m in members if m["name"].startswith(tomatch)]
            for m in matched_members:
                yield Completion(m["name"], start_position=-len(tomatch))


def debug_command(env,
                  breakpoint_locations: Optional[Dict[str, str]] = None,
                  vim: bool = False,
                  verbose: bool = False):
    global CURRENT_FRAME
    cartridges = collect_cartridges(".")
    cartridges = {name: path for path, name in cartridges}

    breakpoints = []
    if breakpoint_locations:
        for location in breakpoint_locations:
            if not location:
                continue
            (path, line) = location.split(":")
            abs_location = os.path.abspath(path)
            script_path = None

            for name, path in cartridges.items():
                abs_cart_path = os.path.abspath(path)
                common_prefix = os.path.commonprefix([abs_cart_path, abs_location])
                if os.path.basename(common_prefix) == name:
                    # cartridge match
                    script_path = "/%s%s" % (name, abs_location[len(common_prefix):])
                    breakpoints.append({
                        "line_number": int(line),
                        "script_path": script_path
                    })
            if script_path is None:
                print("Cannot find cartridge code for " + location)

    debug_context = DebugContext(env['server'], env['username'], env['password'], breakpoints)

    history = FileHistory(os.path.expanduser("~/.dwredebughist"))
    completer = MemberCompleter(debug_context)
    cli = PromptSession(message="> ", bottom_toolbar=lambda: get_bottom_toolbar(debug_context),
                        history=history, completer=completer, complete_in_thread=True,
                        complete_while_typing=False)

    if vim:
        def update_vim(context):
            global CURRENT_FRAME
            if context.is_halted():
                (script, line, _) = debug_context.get_current_location(CURRENT_FRAME)
                filename = script_path_to_real(script, cartridges)
                run_in_terminal(lambda:
                                vim_call('Tapi_Dwre_Update_Location', filename, line))
            else:
                run_in_terminal(lambda: vim_call('Tapi_Dwre_Update_Location', None, None))
        debug_context.add_state_change_listener(update_vim)

    debug_context.add_state_change_listener(lambda x: cli.app.invalidate())

    CURRENT_FRAME = 0

    def update_frame(num):
        global CURRENT_FRAME
        CURRENT_FRAME = num
    debug_context.add_state_change_listener(lambda x: update_frame(0))

    print(f'Connected to {env["server"]} [version: {env["codeVersion"]}]')

    if vim:
        print("VIM mode enabled")

    server_bp = debug_context.breakpoints
    if server_bp:
        for bp in server_bp:
            print("BREAKPOINT %s:%s" % (bp['script_path'], bp['line_number']))

    while True:
        try:
            result = cli.prompt()
            if not result.strip():
                continue
            cmd = result.split(' ')[0]
            rest = result.split(' ')[1:]
            if cmd in ['exit']:
                return
            elif cmd in ['variables', 'v']:
                refine = None
                if rest:
                    refine = rest[0]
                print_variables(debug_context, refine)
            elif cmd in ['print', 'p']:
                var = None
                refine = None
                if rest:
                    var = rest[0]
                if len(rest) > 1:
                    refine = rest[1]
                print_members(debug_context, var, refine)
            elif cmd in ['stack', 's']:
                print_thread(debug_context)
            elif cmd in ['watch']:
                print("Command Not Available")
            elif cmd in ['continue', 'c']:
                debug_context.continue_()
            elif cmd in ['into', 'i']:
                debug_context.into()
            elif cmd in ['out', 'o']:
                debug_context.out()
            elif cmd in ['next', 'n']:
                debug_context.next()
            elif cmd in ['list', 'l']:
                list_current_code(debug_context, cartridges)
            elif cmd in ['help']:
                print(HELP.table)
            elif cmd in ['frame', 'f']:
                if rest:
                    try:
                        frame = int(rest[0])
                    except ValueError:
                        continue
                    CURRENT_FRAME = frame
            elif cmd in ['eval', 'e']:
                print(debug_context.eval(' '.join(rest), frame=CURRENT_FRAME))
            else:
                print(debug_context.eval(result, frame=CURRENT_FRAME))
        except (EOFError, KeyboardInterrupt):
            debug_context.disconnect()
            return
        except Exception:
            debug_context.disconnect()
            raise


COMMANDS = [
    ("continue,c", "Continue Execution To end or Next Breakpoint"),
    ("next,n", "Continue to next statement (jumping over)"),
    ("into,i", "jump into the next function"),
    ("out,o", "jump out of the current function/frame"),
    ("print,p [var] [filter]", "print the current frame members or var members"),
    ("variables,v", "print all variables in scope"),
    ("eval,e expr", "evaluate an expression"),
    ("stack,s", "print current thread stack"),
    ("frame,f num", "set the current stack frame to num"),
]
COMMANDS.insert(0, ['CMD', 'Description'])
HELP = AsciiTable(COMMANDS)
