import re
import pytest
import responses
import json

from dwre_tools.debugger import DebugContext

class MockScriptAPI():
    def __init__(self):
        self.breakpoints = []
        self.threads = []

    def breakpoints_resource(self, request):
        if request.method == 'POST':
            payload = json.loads(request.body)
            self.breakpoints = payload.get('breakpoints')
            if not self.breakpoints:
                return (500, {}, "")
        resp_body = {'breakpoints': self.breakpoints}
        return (200, {}, json.dumps(resp_body))

    def threads_resource(self, request):
        resp_body = {'script_threads': self.threads}
        return (200, {}, json.dumps(resp_body))


@pytest.fixture
def mock_script_debugger():
    script_api = MockScriptAPI()

    responses.add(responses.DELETE, re.compile('.*/s/-/dw/debugger/v2_0/client'),
                  json={}, status=204)
    responses.add(responses.POST, re.compile('.*/s/-/dw/debugger/v2_0/client'),
                  json={}, status=204)
    responses.add(responses.DELETE, re.compile('.*/s/-/dw/debugger/v2_0/breakpoints'),
                  json={}, status=204)
    responses.add_callback(responses.POST, re.compile('.*/s/-/dw/debugger/v2_0/breakpoints'),
                           callback=script_api.breakpoints_resource,
                           content_type="application/json")
    responses.add(responses.POST, re.compile('.*/s/-/dw/debugger/v2_0/threads/reset'),
                  json={}, status=204)
    responses.add_callback(responses.GET, re.compile('.*/s/-/dw/debugger/v2_0/threads'),
                           callback=script_api.threads_resource,
                           content_type="application/json")
    return True


@pytest.fixture
def breakpoints():
    return [
        {
            "line_number": 26,
            "script_path": 'app_debugtest/cartridge/controllers/DebuggerTesting.js'
        }
    ]


@pytest.fixture
@responses.activate
def debug_context(mock_script_debugger, breakpoints):
    return DebugContext('test.com', 'testing', '1234', breakpoints)


@responses.activate
def test_debug_context_creation(mock_script_debugger, debug_context):
    assert(debug_context.is_running())
    assert(not debug_context.is_halted())
